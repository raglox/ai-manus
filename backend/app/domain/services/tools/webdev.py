"""
Web Development Tools for AI-Manus Agent System.

This module provides specialized tools for web development workflows,
enabling agents to start/stop development servers and detect their URLs.

Inspired by OpenHands SDK Terminal Tool best practices:
- Long-running processes should use background execution with output redirection
- Example: `python3 app.py > server.log 2>&1 &`

Reference: https://github.com/OpenHands/software-agent-sdk
"""

import re
import time
import asyncio
from typing import Optional, Dict, Any, List
from app.domain.external.sandbox import Sandbox
from app.domain.services.tools.base import tool, BaseTool
from app.domain.models.tool_result import ToolResult
import logging

logger = logging.getLogger(__name__)


# Security: Allowed server commands (whitelist)
ALLOWED_SERVER_COMMANDS = {
    'npm', 'node', 'python', 'python3', 'flask', 'uvicorn',
    'gunicorn', 'django-admin', 'php', 'ruby', 'rails', 'deno',
    'bun', 'pnpm', 'yarn', 'next', 'vite', 'webpack-dev-server'
}


class WebDevTool(BaseTool):
    """
    Web Development tool for starting/stopping development servers.
    
    Features:
    - Start web servers in background with URL detection
    - Stop servers by PID or pattern
    - Monitor server logs
    - List running servers
    
    Based on StatefulSandbox background process capabilities.
    """

    name: str = "webdev"
    
    def __init__(self, sandbox: Sandbox):
        """Initialize Web Development tool
        
        Args:
            sandbox: Sandbox service with background process support
        """
        super().__init__()
        self.sandbox = sandbox
        self._started_servers: List[int] = []  # ✅ Track started server PIDs for cleanup
    
    def _validate_command(self, command: str) -> None:
        """✅ SECURITY: Validate server command before execution.
        
        Args:
            command: Command to validate
            
        Raises:
            ValueError: If command is unsafe
        """
        if not command or not command.strip():
            raise ValueError("Command cannot be empty")
        
        # Extract first word (the actual command)
        first_word = command.strip().split()[0]
        
        # Disallow path segments to avoid executing arbitrary binaries
        if '/' in first_word:
            raise ValueError("Command must not include path separators or custom binary paths.")
        
        # Path separators are blocked above; use the raw command name
        command_name = first_word
        
        # Check whitelist
        if command_name not in ALLOWED_SERVER_COMMANDS:
            raise ValueError(
                f"Command '{command_name}' is not allowed for web servers. "
                f"Allowed commands: {', '.join(sorted(ALLOWED_SERVER_COMMANDS))}"
            )
        
        # Check for dangerous characters
        dangerous_chars = [';', '|', '&&', '||', '`', '$(']
        for char in dangerous_chars:
            if char in command:
                raise ValueError(
                    f"Command contains dangerous character/sequence: '{char}'. "
                    f"This could be a security risk."
                )
        
        logger.debug(f"Command validation passed: {command}")
    
    def _validate_pid(self, pid: int) -> None:
        """✅ Validate PID.
        
        Args:
            pid: Process ID to validate
            
        Raises:
            ValueError: If PID is invalid
        """
        if pid is None:
            raise ValueError("PID cannot be None")
        if not isinstance(pid, int):
            raise ValueError(f"PID must be an integer, got {type(pid)}")
        if pid <= 0:
            raise ValueError(f"PID must be positive, got {pid}")
    
    async def cleanup(self) -> Dict[str, Any]:
        """✅ Cleanup all resources started by this tool.
        
        Stops all servers that were started through this tool instance.
        
        Returns:
            Dict with cleanup stats:
            - stopped_count: Number of servers stopped
            - stopped_pids: List of PIDs that were stopped
            - failed_pids: List of PIDs that failed to stop
        """
        stopped_pids = []
        failed_pids = []
        
        logger.info(f"Cleaning up {len(self._started_servers)} tracked servers...")
        
        for pid in list(self._started_servers):  # Copy list to avoid modification during iteration
            try:
                result = await self.stop_server(pid)
                if result.success:
                    stopped_pids.append(pid)
                else:
                    failed_pids.append(pid)
            except Exception as e:
                logger.error(f"Failed to stop server {pid} during cleanup: {e}")
                failed_pids.append(pid)
        
        logger.info(f"Cleanup complete: {len(stopped_pids)} stopped, {len(failed_pids)} failed")
        
        return {
            "stopped_count": len(stopped_pids),
            "stopped_pids": stopped_pids,
            "failed_pids": failed_pids
        }
        
    @tool(
        name="start_server",
        description=(
            "Start a web development server in the background and detect its URL. "
            "This tool runs long-running server processes (like npm run dev, python -m http.server, etc.) "
            "in the background and monitors their logs to automatically extract the server URL. "
            "IMPORTANT: Use this tool instead of shell_exec for web servers to avoid blocking execution. "
            "The server will continue running in the background and you'll receive its PID for management."
        ),
        parameters={
            "command": {
                "type": "string",
                "description": (
                    "The server command to execute in background. "
                    "Examples: 'npm run dev', 'python3 -m http.server 8080', 'python server.py', "
                    "'node app.js', 'flask run', 'uvicorn main:app --reload'. "
                    "The command will be automatically run with output redirection."
                )
            },
            "timeout_seconds": {
                "type": "integer",
                "description": (
                    "Maximum time to wait for URL detection in server logs (default: 10 seconds). "
                    "Use higher values (30-60) for slow-starting frameworks like Next.js or Django."
                )
            },
            "session_id": {
                "type": "string",
                "description": "Optional session identifier (defaults to 'default')"
            }
        },
        required=["command"]
    )
    async def start_server(
        self,
        command: str,
        timeout_seconds: int = 10,
        session_id: Optional[str] = None
    ) -> ToolResult:
        """
        Start a web server in background and detect its URL.
        
        Process:
        1. Starts the command in background with output redirection
        2. Monitors logs for URL patterns (http://localhost:PORT, http://127.0.0.1:PORT)
        3. Returns the detected URL and PID for management
        
        Args:
            command: Server command (e.g., "npm run dev")
            timeout_seconds: Maximum wait time for URL detection
            session_id: Session identifier
            
        Returns:
            ToolResult with:
            - success: True if server started
            - message: Status message with URL and PID
            - data: {url, pid, command, log_file}
            
        Example:
            result = await start_server(
                command="python3 -m http.server 8080",
                timeout_seconds=10
            )
            # Result: "Server started on http://localhost:8080 with PID 12345"
        """
        try:
            # ✅ SECURITY: Validate command before execution
            self._validate_command(command)
            
            # Start server in background with & suffix
            logger.info(f"Starting server: {command}")
            
            result = await self.sandbox.exec_command_stateful(
                f"{command} &",
                session_id=session_id
            )
            
            if result["exit_code"] != 0:
                return ToolResult(
                    success=False,
                    message=f"Failed to start server: {result.get('stderr', 'Unknown error')}",
                    data={"command": command, "error": result.get('stderr')}
                )
            
            pid = result.get("background_pid")
            if not pid:
                return ToolResult(
                    success=False,
                    message="Server started but PID not detected. Command may not support background execution.",
                    data={"command": command}
                )
            
            # ✅ Track started server
            self._started_servers.append(pid)
            
            log_file = f"/tmp/bg_{pid}.out"
            logger.info(f"Server started with PID {pid}, monitoring logs at {log_file}")
            
            # Monitor logs for URL detection
            detected_url = await self._detect_server_url(
                pid=pid,
                timeout_seconds=timeout_seconds,
                session_id=session_id
            )
            
            if detected_url:
                message = f"✅ Server started successfully!\n\n"
                message += f"🌐 URL: {detected_url}\n"
                message += f"🔢 PID: {pid}\n"
                message += f"📝 Logs: {log_file}\n\n"
                message += f"Use 'stop_server' with PID {pid} to stop the server."
                
                return ToolResult(
                    success=True,
                    message=message,
                    data={
                        "url": detected_url,
                        "pid": pid,
                        "command": command,
                        "log_file": log_file,
                        "session_id": session_id or "default"
                    }
                )
            else:
                # Server started but no URL detected yet
                message = f"⚠️ Server started (PID: {pid}) but no URL detected yet.\n\n"
                message += f"The server may be starting up. Check logs at: {log_file}\n"
                message += f"Common URLs to try:\n"
                message += f"  - http://localhost:3000 (Node.js/React)\n"
                message += f"  - http://localhost:8000 (Python/Django)\n"
                message += f"  - http://localhost:8080 (General)\n"
                message += f"  - http://localhost:5000 (Flask)\n\n"
                message += f"Use 'get_server_logs' to view detailed logs."
                
                return ToolResult(
                    success=True,
                    message=message,
                    data={
                        "url": None,
                        "pid": pid,
                        "command": command,
                        "log_file": log_file,
                        "session_id": session_id or "default"
                    }
                )
                
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            return ToolResult(
                success=False,
                message=f"Error starting server: {str(e)}",
                data={"command": command, "error": str(e)}
            )
    
    async def _detect_server_url(
        self,
        pid: int,
        timeout_seconds: int,
        session_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Monitor server logs to detect URL.
        
        ✅ FIXED:
        - Memory leak: Now reads only new log lines incrementally
        - Race condition: Takes LAST match instead of first
        - Better pattern matching with context keywords
        
        Searches for patterns like:
        - http://localhost:8080
        - http://127.0.0.1:3000
        - https://localhost:5000
        - Server running on http://0.0.0.0:8000
        
        Args:
            pid: Process ID (must be valid positive integer)
            timeout_seconds: Maximum wait time
            session_id: Session identifier
            
        Returns:
            Detected URL or None
        """
        # ✅ FIXED: Validate PID
        if pid is None or pid <= 0:
            logger.error(f"Invalid PID: {pid}")
            return None
        
        # URL detection patterns (with optional paths)
        url_patterns = [
            r'https?://localhost:\d+(?:/[^\s]*)?',
            r'https?://127\.0\.0\.1:\d+(?:/[^\s]*)?',
            r'https?://0\.0\.0\.0:\d+(?:/[^\s]*)?',
            r'https?://\[::\d*\]:\d+',  # IPv6 any
            r'https?://\[::1?\]:\d+',  # IPv6 localhost
        ]
        
        # Context keywords that indicate actual server start (not errors)
        server_keywords = ['listening', 'running', 'started', 'ready', 'server', 'app']
        
        log_file = f"/tmp/bg_{pid}.out"
        start_time = time.monotonic()
        last_read_size = 0  # ✅ FIXED: Track position to avoid re-reading
        max_bytes_per_read = 65536  # Cap per-read size to avoid log flooding stalls
        max_total_bytes = 5 * 1024 * 1024  # Hard stop for excessive output
        empty_reads = 0
        
        while (time.monotonic() - start_time) < timeout_seconds:
            try:
                if last_read_size > max_total_bytes:
                    logger.warning(f"Aborting URL detection for PID {pid}: log size exceeded {max_total_bytes} bytes")
                    break
                # ✅ FIXED: Read only NEW log content to prevent memory leak
                result = await self.sandbox.exec_command_stateful(
                    (
                        f"if [ -f {log_file} ]; then "
                        f"tail -c +{last_read_size + 1} {log_file} 2>/dev/null | head -c {max_bytes_per_read}; "
                        f"else echo ''; fi"
                    ),
                    session_id=session_id
                )
                
                new_logs = result.get("stdout", "")
                
                if new_logs:
                    empty_reads = 0
                    last_read_size += len(new_logs.encode('utf-8'))
                    
                    # ✅ FIXED: Search line by line with context
                    for line in new_logs.split('\n'):
                        line_lower = line.lower()
                        
                        # Check if line contains server-related keywords
                        has_context = any(keyword in line_lower for keyword in server_keywords)
                        
                        if has_context:
                            for pattern in url_patterns:
                                matches = re.findall(pattern, line)
                                if matches:
                                    # ✅ FIXED: Take LAST match (most recent)
                                    url = matches[-1]
                                    # Remove trailing slashes and normalize
                                    url = url.rstrip('/')
                                    url = url.replace('0.0.0.0', 'localhost')
                                    logger.info(f"Detected server URL: {url} (from line: {line.strip()})")
                                    return url

                else:
                    empty_reads += 1
                    # If there's nothing new and the process exited, bail out early (check sparingly)
                    if empty_reads >= 2:
                        status = await self.sandbox.exec_command_stateful(f"ps -p {pid}", session_id=session_id)
                        if status.get("exit_code", 1) != 0:
                            logger.warning(f"Process {pid} exited before URL detection")
                            break
                        empty_reads = 0

                # Wait before next check
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"Error reading logs for PID {pid}: {e}")
                await asyncio.sleep(0.5)
        
        logger.warning(f"URL detection timed out after {timeout_seconds} seconds for PID {pid}")
        return None
    
    @tool(
        name="stop_server",
        description=(
            "Stop a running web server by its PID. "
            "Use this to cleanly shutdown development servers started with 'start_server'. "
            "You can find the PID from the 'start_server' response or by using 'list_servers'."
        ),
        parameters={
            "pid": {
                "type": "integer",
                "description": "Process ID of the server to stop (obtained from start_server)"
            }
        },
        required=["pid"]
    )
    async def stop_server(self, pid: int) -> ToolResult:
        """
        Stop a web server by PID.
        
        ✅ IMPROVED:
        - PID validation
        - Check process exists before killing
        - Try SIGTERM first, then SIGKILL if needed
        - Remove from tracking list
        
        Args:
            pid: Process ID to kill
            
        Returns:
            ToolResult with success status
            
        Example:
            result = await stop_server(pid=12345)
            # Result: "✅ Server with PID 12345 stopped successfully"
        """
        try:
            # ✅ Validate PID
            self._validate_pid(pid)
            
            # Check if process exists
            check_result = await self.sandbox.exec_command_stateful(f"ps -p {pid}")
            if check_result["exit_code"] != 0:
                return ToolResult(
                    success=False,
                    message=f"❌ Process {pid} does not exist or already stopped.",
                    data={"pid": pid, "exists": False}
                )
            
            # Try to kill the process
            result = await self.sandbox.kill_background_process(pid=pid)
            
            killed_count = result.get("killed_count", 0)
            
            if killed_count > 0:
                # ✅ Remove from tracking
                if pid in self._started_servers:
                    self._started_servers.remove(pid)
                
                # Verify it's actually stopped
                await asyncio.sleep(0.5)
                recheck = await self.sandbox.exec_command_stateful(f"ps -p {pid}")
                
                if recheck["exit_code"] == 0:
                    # Still running! Force kill
                    logger.warning(f"PID {pid} still running, using SIGKILL")
                    await self.sandbox.exec_command_stateful(f"kill -9 {pid}")
                    return ToolResult(
                        success=True,
                        message=f"⚠️ Server with PID {pid} forcefully killed (SIGKILL).",
                        data={"pid": pid, "method": "SIGKILL"}
                    )
                
                return ToolResult(
                    success=True,
                    message=f"✅ Server with PID {pid} stopped successfully.",
                    data={"pid": pid, "killed_count": killed_count, "method": "SIGTERM"}
                )
            else:
                return ToolResult(
                    success=False,
                    message=f"❌ Failed to stop server with PID {pid}. Process may not exist or already stopped.",
                    data={"pid": pid, "killed_count": 0}
                )
                
        except ValueError as e:
            # Validation error
            logger.error(f"PID validation failed: {e}")
            return ToolResult(
                success=False,
                message=f"Invalid PID: {str(e)}",
                data={"pid": pid, "error": "validation_error"}
            )
        except Exception as e:
            logger.error(f"Error stopping server: {e}")
            return ToolResult(
                success=False,
                message=f"Error stopping server: {str(e)}",
                data={"pid": pid, "error": str(e)}
            )
    
    @tool(
        name="list_servers",
        description=(
            "List all running background servers with their PIDs, commands, and status. "
            "Use this to see which servers are currently running and get their PIDs for management."
        ),
        parameters={
            "session_id": {
                "type": "string",
                "description": "Optional session filter. If not provided, lists from all sessions."
            }
        },
        required=[]
    )
    async def list_servers(self, session_id: Optional[str] = None) -> ToolResult:
        """
        List all running background processes (servers).
        
        Args:
            session_id: Optional session filter
            
        Returns:
            ToolResult with list of servers
            
        Example:
            result = await list_servers()
            # Shows: PID, command, session, running status
        """
        try:
            processes = await self.sandbox.list_background_processes(session_id)
            
            if not processes:
                return ToolResult(
                    success=True,
                    message="No background servers currently running.",
                    data={"processes": []}
                )
            
            # Format output
            message = f"📋 Running Servers ({len(processes)} total):\n\n"
            
            for i, proc in enumerate(processes, 1):
                status = "🟢 Running" if proc.get("running") else "🔴 Stopped"
                message += f"{i}. {status}\n"
                message += f"   PID: {proc.get('pid')}\n"
                message += f"   Command: {proc.get('command')}\n"
                message += f"   Session: {proc.get('session_id')}\n"
                message += f"   Logs: /tmp/bg_{proc.get('pid')}.out\n\n"
            
            return ToolResult(
                success=True,
                message=message,
                data={"processes": processes, "count": len(processes)}
            )
            
        except Exception as e:
            logger.error(f"Error listing servers: {e}")
            return ToolResult(
                success=False,
                message=f"Error listing servers: {str(e)}",
                data={"error": str(e)}
            )
    
    @tool(
        name="get_server_logs",
        description=(
            "Retrieve logs from a running or stopped server. "
            "Logs are stored in /tmp/bg_$PID.out and contain stdout/stderr output."
        ),
        parameters={
            "pid": {
                "type": "integer",
                "description": "Process ID of the server"
            },
            "tail_lines": {
                "type": "integer",
                "description": "Number of last lines to return (default: 50). Use -1 for all logs."
            }
        },
        required=["pid"]
    )
    async def get_server_logs(
        self,
        pid: int,
        tail_lines: int = 50
    ) -> ToolResult:
        """
        Get logs from a server process.
        
        Args:
            pid: Process ID
            tail_lines: Number of lines to return (-1 for all)
            
        Returns:
            ToolResult with log content
        """
        try:
            logs = await self.sandbox.get_background_logs(pid)
            
            if not logs:
                return ToolResult(
                    success=False,
                    message=f"No logs found for PID {pid}. Server may not exist or log file was deleted.",
                    data={"pid": pid}
                )
            
            # Tail logs if requested
            if tail_lines > 0:
                lines = logs.split('\n')
                logs = '\n'.join(lines[-tail_lines:])
            
            message = f"📝 Server Logs (PID {pid}):\n\n"
            message += "=" * 60 + "\n"
            message += logs
            message += "\n" + "=" * 60
            
            return ToolResult(
                success=True,
                message=message,
                data={"pid": pid, "logs": logs, "lines": len(logs.split('\n'))}
            )
            
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return ToolResult(
                success=False,
                message=f"Error retrieving logs: {str(e)}",
                data={"pid": pid, "error": str(e)}
            )
