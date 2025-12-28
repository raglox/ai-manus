#!/usr/bin/env python3
"""
Cloud Run Jobs Sandbox Executor

This script runs inside Cloud Run Jobs to execute commands in a sandboxed environment
with state persistence across executions.
"""

import os
import sys
import json
import subprocess
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
from google.cloud import storage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("sandbox-executor")


class ExecutionContext:
    """Manages execution context including CWD, ENV, and background processes."""
    
    def __init__(self, state: Dict[str, Any]):
        self.cwd = state.get("cwd", "/workspace")
        self.env = state.get("env", {})
        self.background_processes = state.get("background_processes", {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization."""
        return {
            "cwd": self.cwd,
            "env": self.env,
            "background_processes": self.background_processes
        }


class StateManager:
    """Manages session state persistence in Cloud Storage."""
    
    def __init__(self, project_id: str, bucket_name: str, session_id: str):
        self.client = storage.Client(project=project_id)
        self.bucket = self.client.bucket(bucket_name)
        self.session_id = session_id
        self.state_path = f"sessions/{session_id}/state.json"
    
    def load_state(self) -> Dict[str, Any]:
        """Load session state from Cloud Storage."""
        try:
            blob = self.bucket.blob(self.state_path)
            if blob.exists():
                content = blob.download_as_text()
                state = json.loads(content)
                logger.info(f"Loaded state for session {self.session_id}")
                return state
            else:
                logger.info(f"No existing state for session {self.session_id}, using defaults")
                return self._default_state()
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            return self._default_state()
    
    def save_state(self, state: Dict[str, Any]) -> bool:
        """Save session state to Cloud Storage."""
        try:
            blob = self.bucket.blob(self.state_path)
            content = json.dumps(state, indent=2)
            blob.upload_from_string(
                content,
                content_type="application/json"
            )
            logger.info(f"Saved state for session {self.session_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving state: {e}")
            return False
    
    def _default_state(self) -> Dict[str, Any]:
        """Return default state for new sessions."""
        return {
            "cwd": "/workspace",
            "env": dict(os.environ),
            "background_processes": {},
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat()
        }


class CommandExecutor:
    """Executes commands with state preservation."""
    
    def __init__(self, context: ExecutionContext):
        self.context = context
    
    def execute(self, command: str) -> Dict[str, Any]:
        """Execute command and return result."""
        logger.info(f"Executing command: {command}")
        
        # Check if it's a background process (ends with &)
        is_background = command.strip().endswith("&")
        if is_background:
            command = command.strip()[:-1].strip()
            return self._execute_background(command)
        
        # Execute regular command
        return self._execute_regular(command)
    
    def _execute_regular(self, command: str) -> Dict[str, Any]:
        """Execute regular (foreground) command."""
        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(self.context.env)
            
            # Execute command
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.context.cwd,
                env=env,
                text=True
            )
            
            stdout, stderr = process.communicate(timeout=120)
            exit_code = process.returncode
            
            # Update CWD if command was 'cd'
            if command.strip().startswith("cd "):
                new_cwd = command.strip()[3:].strip()
                if new_cwd.startswith("/"):
                    self.context.cwd = new_cwd
                else:
                    self.context.cwd = os.path.normpath(
                        os.path.join(self.context.cwd, new_cwd)
                    )
            
            result = {
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "execution_time": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Command completed with exit code: {exit_code}")
            return result
            
        except subprocess.TimeoutExpired:
            logger.error("Command timed out")
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": "Command timed out after 120 seconds",
                "execution_time": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "execution_time": datetime.utcnow().isoformat()
            }
    
    def _execute_background(self, command: str) -> Dict[str, Any]:
        """Execute background process with output redirection."""
        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(self.context.env)
            
            # Create a wrapper script to redirect output
            # This ensures output is captured even after the executor exits
            pid = os.getpid() + 1000  # Approximate next PID
            log_file = f"/tmp/bg_{pid}.out"
            
            # Build command with output redirection
            redirected_command = f"nohup {command} > {log_file} 2>&1 &"
            
            # Execute the command
            process = subprocess.Popen(
                redirected_command,
                shell=True,
                cwd=self.context.cwd,
                env=env,
                start_new_session=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Get the actual PID
            time.sleep(0.1)  # Brief wait to ensure process started
            actual_pid = process.pid
            
            # Store background process info in context
            self.context.background_processes[str(actual_pid)] = {
                "command": command,
                "pid": actual_pid,
                "log_file": log_file,
                "started_at": datetime.utcnow().isoformat(),
                "status": "running"
            }
            
            result = {
                "exit_code": 0,
                "stdout": f"Background process started with PID: {actual_pid}\nLogs: {log_file}",
                "stderr": "",
                "background_pid": actual_pid,
                "log_file": log_file,
                "execution_time": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Started background process with PID: {actual_pid}, logs: {log_file}")
            return result
            
        except Exception as e:
            logger.error(f"Error starting background process: {e}")
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "execution_time": datetime.utcnow().isoformat()
            }


def main():
    """Main execution entry point."""
    try:
        # Get execution parameters from environment
        execution_id = os.environ.get("EXECUTION_ID")
        session_id = os.environ.get("SESSION_ID")
        command = os.environ.get("COMMAND")
        project_id = os.environ.get("PROJECT_ID")
        bucket_name = os.environ.get("BUCKET_NAME", "manus-sandbox-state")
        
        if not all([execution_id, session_id, command, project_id]):
            logger.error("Missing required environment variables")
            sys.exit(1)
        
        logger.info(f"Starting execution {execution_id} for session {session_id}")
        
        # Initialize state manager
        state_manager = StateManager(project_id, bucket_name, session_id)
        
        # Load session state
        state = state_manager.load_state()
        context = ExecutionContext(state)
        
        # Execute command
        executor = CommandExecutor(context)
        result = executor.execute(command)
        
        # Update state with new context
        state.update(context.to_dict())
        state["last_updated"] = datetime.utcnow().isoformat()
        state["last_execution_id"] = execution_id
        
        # Prepare result with new state
        result_with_state = {
            **result,
            "cwd": context.cwd,
            "new_state": {
                "session_id": session_id,
                "cwd": context.cwd,
                "env_vars": context.env,
                "background_pids": context.background_processes,
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
        # Save execution result to the path CloudRunJobsSandbox expects
        result_path = f"executions/{execution_id}/result.json"
        result_blob = state_manager.bucket.blob(result_path)
        result_blob.upload_from_string(
            json.dumps(result_with_state, indent=2),
            content_type="application/json"
        )
        
        # Save updated state
        state_manager.save_state(state)
        
        logger.info(f"Execution {execution_id} completed successfully")
        
        # Print result for Cloud Run Jobs to capture
        print(json.dumps(result))
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Fatal error in main execution: {e}", exc_info=True)
        error_result = {
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Fatal error: {str(e)}",
            "execution_time": datetime.utcnow().isoformat()
        }
        print(json.dumps(error_result))
        sys.exit(1)


if __name__ == "__main__":
    main()