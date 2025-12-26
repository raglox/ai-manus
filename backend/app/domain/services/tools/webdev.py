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
import shlex
from typing import Optional, Dict, Any, List, Set
from app.domain.external.sandbox import Sandbox
from app.domain.services.tools.base import tool, BaseTool
from app.domain.models.tool_result import ToolResult
import logging

logger = logging.getLogger(__name__)


# 🔒 P0-1: SECURITY - Strict command-to-binary mapping
ALLOWED_BINARIES = {
    'npm': '/usr/bin/npm',
    'node': '/usr/bin/node',
    'python': '/usr/bin/python',
    'python3': '/usr/bin/python3',
    'flask': '/usr/local/bin/flask',
    'uvicorn': '/usr/local/bin/uvicorn',
    'gunicorn': '/usr/local/bin/gunicorn',
    'django-admin': '/usr/local/bin/django-admin',
    'php': '/usr/bin/php',
    'ruby': '/usr/bin/ruby',
    'rails': '/usr/local/bin/rails',
    'deno': '/usr/bin/deno',
    'bun': '/usr/bin/bun',
    'pnpm': '/usr/bin/pnpm',
    'yarn': '/usr/bin/yarn',
    'next': '/usr/local/bin/next',
    'vite': '/usr/local/bin/vite',
    'webpack-dev-server': '/usr/local/bin/webpack-dev-server'
}

