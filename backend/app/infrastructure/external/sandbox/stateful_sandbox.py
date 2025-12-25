# Stateful Sandbox Implementation for ai-manus
# Based on OpenHands SDK Architecture

"""
This module implements a StatefulSandbox that maintains session context
(environment variables, current working directory) between command executions,
similar to OpenHands SDK's runtime implementation.

Key Features:
1. Stateful shell sessions with persistent CWD and ENV
2. Background process support (detached &)
3. File editor integration from OpenHands
4. Skills/plugins system
"""

from typing import Dict, Any, Optional, List, BinaryIO, Tuple
import uuid
import httpx
import docker
import socket
import logging
import asyncio
import io
import json
from pathlib import Path
from async_lru import alru_cache
from app.core.config import get_settings
from app.domain.models.tool_result import ToolResult
from app.domain.external.sandbox import Sandbox
from app.infrastructure.external.browser.playwright_browser import PlaywrightBrowser
from app.domain.external.browser import Browser
from app.domain.external.llm import LLM

logger = logging.getLogger(__name__)


class StatefulSession:
    """Maintains state for a single shell session"""
    
    def __init__(self, session_id: str, initial_cwd: str = "/workspace"):
        self.session_id = session_id
        self.cwd = initial_cwd
        self.env_vars: Dict[str, str] = {}
        self.background_pids: Dict[str, int] = {}  # command -> PID mapping
        
    def update_cwd(self, new_cwd: str):
        """Update current working directory"""
        self.cwd = new_cwd
        
    def set_env(self, key: str, value: str):
        """Set environment variable"""
        self.env_vars[key] = value
        
    def get_env(self, key: str) -> Optional[str]:
        """Get environment variable"""
        return self.env_vars.get(key)
    
    def add_background_process(self, command: str, pid: int):
        """Track a background process"""
        self.background_pids[command] = pid
        
    def remove_background_process(self, command: str):
        """Remove tracked background process"""
        if command in self.background_pids:
            del self.background_pids[command]


class StatefulSandbox(Sandbox):
    """
    Stateful Docker Sandbox that maintains shell session context.
    
    This implementation follows OpenHands SDK patterns:
    - Persistent CWD between commands
    - Environment variable persistence
    - Background process management
    - Integrated file editor from OpenHands
    """
    
    def __init__(self, ip: str = None, container_name: str = None):
        """Initialize Stateful Docker sandbox"""
        self.client = httpx.AsyncClient(timeout=600)
        self.ip = ip
        self.base_url = f"http://{self.ip}:8080"
        self._vnc_url = f"ws://{self.ip}:5901"
        self._cdp_url = f"http://{self.ip}:9222"
        self._container_name = container_name
        
        # Session management
        self._sessions: Dict[str, StatefulSession] = {}
        self._default_session_id = "default"
        
        # Ens

