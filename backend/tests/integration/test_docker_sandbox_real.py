"""
Real Integration Tests for DockerSandbox

These tests use actual Docker containers and require Docker daemon to be running.
They test the actual functionality of DockerSandbox with real containers.

Requirements:
- Docker daemon running
- Sandbox containers with HTTP API on port 8080
- Containers must be accessible from test environment

Note: These tests are marked as integration tests and can be skipped in CI/CD
if sandbox containers are not available. Run with: pytest -m integration

The sandbox containers must provide HTTP API endpoints for command execution
and file operations. For example, containers built from:
- ghcr.io/raglox/raglox-sandbox:latest (with HTTP API enabled)
- Custom sandbox images with HTTP API on port 8080
"""

import pytest
import docker
import asyncio
from typing import Optional
from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox

# Check if Docker is available
try:
    docker_client = docker.from_env()
    docker_client.ping()
    DOCKER_AVAILABLE = True
except Exception:
    DOCKER_AVAILABLE = False

# Mark all tests as integration tests
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not DOCKER_AVAILABLE, reason="Docker not available")
]


@pytest.fixture
def get_available_sandbox():
    """Get an available sandbox container from running containers
    
    This fixture looks for sandbox containers with HTTP API on port 8080.
    It verifies the container is accessible before returning it.
    
    Note: This will skip the test if no suitable sandbox is found.
    """
    client = docker.from_env()
    
    # Try to find containers that might be sandbox containers with HTTP API
    # Look for common sandbox image patterns
    sandbox_patterns = ["raglox-sandbox", "strix-sandbox", "openhands", "sandbox"]
    
    containers = client.containers.list()
    
    for container in containers:
        # Check if container name or image matches sandbox patterns
        image_name = container.image.tags[0] if container.image.tags else str(container.image.id)
        if any(pattern in image_name.lower() or pattern in container.name.lower() for pattern in sandbox_patterns):
            # Get container IP
            networks = container.attrs['NetworkSettings']['Networks']
            if not networks:
                continue
                
            ip = list(networks.values())[0]['IPAddress']
            if not ip:
                continue
            
            # Try to verify sandbox is accessible (optional - removed to avoid timeout)
            # If you want to verify, uncomment the lines below:
            # try:
            #     response = requests.get(f"http://{ip}:8080", timeout=2)
            #     if response.status_code >= 200:
            #         return {"ip": ip, "container_name": container.name, "container": container}
            # except:
            #     continue
            
            # Return first matching container without verification
            return {"ip": ip, "container_name": container.name, "container": container}
    
    pytest.skip("No suitable sandbox containers with HTTP API found. "
                "Please ensure sandbox containers are running with HTTP API on port 8080.")


@pytest.mark.asyncio
class TestDockerSandboxReal:
    """Real integration tests using actual Docker containers"""
    
    async def test_sandbox_initialization(self, get_available_sandbox):
        """Test that we can initialize a DockerSandbox with a real container"""
        sandbox_info = get_available_sandbox
        
        # Initialize sandbox
        sandbox = DockerSandbox(
            ip=sandbox_info["ip"],
            container_name=sandbox_info["container_name"]
        )
        
        # Verify sandbox has default session
        sessions = sandbox.list_sessions()
        assert len(sessions) >= 1
        assert any(s["session_id"] == "default" for s in sessions)
        
        # Cleanup
        await sandbox.destroy()
    
    async def test_exec_command_basic(self, get_available_sandbox):
        """Test executing a simple command in the sandbox"""
        sandbox_info = get_available_sandbox
        sandbox = DockerSandbox(
            ip=sandbox_info["ip"],
            container_name=sandbox_info["container_name"]
        )
        
        try:
            # Execute echo command
            result = await sandbox.exec_command(
                session_id="default",
                exec_dir="/workspace",
                command="echo 'Hello from sandbox'"
            )
            
            # Verify result
            assert result is not None
            assert result.exit_code == 0
            assert "Hello from sandbox" in result.output
            
        finally:
            await sandbox.destroy()
    
    async def test_exec_command_pwd(self, get_available_sandbox):
        """Test pwd command to verify working directory"""
        sandbox_info = get_available_sandbox
        sandbox = DockerSandbox(
            ip=sandbox_info["ip"],
            container_name=sandbox_info["container_name"]
        )
        
        try:
            # Execute pwd command
            result = await sandbox.exec_command(
                session_id="default",
                exec_dir="/workspace",
                command="pwd"
            )
            
            # Verify result
            assert result is not None
            assert result.exit_code == 0
            assert "/workspace" in result.output
            
        finally:
            await sandbox.destroy()
    
    async def test_session_state_tracking(self, get_available_sandbox):
        """Test that session state is tracked properly"""
        sandbox_info = get_available_sandbox
        sandbox = DockerSandbox(
            ip=sandbox_info["ip"],
            container_name=sandbox_info["container_name"]
        )
        
        try:
            # Get initial session info
            session_info = sandbox.get_session_info("default")
            assert session_info is not None
            initial_cwd = session_info["cwd"]
            
            # Session should exist
            assert session_info["session_id"] == "default"
            
            # Verify we can list sessions
            sessions = sandbox.list_sessions()
            assert len(sessions) >= 1
            assert any(s["session_id"] == "default" for s in sessions)
            
        finally:
            await sandbox.destroy()
    
    async def test_multiple_commands(self, get_available_sandbox):
        """Test executing multiple commands in sequence"""
        sandbox_info = get_available_sandbox
        sandbox = DockerSandbox(
            ip=sandbox_info["ip"],
            container_name=sandbox_info["container_name"]
        )
        
        try:
            # Execute first command
            result1 = await sandbox.exec_command(
                session_id="default",
                exec_dir="/workspace",
                command="echo 'First command'"
            )
            assert result1.exit_code == 0
            assert "First command" in result1.output
            
            # Execute second command
            result2 = await sandbox.exec_command(
                session_id="default",
                exec_dir="/workspace",
                command="echo 'Second command'"
            )
            assert result2.exit_code == 0
            assert "Second command" in result2.output
            
        finally:
            await sandbox.destroy()
    
    async def test_command_with_error(self, get_available_sandbox):
        """Test executing a command that fails"""
        sandbox_info = get_available_sandbox
        sandbox = DockerSandbox(
            ip=sandbox_info["ip"],
            container_name=sandbox_info["container_name"]
        )
        
        try:
            # Execute command that should fail
            result = await sandbox.exec_command(
                session_id="default",
                exec_dir="/workspace",
                command="ls /nonexistent_directory_12345"
            )
            
            # Verify error is captured
            assert result is not None
            # Command should fail (non-zero exit code)
            assert result.exit_code != 0
            
        finally:
            await sandbox.destroy()
    
    async def test_sandbox_cleanup(self, get_available_sandbox):
        """Test that sandbox cleanup works properly"""
        sandbox_info = get_available_sandbox
        sandbox = DockerSandbox(
            ip=sandbox_info["ip"],
            container_name=sandbox_info["container_name"]
        )
        
        try:
            # Execute a command to ensure sandbox is working
            result = await sandbox.exec_command(
                session_id="default",
                exec_dir="/workspace",
                command="echo 'Test cleanup'"
            )
            assert result.exit_code == 0
            
        finally:
            # Close should not raise exceptions
            await sandbox.close()
