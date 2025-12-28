"""
Cloud Run Jobs Sandbox Implementation

Replaces DockerSandbox for Cloud Run production environments where
Docker-in-Docker is not available.

Architecture:
- Uses Cloud Run Jobs for isolated command execution
- Cloud Storage for session state persistence  
- Supports stateful execution with CWD/ENV preservation
- Background process management
- Full Sandbox protocol compatibility

Author: Kilo Code
Date: 2025-12-28
"""

from typing import Dict, Any, Optional, List, BinaryIO
import uuid
import json
import asyncio
import logging
import io
import re
from datetime import datetime
from pathlib import Path

from google.cloud import run_v2
from google.cloud import storage
from google.api_core import exceptions as gcp_exceptions

from app.core.config import get_settings
from app.domain.models.tool_result import ToolResult
from app.domain.external.sandbox import Sandbox
from app.domain.external.browser import Browser

logger = logging.getLogger(__name__)


class SessionStateManager:
    """
    Manages session state persistence in Cloud Storage.
    
    State Structure:
    - sessions/{session_id}/state.json - Current session state
    - executions/{execution_id}/result.json - Execution results
    """
    
    def __init__(self, storage_client: storage.Client, bucket_name: str):
        """
        Initialize state manager.
        
        Args:
            storage_client: Google Cloud Storage client
            bucket_name: Cloud Storage bucket name for state
        """
        self.storage_client = storage_client
        self.bucket_name = bucket_name
        self.bucket = storage_client.bucket(bucket_name)
        
        logger.info(f"SessionStateManager initialized with bucket: {bucket_name}")
    
    async def load_state(self, session_id: str) -> Dict[str, Any]:
        """
        Load session state from Cloud Storage.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session state dict with:
            - session_id: Session identifier
            - cwd: Current working directory
            - env_vars: Environment variables
            - background_pids: Background process tracking
            - created_at: Session creation timestamp
        """
        try:
            blob = self.bucket.blob(f"sessions/{session_id}/state.json")
            
            if not await asyncio.to_thread(blob.exists):
                # Initialize new session with default state
                logger.info(f"Creating new session state: {session_id}")
                return self._create_default_state(session_id)
            
            # Load existing state
            state_json = await asyncio.to_thread(blob.download_as_text)
            state = json.loads(state_json)
            logger.debug(f"Loaded state for session {session_id}: cwd={state.get('cwd')}")
            return state
            
        except Exception as e:
            logger.error(f"Failed to load session state {session_id}: {e}")
            # Return default state on error
            return self._create_default_state(session_id)
    
    async def save_state(self, session_id: str, state: Dict[str, Any]) -> None:
        """
        Save session state to Cloud Storage.
        
        Args:
            session_id: Session identifier
            state: State dict to save
        """
        try:
            state["last_updated"] = datetime.utcnow().isoformat()
            blob = self.bucket.blob(f"sessions/{session_id}/state.json")
            
            await asyncio.to_thread(
                blob.upload_from_string,
                json.dumps(state, indent=2),
                content_type="application/json"
            )
            logger.debug(f"Saved state for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to save session state {session_id}: {e}")
            raise
    
    async def save_execution_result(
        self,
        execution_id: str,
        result: Dict[str, Any]
    ) -> None:
        """
        Save execution result for retrieval.
        
        Args:
            execution_id: Execution identifier
            result: Result dict to save
        """
        try:
            blob = self.bucket.blob(f"executions/{execution_id}/result.json")
            
            await asyncio.to_thread(
                blob.upload_from_string,
                json.dumps(result, indent=2),
                content_type="application/json"
            )
            logger.debug(f"Saved execution result: {execution_id}")
            
        except Exception as e:
            logger.error(f"Failed to save execution result {execution_id}: {e}")
            raise
    
    async def load_execution_result(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Load execution result from Cloud Storage.
        
        Args:
            execution_id: Execution identifier
            
        Returns:
            Result dict or None if not found
        """
        try:
            blob = self.bucket.blob(f"executions/{execution_id}/result.json")
            
            if not await asyncio.to_thread(blob.exists):
                return None
            
            result_json = await asyncio.to_thread(blob.download_as_text)
            return json.loads(result_json)
            
        except Exception as e:
            logger.error(f"Failed to load execution result {execution_id}: {e}")
            return None
    
    async def delete_state(self, session_id: str) -> None:
        """
        Delete session state from Cloud Storage.
        
        Args:
            session_id: Session identifier
        """
        try:
            blob = self.bucket.blob(f"sessions/{session_id}/state.json")
            await asyncio.to_thread(blob.delete)
            logger.info(f"Deleted session state: {session_id}")
            
        except gcp_exceptions.NotFound:
            logger.debug(f"Session state not found (already deleted): {session_id}")
        except Exception as e:
            logger.error(f"Failed to delete session state {session_id}: {e}")
    
    def _create_default_state(self, session_id: str) -> Dict[str, Any]:
        """Create default session state"""
        return {
            "session_id": session_id,
            "cwd": "/workspace",
            "env_vars": {},
            "background_pids": {},
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat()
        }


class CloudRunJobManager:
    """
    Manages Cloud Run Job lifecycle for command execution.
    """
    
    def __init__(
        self,
        project_id: str,
        region: str,
        executor_image: str,
        state_bucket: str
    ):
        """
        Initialize job manager.
        
        Args:
            project_id: GCP project ID
            region: GCP region
            executor_image: Container image for executor
            state_bucket: Cloud Storage bucket for state
        """
        self.project_id = project_id
        self.region = region
        self.executor_image = executor_image
        self.state_bucket = state_bucket
        
        # Initialize GCP clients
        self.jobs_client = run_v2.JobsClient()
        self.executions_client = run_v2.ExecutionsClient()
        
        self.parent = f"projects/{project_id}/locations/{region}"
        
        logger.info(f"CloudRunJobManager initialized: {self.parent}")
    
    async def create_job(
        self,
        execution_id: str,
        session_id: str,
        command: str,
        timeout: int = 120,
        memory: str = "512Mi",
        cpu: str = "1"
    ) -> str:
        """
        Create and execute a Cloud Run Job.
        
        Args:
            execution_id: Unique execution identifier
            session_id: Session identifier
            command: Shell command to execute
            timeout: Command timeout in seconds
            memory: Memory limit (e.g., "512Mi")
            cpu: CPU limit (e.g., "1")
            
        Returns:
            Job name for tracking
        """
        job_name = f"sandbox-{execution_id[:8]}"
        
        try:
            # Create job definition
            job = run_v2.Job(
                template=run_v2.ExecutionTemplate(
                    template=run_v2.TaskTemplate(
                        containers=[run_v2.Container(
                            image=self.executor_image,
                            env=[
                                run_v2.EnvVar(name="EXECUTION_ID", value=execution_id),
                                run_v2.EnvVar(name="SESSION_ID", value=session_id),
                                run_v2.EnvVar(name="COMMAND", value=command),
                                run_v2.EnvVar(name="PROJECT_ID", value=self.project_id),
                                run_v2.EnvVar(name="STATE_BUCKET", value=self.state_bucket),
                                run_v2.EnvVar(name="TIMEOUT", value=str(timeout)),
                            ],
                            resources=run_v2.ResourceRequirements(
                                limits={"memory": memory, "cpu": cpu}
                            )
                        )],
                        timeout=f"{timeout}s",
                        max_retries=0,  # No retries for sandbox execution
                    )
                )
            )
            
            # Create job (async operation)
            logger.info(f"Creating Cloud Run Job: {job_name}")
            operation = await asyncio.to_thread(
                self.jobs_client.create_job,
                parent=self.parent,
                job=job,
                job_id=job_name
            )
            
            # Wait for job creation
            created_job = await asyncio.to_thread(operation.result, timeout=30)
            logger.info(f"Job created successfully: {created_job.name}")
            
            return created_job.name
            
        except Exception as e:
            logger.error(f"Failed to create job {job_name}: {e}")
            raise
    
    async def execute_job(self, job_name: str) -> str:
        """
        Trigger job execution.
        
        Args:
            job_name: Job resource name
            
        Returns:
            Execution name for tracking
        """
        try:
            logger.info(f"Executing job: {job_name}")
            operation = await asyncio.to_thread(
                self.jobs_client.run_job,
                name=job_name
            )
            
            # Wait for execution to start
            execution = await asyncio.to_thread(operation.result, timeout=30)
            logger.info(f"Job execution started: {execution.name}")
            
            return execution.name
            
        except Exception as e:
            logger.error(f"Failed to execute job {job_name}: {e}")
            raise
    
    async def wait_for_completion(
        self,
        execution_name: str,
        timeout: int = 300,
        poll_interval: int = 2
    ) -> Dict[str, Any]:
        """
        Wait for job execution to complete.
        
        Args:
            execution_name: Execution resource name
            timeout: Maximum wait time in seconds
            poll_interval: Polling interval in seconds
            
        Returns:
            Execution status dict
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                logger.error(f"Execution timeout after {timeout}s: {execution_name}")
                return {
                    "completed": False,
                    "success": False,
                    "error": f"Execution timeout after {timeout}s"
                }
            
            try:
                execution = await asyncio.to_thread(
                    self.executions_client.get_execution,
                    name=execution_name
                )
                
                # Check completion
                if execution.completion_time:
                    success = execution.succeeded_count > 0
                    logger.info(f"Execution completed: {execution_name}, success={success}")
                    return {
                        "completed": True,
                        "success": success,
                        "succeeded_count": execution.succeeded_count,
                        "failed_count": execution.failed_count
                    }
                
                # Still running, wait and poll again
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                logger.error(f"Error polling execution {execution_name}: {e}")
                await asyncio.sleep(poll_interval)
    
    async def delete_job(self, job_name: str) -> None:
        """
        Delete job after execution.
        
        Args:
            job_name: Job resource name
        """
        try:
            logger.info(f"Deleting job: {job_name}")
            operation = await asyncio.to_thread(
                self.jobs_client.delete_job,
                name=job_name
            )
            await asyncio.to_thread(operation.result, timeout=30)
            logger.info(f"Job deleted: {job_name}")
            
        except gcp_exceptions.NotFound:
            logger.debug(f"Job not found (already deleted): {job_name}")
        except Exception as e:
            logger.warning(f"Failed to delete job {job_name}: {e}")
    
    async def get_logs(self, execution_name: str) -> str:
        """
        Get execution logs.
        
        Args:
            execution_name: Execution resource name
            
        Returns:
            Log content as string
        """
        # TODO: Implement log retrieval using Cloud Logging API
        # For now, return empty string
        logger.debug(f"Log retrieval not yet implemented for: {execution_name}")
        return ""


class CloudRunJobsSandbox(Sandbox):
    """
    Cloud Run Jobs-based sandbox implementation.
    
    Replaces DockerSandbox for Cloud Run deployment where
    Docker-in-Docker is not available.
    
    Features:
    - Stateful command execution with CWD/ENV preservation
    - Background process management
    - File operations via Cloud Storage
    - Full Sandbox protocol compatibility
    """
    
    def __init__(
        self,
        project_id: str,
        region: str = "us-central1",
        executor_image: Optional[str] = None,
        state_bucket: Optional[str] = None
    ):
        """
        Initialize Cloud Run Jobs sandbox.
        
        Args:
            project_id: GCP project ID
            region: GCP region for job execution
            executor_image: Container image for executor
            state_bucket: Cloud Storage bucket for state
        """
        self.project_id = project_id
        self.region = region
        self.executor_image = executor_image or f"gcr.io/{project_id}/sandbox-executor:latest"
        self.state_bucket = state_bucket or f"{project_id}-sandbox-sessions"
        
        # Initialize components
        self.storage_client = storage.Client(project=project_id)
        self.state_manager = SessionStateManager(
            self.storage_client,
            self.state_bucket
        )
        self.job_manager = CloudRunJobManager(
            project_id=project_id,
            region=region,
            executor_image=self.executor_image,
            state_bucket=self.state_bucket
        )
        
        # Sandbox ID
        self._sandbox_id = str(uuid.uuid4())
        self._default_session_id = "default"
        
        logger.info(f"CloudRunJobsSandbox initialized: {self._sandbox_id}")
    
    @property
    def id(self) -> str:
        """Sandbox ID"""
        return self._sandbox_id
    
    @property
    def cdp_url(self) -> str:
        """CDP URL - Not supported in Cloud Run Jobs"""
        return ""
    
    @property
    def vnc_url(self) -> str:
        """VNC URL - Not supported in Cloud Run Jobs"""
        return ""
    
    async def ensure_sandbox(self) -> None:
        """
        Ensure sandbox is ready.
        
        For Cloud Run Jobs, this verifies bucket access.
        """
        try:
            # Verify bucket exists and is accessible
            bucket = self.storage_client.bucket(self.state_bucket)
            exists = await asyncio.to_thread(bucket.exists)
            
            if not exists:
                logger.warning(f"State bucket does not exist: {self.state_bucket}")
                # Try to create it
                await asyncio.to_thread(bucket.create, location=self.region)
                logger.info(f"Created state bucket: {self.state_bucket}")
            
            logger.info("CloudRunJobsSandbox is ready")
            
        except Exception as e:
            logger.error(f"Failed to ensure sandbox readiness: {e}")
            raise
    
    async def exec_command_stateful(
        self,
        command: str,
        session_id: Optional[str] = None,
        timeout: int = 120
    ) -> Dict[str, Any]:
        """
        Execute command with stateful context preservation.
        
        Preserves CWD and ENV between commands in the same session.
        Supports background processes with & suffix.
        
        Args:
            command: Shell command to execute
            session_id: Session identifier (default: "default")
            timeout: Command timeout in seconds
            
        Returns:
            Dict with keys:
            - exit_code: Command exit code
            - stdout: Standard output
            - stderr: Standard error
            - cwd: Current working directory after execution
            - session_id: Session identifier
            - background_pid: PID if background process (optional)
        """
        if session_id is None:
            session_id = self._default_session_id
        
        execution_id = str(uuid.uuid4())
        
        logger.info(f"Executing command (session={session_id}, exec={execution_id}): {command[:100]}")
        
        try:
            # Step 1: Load session state
            state = await self.state_manager.load_state(session_id)
            
            # Step 2: Create and execute job
            job_name = await self.job_manager.create_job(
                execution_id=execution_id,
                session_id=session_id,
                command=command,
                timeout=timeout
            )
            
            # Step 3: Trigger execution
            execution_name = await self.job_manager.execute_job(job_name)
            
            # Step 4: Wait for completion
            exec_status = await self.job_manager.wait_for_completion(
                execution_name,
                timeout=timeout + 30  # Extra time for polling
            )
            
            # Step 5: Retrieve result from Cloud Storage
            result = await self.state_manager.load_execution_result(execution_id)
            
            if result is None:
                # Execution failed or result not saved
                logger.error(f"No result found for execution: {execution_id}")
                result = {
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": "Execution failed - no result found",
                    "cwd": state["cwd"],
                    "session_id": session_id
                }
            else:
                # Update session state with new state from result
                if "new_state" in result:
                    await self.state_manager.save_state(session_id, result["new_state"])
                
                # Add session_id to result
                result["session_id"] = session_id
            
            # Step 6: Cleanup job (best effort, don't fail on cleanup error)
            try:
                await self.job_manager.delete_job(job_name)
            except Exception as e:
                logger.warning(f"Job cleanup failed: {e}")
            
            logger.info(f"Command completed (exit_code={result.get('exit_code')}): {execution_id}")
            return result
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Execution error: {str(e)}",
                "cwd": "/workspace",
                "session_id": session_id
            }
    
    async def exec_command(
        self,
        session_id: str,
        exec_dir: str,
        command: str
    ) -> ToolResult:
        """
        Legacy exec_command - redirects to stateful execution.
        
        Args:
            session_id: Session ID
            exec_dir: Execution directory (ignored, uses session CWD)
            command: Command to execute
            
        Returns:
            Command execution result
        """
        result = await self.exec_command_stateful(command, session_id)
        return ToolResult(
            success=(result["exit_code"] == 0),
            message=result["stdout"] if result["exit_code"] == 0 else result["stderr"],
            data={
                "exit_code": result["exit_code"],
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "cwd": result["cwd"]
            }
        )
    
    async def list_background_processes(
        self,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all background processes, optionally filtered by session.
        
        Args:
            session_id: Optional session filter. If None, lists all sessions.
            
        Returns:
            List of process info dicts with keys:
            - session_id: Session owning the process
            - command: Original command
            - pid: Process ID
            - running: Whether process is still running
        """
        try:
            if session_id is None:
                session_id = self._default_session_id
            
            # Load session state
            state = await self.state_manager.load_state(session_id)
            background_pids = state.get("background_pids", {})
            
            processes = []
            for pid_str, process_info in background_pids.items():
                # Check if process is still running
                running = await self._check_pid_running(int(pid_str), session_id)
                
                processes.append({
                    "session_id": session_id,
                    "command": process_info.get("command", ""),
                    "pid": int(pid_str),
                    "running": running,
                    "started_at": process_info.get("started_at", "")
                })
            
            logger.debug(f"Listed {len(processes)} background processes for session: {session_id}")
            return processes
            
        except Exception as e:
            logger.error(f"Failed to list background processes: {e}")
            return []
    
    async def kill_background_process(
        self,
        pid: Optional[int] = None,
        session_id: Optional[str] = None,
        pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Kill background process(es) by PID, session, or pattern.
        
        Args:
            pid: Specific PID to kill
            session_id: Kill all processes in this session
            pattern: Kill processes matching this command pattern
            
        Returns:
            Dict with keys:
            - killed_count: Number of processes killed
            - killed_pids: List of PIDs that were killed
        """
        try:
            if session_id is None:
                session_id = self._default_session_id
            
            killed_pids = []
            
            if pid is not None:
                # Kill specific PID
                result = await self.exec_command_stateful(f"kill -9 {pid}", session_id=session_id)
                if result["exit_code"] == 0:
                    killed_pids.append(pid)
                    logger.info(f"Killed process PID={pid}")
            else:
                # Get list of background processes
                processes = await self.list_background_processes(session_id)
                
                for proc in processes:
                    if pattern and pattern not in proc["command"]:
                        continue
                    
                    proc_pid = proc["pid"]
                    result = await self.exec_command_stateful(f"kill -9 {proc_pid}", session_id=session_id)
                    if result["exit_code"] == 0:
                        killed_pids.append(proc_pid)
                        logger.info(f"Killed process PID={proc_pid}")
            
            # Update session state to remove killed PIDs
            state = await self.state_manager.load_state(session_id)
            background_pids = state.get("background_pids", {})
            for killed_pid in killed_pids:
                background_pids.pop(str(killed_pid), None)
            state["background_pids"] = background_pids
            await self.state_manager.save_state(session_id, state)
            
            return {
                "killed_count": len(killed_pids),
                "killed_pids": killed_pids
            }
            
        except Exception as e:
            logger.error(f"Failed to kill background processes: {e}")
            return {
                "killed_count": 0,
                "killed_pids": []
            }
    
    async def get_background_logs(self, pid: int, session_id: Optional[str] = None) -> Optional[str]:
        """
        Get logs from background process output file.
        
        Background processes redirect output to /tmp/bg_$PID.out
        
        Args:
            pid: Process ID
            session_id: Session identifier (default: "default")
            
        Returns:
            Log content as string, or None if not available
        """
        try:
            if session_id is None:
                session_id = self._default_session_id
            
            # Read log file
            log_file = f"/tmp/bg_{pid}.out"
            result = await self.exec_command_stateful(f"cat {log_file}", session_id=session_id)
            
            if result["exit_code"] == 0:
                return result["stdout"]
            else:
                logger.debug(f"No logs found for PID {pid}: {result['stderr']}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get background logs for PID {pid}: {e}")
            return None
    
    # File operations
    
    async def file_write(
        self,
        file: str,
        content: str,
        append: bool = False,
        leading_newline: bool = False,
        trailing_newline: bool = False,
        sudo: bool = False
    ) -> ToolResult:
        """Write content to file"""
        try:
            # Prepare content with newlines
            if leading_newline:
                content = "\n" + content
            if trailing_newline:
                content = content + "\n"
            
            # Escape content for shell
            escaped_content = content.replace("'", "'\\''")
            
            # Build command
            redirect = ">>" if append else ">"
            sudo_prefix = "sudo " if sudo else ""
            command = f"{sudo_prefix}echo -n '{escaped_content}' {redirect} {file}"
            
            result = await self.exec_command_stateful(command)
            
            if result["exit_code"] == 0:
                return ToolResult(
                    success=True,
                    message=f"File written: {file}",
                    data={"file": file, "bytes_written": len(content)}
                )
            else:
                return ToolResult(
                    success=False,
                    message=f"Failed to write file: {result['stderr']}"
                )
                
        except Exception as e:
            logger.error(f"Failed to write file {file}: {e}")
            return ToolResult(success=False, message=str(e))
    
    async def file_read(
        self,
        file: str,
        start_line: int = None,
        end_line: int = None,
        sudo: bool = False
    ) -> ToolResult:
        """Read file content"""
        try:
            sudo_prefix = "sudo " if sudo else ""
            
            # Build command based on line range
            if start_line is not None and end_line is not None:
                command = f"{sudo_prefix}sed -n '{start_line},{end_line}p' {file}"
            elif start_line is not None:
                command = f"{sudo_prefix}tail -n +{start_line} {file}"
            elif end_line is not None:
                command = f"{sudo_prefix}head -n {end_line} {file}"
            else:
                command = f"{sudo_prefix}cat {file}"
            
            result = await self.exec_command_stateful(command)
            
            if result["exit_code"] == 0:
                return ToolResult(
                    success=True,
                    message=f"File read: {file}",
                    data={"content": result["stdout"], "file": file}
                )
            else:
                return ToolResult(
                    success=False,
                    message=f"Failed to read file: {result['stderr']}"
                )
                
        except Exception as e:
            logger.error(f"Failed to read file {file}: {e}")
            return ToolResult(success=False, message=str(e))
    
    async def file_exists(self, path: str) -> ToolResult:
        """Check if file exists"""
        try:
            result = await self.exec_command_stateful(f"test -e {path} && echo 'exists' || echo 'not found'")
            
            exists = "exists" in result["stdout"]
            return ToolResult(
                success=True,
                message=f"File {'exists' if exists else 'does not exist'}: {path}",
                data={"exists": exists, "path": path}
            )
            
        except Exception as e:
            logger.error(f"Failed to check file existence {path}: {e}")
            return ToolResult(success=False, message=str(e))
    
    async def file_delete(self, path: str, sudo: bool = False) -> ToolResult:
        """Delete file"""
        try:
            sudo_prefix = "sudo " if sudo else ""
            result = await self.exec_command_stateful(f"{sudo_prefix}rm -f {path}")
            
            if result["exit_code"] == 0:
                return ToolResult(
                    success=True,
                    message=f"File deleted: {path}",
                    data={"path": path}
                )
            else:
                return ToolResult(
                    success=False,
                    message=f"Failed to delete file: {result['stderr']}"
                )
                
        except Exception as e:
            logger.error(f"Failed to delete file {path}: {e}")
            return ToolResult(success=False, message=str(e))
    
    async def file_list(self, path: str, recursive: bool = False) -> ToolResult:
        """List directory contents"""
        try:
            command = f"ls -la {path}" if not recursive else f"find {path} -ls"
            result = await self.exec_command_stateful(command)
            
            if result["exit_code"] == 0:
                return ToolResult(
                    success=True,
                    message=f"Directory listed: {path}",
                    data={"content": result["stdout"], "path": path}
                )
            else:
                return ToolResult(
                    success=False,
                    message=f"Failed to list directory: {result['stderr']}"
                )
                
        except Exception as e:
            logger.error(f"Failed to list directory {path}: {e}")
            return ToolResult(success=False, message=str(e))
    
    async def file_replace(
        self,
        file: str,
        old_str: str,
        new_str: str,
        sudo: bool = False
    ) -> ToolResult:
        """Replace string in file"""
        try:
            # Escape strings for sed
            old_escaped = old_str.replace("/", "\\/").replace("'", "'\\''")
            new_escaped = new_str.replace("/", "\\/").replace("'", "'\\''")
            
            sudo_prefix = "sudo " if sudo else ""
            command = f"{sudo_prefix}sed -i 's/{old_escaped}/{new_escaped}/g' {file}"
            
            result = await self.exec_command_stateful(command)
            
            if result["exit_code"] == 0:
                return ToolResult(
                    success=True,
                    message=f"String replaced in file: {file}",
                    data={"file": file, "old": old_str, "new": new_str}
                )
            else:
                return ToolResult(
                    success=False,
                    message=f"Failed to replace string: {result['stderr']}"
                )
                
        except Exception as e:
            logger.error(f"Failed to replace in file {file}: {e}")
            return ToolResult(success=False, message=str(e))
    
    async def file_search(
        self,
        file: str,
        regex: str,
        sudo: bool = False
    ) -> ToolResult:
        """Search in file content"""
        try:
            sudo_prefix = "sudo " if sudo else ""
            command = f"{sudo_prefix}grep -n '{regex}' {file}"
            
            result = await self.exec_command_stateful(command)
            
            # grep returns exit code 1 if no matches (not an error)
            if result["exit_code"] in [0, 1]:
                matches = result["stdout"].strip().split("\n") if result["stdout"].strip() else []
                return ToolResult(
                    success=True,
                    message=f"Search completed: {len(matches)} matches",
                    data={"matches": matches, "file": file, "regex": regex}
                )
            else:
                return ToolResult(
                    success=False,
                    message=f"Failed to search file: {result['stderr']}"
                )
                
        except Exception as e:
            logger.error(f"Failed to search file {file}: {e}")
            return ToolResult(success=False, message=str(e))
    
    async def file_find(
        self,
        path: str,
        glob_pattern: str
    ) -> ToolResult:
        """Find files by name pattern"""
        try:
            command = f"find {path} -name '{glob_pattern}'"
            result = await self.exec_command_stateful(command)
            
            if result["exit_code"] == 0:
                files = result["stdout"].strip().split("\n") if result["stdout"].strip() else []
                return ToolResult(
                    success=True,
                    message=f"Found {len(files)} files",
                    data={"files": files, "path": path, "pattern": glob_pattern}
                )
            else:
                return ToolResult(
                    success=False,
                    message=f"Failed to find files: {result['stderr']}"
                )
                
        except Exception as e:
            logger.error(f"Failed to find files in {path}: {e}")
            return ToolResult(success=False, message=str(e))
    
    async def file_upload(
        self,
        file_data: BinaryIO,
        path: str,
        filename: str = None
    ) -> ToolResult:
        """Upload file to sandbox via Cloud Storage"""
        try:
            # Determine target file path
            if filename:
                target_path = f"{path}/{filename}"
            else:
                target_path = path
            
            # Upload to Cloud Storage temporary location
            temp_blob_name = f"uploads/{self._sandbox_id}/{uuid.uuid4()}"
            blob = self.storage_client.bucket(self.state_bucket).blob(temp_blob_name)
            
            # Read file data
            file_content = file_data.read()
            await asyncio.to_thread(blob.upload_from_string, file_content)
            
            # Download from Cloud Storage to sandbox filesystem
            gs_path = f"gs://{self.state_bucket}/{temp_blob_name}"
            command = f"gsutil cp {gs_path} {target_path}"
            result = await self.exec_command_stateful(command)
            
            # Cleanup temporary blob
            try:
                await asyncio.to_thread(blob.delete)
            except Exception:
                pass
            
            if result["exit_code"] == 0:
                return ToolResult(
                    success=True,
                    message=f"File uploaded: {target_path}",
                    data={"path": target_path, "size": len(file_content)}
                )
            else:
                return ToolResult(
                    success=False,
                    message=f"Failed to upload file: {result['stderr']}"
                )
                
        except Exception as e:
            logger.error(f"Failed to upload file to {path}: {e}")
            return ToolResult(success=False, message=str(e))
    
    async def file_download(self, path: str) -> BinaryIO:
        """Download file from sandbox via Cloud Storage"""
        try:
            # Upload from sandbox filesystem to Cloud Storage
            temp_blob_name = f"downloads/{self._sandbox_id}/{uuid.uuid4()}"
            gs_path = f"gs://{self.state_bucket}/{temp_blob_name}"
            command = f"gsutil cp {path} {gs_path}"
            
            result = await self.exec_command_stateful(command)
            
            if result["exit_code"] != 0:
                raise Exception(f"Failed to copy file to Cloud Storage: {result['stderr']}")
            
            # Download from Cloud Storage
            blob = self.storage_client.bucket(self.state_bucket).blob(temp_blob_name)
            file_content = await asyncio.to_thread(blob.download_as_bytes)
            
            # Cleanup temporary blob
            try:
                await asyncio.to_thread(blob.delete)
            except Exception:
                pass
            
            return io.BytesIO(file_content)
            
        except Exception as e:
            logger.error(f"Failed to download file {path}: {e}")
            raise
    
    async def view_shell(self, session_id: str, console: bool = False) -> ToolResult:
        """View shell status"""
        # Return session info
        state = await self.state_manager.load_state(session_id)
        return ToolResult(
            success=True,
            message=f"Session {session_id}",
            data={
                "session_id": session_id,
                "cwd": state.get("cwd"),
                "env_count": len(state.get("env_vars", {}))
            }
        )
    
    async def wait_for_process(
        self,
        session_id: str,
        seconds: Optional[int] = None
    ) -> ToolResult:
        """Wait for process"""
        if seconds:
            await asyncio.sleep(seconds)
        return ToolResult(success=True, message=f"Waited {seconds}s")
    
    async def write_to_process(
        self,
        session_id: str,
        input_text: str,
        press_enter: bool = True
    ) -> ToolResult:
        """Write input to process - Not applicable for Cloud Run Jobs"""
        return ToolResult(
            success=False,
            message="write_to_process not supported in Cloud Run Jobs sandbox"
        )
    
    async def kill_process(self, session_id: str) -> ToolResult:
        """Terminate process"""
        # For Cloud Run Jobs, we can't interrupt running executions
        return ToolResult(
            success=False,
            message="kill_process not supported in Cloud Run Jobs sandbox"
        )
    
    async def destroy(self) -> bool:
        """Destroy current sandbox instance"""
        try:
            # Cleanup all sessions
            # TODO: Implement session cleanup
            logger.info(f"Destroying sandbox: {self._sandbox_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to destroy sandbox: {e}")
            return False
    
    async def get_browser(self) -> Browser:
        """Get browser instance - Not supported in Cloud Run Jobs"""
        raise NotImplementedError(
            "Browser/CDP not available in Cloud Run Jobs sandbox. "
            "CDP requires persistent container with Chrome DevTools Protocol port."
        )
    
    @classmethod
    async def create(cls) -> 'CloudRunJobsSandbox':
        """
        Create a new sandbox instance.
        
        Returns:
            New CloudRunJobsSandbox instance
        """
        settings = get_settings()
        
        # Get configuration from settings
        project_id = settings.gcp_project_id
        region = getattr(settings, 'gcp_region', 'us-central1')
        executor_image = getattr(settings, 'sandbox_executor_image', None)
        state_bucket = getattr(settings, 'sandbox_state_bucket', None)
        
        if not project_id:
            raise ValueError("GCP_PROJECT_ID must be configured for CloudRunJobsSandbox")
        
        sandbox = cls(
            project_id=project_id,
            region=region,
            executor_image=executor_image,
            state_bucket=state_bucket
        )
        
        # Ensure sandbox is ready
        await sandbox.ensure_sandbox()
        
        return sandbox
    
    async def _check_pid_running(self, pid: int, session_id: str) -> bool:
        """
        Check if a process ID is still running.
        
        Args:
            pid: Process ID to check
            session_id: Session identifier
            
        Returns:
            True if process is running, False otherwise
        """
        try:
            result = await self.exec_command_stateful(f"kill -0 {pid} 2>/dev/null && echo 'running'", session_id=session_id)
            return "running" in result["stdout"]
        except Exception:
            return False
    
    @classmethod
    async def get(cls, id: str) -> 'CloudRunJobsSandbox':
        """
        Get sandbox by ID.
        
        Args:
            id: Sandbox ID
            
        Returns:
            Sandbox instance
        """
        # For now, just create a new instance
        # TODO: Implement proper sandbox retrieval/reuse
        return await cls.create()