ure default session exists
        self._get_or_create_session(self._default_session_id)
        
    def _get_or_create_session(self, session_id: str) -> StatefulSession:
        """Get existing session or create new one"""
        if session_id not in self._sessions:
            self._sessions[session_id] = StatefulSession(session_id)
            logger.info(f"Created new stateful session: {session_id}")
        return self._sessions[session_id]
    
    @property
    def id(self) -> str:
        """Sandbox ID"""
        if not self._container_name:
            return "dev-sandbox"
        return self._container_name
    
    @property
    def cdp_url(self) -> str:
        return self._cdp_url

    @property
    def vnc_url(self) -> str:
        return self._vnc_url

    @staticmethod
    def _get_container_ip(container) -> str:
        """Get container IP address from network settings"""
        network_settings = container.attrs['NetworkSettings']
        ip_address = network_settings['IPAddress']
        
        if not ip_address and 'Networks' in network_settings:
            networks = network_settings['Networks']
            for network_name, network_config in networks.items():
                if 'IPAddress' in network_config and network_config['IPAddress']:
                    ip_address = network_config['IPAddress']
                    break
        
        return ip_address

    @staticmethod
    def _create_task() -> 'StatefulSandbox':
        """Create a new Docker sandbox with plugins injection"""
        settings = get_settings()
        image = settings.sandbox_image
        name_prefix = settings.sandbox_name_prefix
        container_name = f"{name_prefix}-{str(uuid.uuid4())[:8]}"
        
        try:
            docker_client = docker.from_env()
            
            # Prepare plugins directory for volume mount
            plugins_dir = Path(__file__).parent / "plugins"
            plugins_dir_str = str(plugins_dir.absolute())
            
            container_config = {
                "image": image,
                "name": container_name,
                "detach": True,
                "remove": True,
                "environment": {
                    "SERVICE_TIMEOUT_MINUTES": settings.sandbox_ttl_minutes,
                    "CHROME_ARGS": settings.sandbox_chrome_args,
                    "PYTHONPATH": "/openhands/tools:$PYTHONPATH",  # Add tools to Python path
                },
                "volumes": {
                    plugins_dir_str: {
                        "bind": "/openhands/tools",
                        "mode": "ro"  # Read-only mount
                    }
                }
            }
            
            # Add proxy settings if configured
            if settings.https_proxy:
                container_config["environment"]["HTTPS_PROXY"] = settings.https_proxy
            if settings.http_proxy:
                container_config["environment"]["HTTP_PROXY"] = settings.http_proxy
            if settings.no_proxy:
                container_config["environment"]["NO_PROXY"] = settings.no_proxy
                
            # Add network if configured
            if settings.sandbox_network:
                container_config["network"] = settings.sandbox_network
            
            # Create container
            container = docker_client.containers.run(**container_config)
            
            # Get container IP
            container.reload()  # Refresh container info
            ip = StatefulSandbox._get_container_ip(container)
            
            if not ip:
                raise Exception(f"Could not get IP address for container {container_name}")
            
            logger.info(f"Created stateful sandbox container: {container_name} with IP: {ip}")
            logger.info(f"Plugins mounted at: /openhands/tools")
            
            return StatefulSandbox(ip=ip, container_name=container_name)
            
        except Exception as e:
            logger.error(f"Failed to create sandbox: {e}")
            raise

    async def exec_command_stateful(
        self, 
        command: str, 
        session_id: str = None,
        timeout: int = 120
    ) -> Dict[str, Any]:
        """
        Execute command with stateful context preservation.
        
        This method:
        1. Loads session CWD and ENV
        2. Wraps command to preserve state
        3. Extracts new CWD after execution
        4. Returns exit_code, stdout, stderr, and updated cwd
        
        Args:
            command: Shell command to execute
            session_id: Session identifier (default: "default")
            timeout: Command timeout in seconds
            
        Returns:
            Dict with keys: exit_code, stdout, stderr, cwd, background_pid (optional)
        """
        if session_id is None:
            session_id = self._default_session_id
            
        session = self._get_or_create_session(session_id)
        
        # Check if command should run in background
        is_background = command.strip().endswith('&')
        if is_background:
            command = command.strip()[:-1].strip()  # Remove trailing &
        
        # Build stateful command wrapper
        # 1. cd to session CWD
        # 2. Export session ENV vars
        # 3. Execute command
        # 4. Capture new CWD
        # 5. Return everything
        
        env_exports = " ".join([f"export {k}={v};" for k, v in session.env_vars.items()])
        
        if is_background:
            # For background processes, we need to capture PID
            wrapped_command = f"""
cd {session.cwd} || true
{env_exports}
nohup {command} > /tmp/bg_$$.out 2>&1 & echo $!
pwd
"""
        else:
            wrapped_command = f"""
cd {session.cwd} || true
{env_exports}
{command}
EXIT_CODE=$?
pwd
exit $EXIT_CODE
"""
        
        # Execute via sandbox API
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/shell/exec",
                json={
                    "id": session_id,
                    "exec_dir": session.cwd,
                    "command": wrapped_command
                },
                timeout=timeout
            )
            
            result = response.json()
            
            # Parse result
            exit_code = result.get("exit_code", -1)
            stdout = result.get("stdout", "")
            stderr = result.get("stderr", "")
            
            # Extract new CWD from last line of stdout
            if stdout:
                lines = stdout.strip().split('\n')
                if lines:
                    potential_cwd = lines[-1].strip()
                    # Check if it looks like a path
                    if potential_cwd.startswith('/'):
                        session.update_cwd(potential_cwd)
                        # Remove CWD from output
                        stdout = '\n'.join(lines[:-1])
            
            # Handle background process
            background_pid = None
            if is_background and stdout:
                lines = stdout.strip().split('\n')
                if lines and lines[0].isdigit():
                    background_pid = int(lines[0])
                    session.add_background_process(command, background_pid)
                    stdout = '\n'.join(lines[1:])  # Remove PID from output
            
            # Parse ENV changes from command output (if export was used)
            # This is a simplified version; OpenHands has more sophisticated parsing
            if 'export ' in command:
                # Extract export statements
                import re
                exports = re.findall(r'export\s+(\w+)=([^\s;]+)', command)
                for key, value in exports:
                    session.set_env(key, value.strip('"').strip("'"))
            
            result_dict = {
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "cwd": session.cwd,
                "session_id": session_id
            }
            
            if background_pid:
                result_dict["background_pid"] = background_pid
                
            return result_dict
            
        except Exception as e:
            logger.error(f"Stateful command execution failed: {e}")
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "cwd": session.cwd,
                "session_id": session_id
            }

    # Legacy compatibility methods
    async def exec_command(self, session_id: str, exec_dir: str, command: str) -> ToolResult:
        """Legacy method - redirects to stateful execution"""
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

    async def ensure_sandbox(self, max_retries: int = 30, retry_interval: float = 2.0) -> None:
        """
        Wait for sandbox services to start and inject plugins.
        
        Enhanced from original to support:
        - CDP health check
        - Plugins availability verification
        """
        for attempt in range(max_retries):
            try:
                # Check supervisor status
                response = await self.client.get(
                    f"{self.base_url}/api/v1/supervisor/status",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    services = data.get("services", {})
                    
                    non_running_services = [
                        name for name, status in services.items()
                        if status != "RUNNING"
                    ]
                    
                    if not non_running_services:
                        # All services running, check CDP
                        cdp_accessible = await self._check_cdp_health()
                        if cdp_accessible:
                            # Verify plugins are mounted
                            plugins_check = await self.exec_command_stateful(
                                "test -d /openhands/tools && echo 'OK' || echo 'MISSING'",
                                self._default_session_id
                            )
                            
                            if plugins_check.get("stdout", "").strip() == "OK":
                                logger.info("Sandbox ready with plugins mounted")
                                return
                            else:
                                logger.warning("Plugins directory not found, retrying...")
                        else:
                            logger.warning(f"CDP not accessible yet (attempt {attempt + 1}/{max_retries})")
                    else:
                        logger.info(f"Waiting for services: {', '.join(non_running_services)}")
                    
                    await asyncio.sleep(retry_interval)
                    
            except Exception as e:
                logger.warning(f"Sandbox check failed (attempt {attempt + 1}/{max_retries}): {e}")
                await asyncio.sleep(retry_interval)
        
        # CRITICAL: Raise exception to prevent continuation with broken sandbox
        error_message = f"Sandbox services failed to start after {max_retries} attempts"
        logger.error(error_message)
        raise Exception(error_message)

    async def _check_cdp_health(self) -> bool:
        """CDP health check"""
        try:
            response = await self.client.get(
                f"{self.cdp_url}/json/version",
                timeout=5.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if "Browser" in data and "Protocol-Version" in data:
                    logger.debug(f"CDP health check passed: {data.get('Browser')}")
                    return True
            
            return False
            
        except Exception as e:
            logger.debug(f"CDP health check failed: {e}")
            return False

    # Keep all other methods from original DockerSandbox
    # (file operations, browser, etc.)
    # ... [Continue with rest of implementation]
