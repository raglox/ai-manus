"""
Real Integration Tests for DockerSandbox

These tests use actual Docker containers and require Docker daemon to be running.
They test the actual functionality of DockerSandbox with real containers.

Requirements:
- Docker daemon running
- raglox-sandbox containers available
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

# Skip all tests if Docker is not available
pytestmark = pytest.mark.skipif(not DOCKER_AVAILABLE, reason="Docker not available")


@pytest.fixture
def get_available_sandbox():
    """Get an available sandbox container from running containers"""
    client = docker.from_env()
    containers = client.containers.list(filters={"name": "raglox"})
    
    if not containers:
        pytest.skip("No raglox sandbox containers available")
    
    # Get first available container
    container = containers[0]
    container_name = container.name
    
    # Get container IP
    networks = container.attrs['NetworkSettings']['Networks']
    ip = list(networks.values())[0]['IPAddress']
    
    if not ip:
        pytest.skip(f"Container {container_name} has no IP address")
    
    return {"ip": ip, "container_name": container_name, "container": container}


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