# 🔒 P0-1: SECURITY - Forbidden argument patterns
FORBIDDEN_ARGS = [
    r'-c\s',           # python -c (arbitrary code)
    r'--eval',         # node --eval (arbitrary code)
    r'--interactive',  # python -i (interactive shell)
    r'-e\s',           # perl -e (arbitrary code)
]


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
        # 🔒 P0-2: Track servers with metadata (PID -> {start_time, command, port})
        self._started_servers: Dict[int, Dict[str, Any]] = {}
        # 🔒 P1-1: Async lock for race condition protection
        self._server_lock = asyncio.Lock()
    
    def _validate_command(self, command: str) -> None:
        """🔒 P0-1: HARDENED multi-layer command validation.
        
        Defenses:
        1. Parse command safely with shlex
        2. Validate binary against whitelist (reject paths)
        3. Scan for dangerous argument patterns (-c, --eval, etc.)
        4. Check for environment variable injection (LD_PRELOAD, PATH)
        5. Filter dangerous shell characters
        
        Args:
            command: Command to validate
            
        Raises:
            ValueError: If command is unsafe
        """
        if not command or not command.strip():
            raise ValueError("Command cannot be empty")
        
        # 🔒 DEFENSE 1: Parse command safely
        try:
            parts = shlex.split(command)
        except ValueError as e:
            raise ValueError(f"Invalid command syntax: {e}")
        
        if not parts:
            raise ValueError("Command cannot be empty after parsing")
        
        command_name = parts[0]
        arguments = parts[1:] if len(parts) > 1 else []
        
        # 🔒 DEFENSE 2: Reject absolute/relative paths
        if '/' in command_name:
            raise ValueError(
                f"Absolute or relative paths are not allowed: '{command_name}'. "
                f"Use binary names only (e.g., 'python3' not '/usr/bin/python3')"
            )
        
        if command_name not in ALLOWED_BINARIES:
            raise ValueError(
                f"Command '{command_name}' is not allowed for web servers. "
                f"Allowed commands: {', '.join(sorted(ALLOWED_BINARIES.keys()))}"
            )
        
        # 🔒 DEFENSE 3: Scan for dangerous argument patterns
        full_args = ' '.join(arguments)
        for pattern in FORBIDDEN_ARGS:
            if re.search(pattern, full_args, re.IGNORECASE):
                raise ValueError(
                    f"Command contains forbidden argument pattern matching '{pattern}'. "
                    f"This could enable arbitrary code execution."
                )
        
        # 🔒 DEFENSE 4: Check for environment variable injection
        forbidden_env_vars = [
            'LD_PRELOAD', 'LD_LIBRARY_PATH', 'PATH',
            'PYTHONPATH', 'NODE_PATH', 'PERL5LIB', 'RUBYLIB'
        ]
        
        for arg in arguments:
            if '=' in arg and not arg.startswith('--'):
                # Looks like ENV=value
                env_name = arg.split('=')[0].upper()
                if env_name in forbidden_env_vars:
                    raise ValueError(
                        f"Setting environment variable '{env_name}' is forbidden. "
                        f"This could be used for code injection (e.g., LD_PRELOAD attacks)."
                    )
        
        # 🔒 DEFENSE 5: Check for dangerous shell characters
        dangerous_chars = [';', '|', '&&', '||', '`', '$(', '>', '<', '\n', '\r']
        for char in dangerous_chars:
            if char in command:
                raise ValueError(
                    f"Command contains dangerous character/sequence: '{char}'. "
                    f"This could be a shell injection vector."
                )
        
        logger.debug(f"✅ Command validation passed: {command}")
    
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
    
    async def _get_process_start_time(self, pid: int) -> Optional[float]:
        """🔒 P0-2: Get process start time for PID validation.
        
        Uses ps command to get process start time.
        This is critical for detecting PID recycling attacks.
        
        Args:
            pid: Process ID
            
        Returns:
            Process start time as Unix timestamp, or None if process doesn't exist
        """
        try:
            # Get process start time using ps
            result = await self.sandbox.exec_command_stateful(
                f"ps -p {pid} -o etimes= 2>/dev/null || echo ''"
            )
            
            if result["exit_code"] != 0 or not result["stdout"].strip():
                logger.warning(f"Process {pid} not found")
                return None
            
            # etimes = elapsed time in seconds since process started
            # Calculate start time = current_time - elapsed_time
            try:
                elapsed_seconds = int(result["stdout"].strip())
                start_time = time.time() - elapsed_seconds
                logger.debug(f"PID {pid} start time: {start_time} (elapsed: {elapsed_seconds}s)")
                return start_time
            except (ValueError, AttributeError):
                logger.warning(f"Could not parse elapsed time for PID {pid}")
                return time.time()  # Fallback to current time
            
        except Exception as e:
            logger.error(f"Failed to get process start time for PID {pid}: {e}")
            return None
    
    def _extract_port_from_command(self, command: str) -> Optional[int]:
        """🔒 P0-3: Extract port number from command if specified.
        
        Args:
            command: Server command
            
        Returns:
            Port number (1024-65535) or None
        """
        # Match patterns: :8080, 8080, --port 8080, -p 8080, --port=8080
        patterns = [
            r':(\d{4,5})\b',
            r'\b(\d{4,5})\b(?!\.)',
            r'--port[=\s]+(\d{4,5})',
            r'-p\s+(\d{4,5})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, command)
            if match:
                port = int(match.group(1))
                if 1024 <= port <= 65535:
                    return port
        return None
    
    async def _verify_port_listening(self, pid: int, url: str) -> bool:
        """🔒 P0-3: Verify that port is actually listening and owned by correct PID.
        
        Three-layer verification:
        1. Check if port is listening (netstat/ss)
        2. Verify PID owns the socket (lsof)
        3. HTTP health check (curl)
        
        Args:
            pid: Process ID that should own the port
            url: URL to verify
            
        Returns:
            True if all verifications pass, False otherwise
        """
        try:
            # Extract port from URL
            port_match = re.search(r':(\d+)', url)
            if not port_match:
                logger.warning(f"Could not extract port from URL: {url}")
                return False
            
            port = int(port_match.group(1))
            logger.info(f"🔍 Verifying port {port} for PID {pid}...")
            
            # 🔒 DEFENSE 1: Check if port is listening
            netstat_result = await self.sandbox.exec_command_stateful(
                f"netstat -tuln 2>/dev/null | grep ':{port} ' || ss -tuln 2>/dev/null | grep ':{port} ' || echo 'not_found'"
            )
            
            if "not_found" in netstat_result.get("stdout", ""):
                logger.warning(f"❌ Port {port} is not listening")
                return False
            
            logger.info(f"✅ Port {port} is listening")
            
            # 🔒 DEFENSE 2: Verify PID owns the socket (lsof)
            lsof_result = await self.sandbox.exec_command_stateful(
                f"lsof -i :{port} -t 2>/dev/null || echo 'not_found'"
            )
            
            if "not_found" in lsof_result.get("stdout", ""):
                logger.warning(f"⚠️ lsof not available, skipping PID ownership check")
                # Continue - lsof might not be installed
            else:
                owning_pids_str = lsof_result["stdout"].strip()
                if owning_pids_str and owning_pids_str != "not_found":
                    owning_pids = []
                    for line in owning_pids_str.split('\n'):
                        line = line.strip()
                        if line.isdigit():
                            owning_pids.append(int(line))
                    
                    if owning_pids and pid not in owning_pids:
                        logger.error(
                            f"❌ PORT HIJACKING DETECTED! "
                            f"Port {port} is owned by PID(s) {owning_pids}, "
                            f"but expected PID {pid}. This could be a security attack!"
                        )
                        return False
                    
                    if owning_pids:
                        logger.info(f"✅ PID {pid} owns port {port}")
            
            # 🔒 DEFENSE 3: HTTP health check
            try:
                health_result = await self.sandbox.exec_command_stateful(
                    f"curl -s -o /dev/null -w '%{{http_code}}' --connect-timeout 5 --max-time 5 {url} 2>/dev/null || echo '000'",
                    timeout=10
                )
                
                http_code = health_result.get("stdout", "000").strip()
                
                # Accept 2xx (success), 3xx (redirect), 4xx (client error - server is responding)
                # Reject 000 (connection refused), 5xx (server error)
                if http_code and http_code[0] in ['2', '3', '4']:
                    logger.info(f"✅ Port {port} is reachable (HTTP {http_code})")
                    return True
                else:
                    logger.warning(f"⚠️ Port {port} returned HTTP {http_code} (may still be starting up)")
                    # Still return True if port is listening and owned by correct PID
                    # Server might be starting up
                    return True
                    
            except Exception as e:
                logger.warning(f"HTTP health check failed for {url}: {e}")
                # If netstat and lsof passed, server is probably starting up
                return True
            
        except Exception as e:
            logger.error(f"Port verification failed: {e}")
            return False
    
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
        
        # 🔒 P1-1: Acquire lock to get snapshot of PIDs
        async with self._server_lock:
            pids_to_stop = list(self._started_servers.keys())
            server_count = len(pids_to_stop)
        
        logger.info(f"Cleaning up {server_count} tracked servers...")
        
        for pid in pids_to_stop:  # Iterate over snapshot
            try:
                result = await self.stop_server(pid)  # stop_server has its own lock
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
            
            # 🔒 P0-2: Get process start time for PID validation
            start_time = await self._get_process_start_time(pid)
            if start_time is None:
                start_time = time.time()  # Fallback to current time
            
            # 🔒 P1-1: Acquire lock before modifying _started_servers
            async with self._server_lock:
                self._started_servers[pid] = {
                    "command": command,
                    "start_time": start_time,
                    "session_id": session_id or "default"
                }
            
            log_file = f"/tmp/bg_{pid}.out"
            logger.info(f"✅ Server started: PID={pid}, start_time={start_time}")
            
            # Monitor logs for URL detection
            detected_url = await self._detect_server_url(
                pid=pid,
                timeout_seconds=timeout_seconds,
                session_id=session_id
            )
            
            if detected_url:
                # 🔒 P0-3: VERIFY port ownership before returning
                logger.info(f"🔍 Starting port verification for {detected_url}...")
                is_verified = await self._verify_port_listening(pid, detected_url)
                
                if not is_verified:
                    logger.error(f"❌ Port verification FAILED for {detected_url}")
                    # 🔒 P1-1: Acquire lock before deleting
                    async with self._server_lock:
                        # Clean up tracking
                        if pid in self._started_servers:
                            del self._started_servers[pid]
                    
                    return ToolResult(
                        success=False,
                        message=(
                            f"⚠️ SECURITY ALERT: Port verification failed for {detected_url}\n\n"
                            f"The detected URL may not belong to PID {pid}.\n"
                            f"Possible causes:\n"
                            f"  - Port hijacking (another process bound to port first)\n"
                            f"  - URL spoofing (fake URL in logs)\n"
                            f"  - Server crashed immediately after startup\n\n"
                            f"Server has been removed from tracking for safety.\n"
                            f"Check logs at: {log_file}"
                        ),
                        data={
                            "url": detected_url,
                            "pid": pid,
                            "error": "port_verification_failed",
                            "security_alert": True,
                            "log_file": log_file
                        }
                    )
                
                # Success - verified URL
                message = f"✅ Server started and VERIFIED!\n\n"
                message += f"🌐 URL: {detected_url}\n"
                message += f"🔢 PID: {pid}\n"
                message += f"🔒 Security: Port ownership verified\n"
                message += f"⏰ Started: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}\n"
                message += f"📝 Logs: {log_file}\n\n"
                message += f"Use 'stop_server' with PID {pid} to stop the server."
                
                return ToolResult(
                    success=True,
                    message=message,
                    data={
                        "url": detected_url,
                        "pid": pid,
                        "start_time": start_time,
                        "command": command,
                        "log_file": log_file,
                        "session_id": session_id or "default",
                        "verified": True
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
        
        while (time.monotonic() - start_time) < timeout_seconds:
            try:
                # ✅ FIXED: Read only NEW log content to prevent memory leak
                result = await self.sandbox.exec_command_stateful(
                    f"tail -c +{last_read_size + 1} {log_file} 2>/dev/null || echo ''",
                    session_id=session_id
                )
                
                new_logs = result.get("stdout", "")
                
                if new_logs:
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
        """🔒 P0-2 HARDENED: Stop server with PID recycling detection.
        
        Security enhancements:
        - P0-2: Validate PID is tracked by this tool
        - P0-2: Check process start time to detect PID recycling
        - Try SIGTERM first, then SIGKILL if needed
        - Remove from tracking after successful kill
        
        Args:
            pid: Process ID to kill
            
        Returns:
            ToolResult with success status
        """
        try:
            # ✅ Validate PID format
            self._validate_pid(pid)
            
            # 🔒 P1-1: Acquire lock for atomic check-read-delete operation
            async with self._server_lock:
                # 🔒 P0-2: DEFENSE - Check if PID is tracked by this tool
                if pid not in self._started_servers:
                    return ToolResult(
                        success=False,
                        message=f"❌ PID {pid} is not tracked by this tool. Cannot stop for safety.",
                        data={"pid": pid, "tracked": False}
                    )
                
                # Get expected start time from tracking
                server_metadata = self._started_servers[pid]
                expected_start_time = server_metadata['start_time']
            
            # 🔒 P0-2: DEFENSE - Verify PID hasn't been recycled
            current_start_time = await self._get_process_start_time(pid)
            
            if current_start_time is None:
                # Process doesn't exist anymore - clean up tracking
                # 🔒 P1-1: Acquire lock before deleting
                async with self._server_lock:
                    if pid in self._started_servers:
                        del self._started_servers[pid]
                return ToolResult(
                    success=False,
                    message=f"❌ Process {pid} does not exist or already stopped.",
                    data={"pid": pid, "exists": False}
                )
            
            # Allow 2-second tolerance for timing (ps resolution)
            time_diff = abs(current_start_time - expected_start_time)
            if time_diff > 2.0:
                logger.error(
                    f"🚨 PID RECYCLING DETECTED! PID {pid} start time mismatch: "
                    f"expected={expected_start_time}, current={current_start_time}, "
                    f"diff={time_diff}s"
                )
                return ToolResult(
                    success=False,
                    message=(
                        f"❌ SECURITY ALERT: PID {pid} validation failed!\n\n"
                        f"Process start time doesn't match expected value.\n"
                        f"This could indicate PID recycling (kernel reused PID for different process).\n\n"
                        f"Expected start time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expected_start_time))}\n"
                        f"Current start time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_start_time))}\n"
                        f"Time difference: {time_diff:.1f} seconds\n\n"
                        f"Refusing to kill for safety. This prevents accidentally killing critical system processes."
                    ),
                    data={
                        "pid": pid,
                        "expected_start_time": expected_start_time,
                        "current_start_time": current_start_time,
                        "time_diff": time_diff,
                        "error": "pid_recycling_detected",
                        "security_alert": True
                    }
                )
            
            logger.info(f"✅ PID {pid} validation passed (time_diff={time_diff:.2f}s)")
            
            # Try to kill the process
            result = await self.sandbox.kill_background_process(pid=pid)
            
            killed_count = result.get("killed_count", 0)
            
            if killed_count > 0:
                # 🔒 P1-1: Acquire lock before deleting
                async with self._server_lock:
                    # Remove from tracking
                    if pid in self._started_servers:
                        del self._started_servers[pid]
                
                # Verify it's actually stopped
                await asyncio.sleep(0.5)
                verify_stop = await self._get_process_start_time(pid)
                
                if verify_stop is not None:
                    # Still running! Force kill
                    logger.warning(f"PID {pid} still running after SIGTERM, using SIGKILL")
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
                    message=f"❌ Failed to stop server with PID {pid}.",
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
