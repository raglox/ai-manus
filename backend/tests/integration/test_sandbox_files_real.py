"""
Real Integration Tests for Sandbox File Operations

These tests use actual Docker containers and require Docker daemon to be running.
They test file upload/download functionality with real sandbox containers.

Requirements:
- Docker daemon running
- raglox-sandbox containers available
"""

import pytest
import docker
import asyncio
import os
from io import BytesIO
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


@pytest.fixture
def sample_file_content():
    """Sample file content for testing"""
    return b"This is a test file content for sandbox file operations testing."


@pytest.fixture
def temp_file_path():
    """Generate a unique temporary file path"""
    unique_id = os.urandom(8).hex()
    return f"/workspace/test_file_{unique_id}.txt"


@pytest.mark.asyncio
class TestSandboxFilesReal:
    """Real integration tests for sandbox file operations"""
    
    async def test_file_upload_success(self, get_available_sandbox, sample_file_content, temp_file_path):
        """Test uploading a file to the sandbox"""
        sandbox_info = get_available_sandbox
        sandbox = DockerSandbox(
            ip=sandbox_info["ip"],
            container_name=sandbox_info["container_name"]
        )
        
        try:
            # Create BytesIO stream from content
            file_stream = BytesIO(sample_file_content)
            
            # Upload file
            result = await sandbox.upload_file(
                file_path=temp_file_path,
                file_content=file_stream,
                filename="test_file.txt"
            )
            
            # Verify upload was successful
            assert result is not None
            assert result.get("success") == True or result.get("status") == "success"
            
            # Verify file exists by reading it back
            verify_result = await sandbox.exec_command(
                session_id="default",
                exec_dir="/workspace",
                command=f"test -f {temp_file_path} && echo 'EXISTS' || echo 'NOT_FOUND'"
            )
            
            assert "EXISTS" in verify_result.output
            
        finally:
            # Cleanup: remove test file
            await sandbox.exec_command(
                session_id="default",
                exec_dir="/workspace",
                command=f"rm -f {temp_file_path}"
            )
            await sandbox.destroy()
    
    async def test_file_download_success(self, get_available_sandbox, sample_file_content, temp_file_path):
        """Test downloading a file from the sandbox"""
        sandbox_info = get_available_sandbox
        sandbox = DockerSandbox(
            ip=sandbox_info["ip"],
            container_name=sandbox_info["container_name"]
        )
        
        try:
            # First, upload a file
            file_stream = BytesIO(sample_file_content)
            upload_result = await sandbox.upload_file(
                file_path=temp_file_path,
                file_content=file_stream,
                filename="test_download.txt"
            )
            assert upload_result.get("success") == True or upload_result.get("status") == "success"
            
            # Now download the file
            download_result = await sandbox.download_file(file_path=temp_file_path)
            
            # Verify download result
            assert download_result is not None
            
            # Check if we got file content back (could be bytes or dict with content)
            if isinstance(download_result, bytes):
                assert len(download_result) > 0
            elif isinstance(download_result, dict):
                assert "content" in download_result or "data" in download_result
            
        finally:
            # Cleanup: remove test file
            await sandbox.exec_command(
                session_id="default",
                exec_dir="/workspace",
                command=f"rm -f {temp_file_path}"
            )
            await sandbox.destroy()
    
    async def test_file_upload_and_verify_content(self, get_available_sandbox, sample_file_content, temp_file_path):
        """Test uploading a file and verifying its content"""
        sandbox_info = get_available_sandbox
        sandbox = DockerSandbox(
            ip=sandbox_info["ip"],
            container_name=sandbox_info["container_name"]
        )
        
        try:
            # Upload file
            file_stream = BytesIO(sample_file_content)
            upload_result = await sandbox.upload_file(
                file_path=temp_file_path,
                file_content=file_stream,
                filename="test_content.txt"
            )
            assert upload_result.get("success") == True or upload_result.get("status") == "success"
            
            # Read file content back using cat command
            cat_result = await sandbox.exec_command(
                session_id="default",
                exec_dir="/workspace",
                command=f"cat {temp_file_path}"
            )
            
            # Verify content matches
            assert cat_result.exit_code == 0
            assert sample_file_content.decode() in cat_result.output
            
        finally:
            # Cleanup
            await sandbox.exec_command(
                session_id="default",
                exec_dir="/workspace",
                command=f"rm -f {temp_file_path}"
            )
            await sandbox.destroy()
    
    async def test_file_operations_multiple_files(self, get_available_sandbox, sample_file_content):
        """Test uploading multiple files"""
        sandbox_info = get_available_sandbox
        sandbox = DockerSandbox(
            ip=sandbox_info["ip"],
            container_name=sandbox_info["container_name"]
        )
        
        try:
            # Generate multiple unique paths
            paths = [f"/workspace/test_multi_{i}_{os.urandom(4).hex()}.txt" for i in range(3)]
            
            # Upload multiple files
            for i, path in enumerate(paths):
                content = f"File {i}: {sample_file_content.decode()}".encode()
                file_stream = BytesIO(content)
                result = await sandbox.upload_file(
                    file_path=path,
                    file_content=file_stream,
                    filename=f"multi_file_{i}.txt"
                )
                assert result.get("success") == True or result.get("status") == "success"
            
            # Verify all files exist
            for path in paths:
                verify_result = await sandbox.exec_command(
                    session_id="default",
                    exec_dir="/workspace",
                    command=f"test -f {path} && echo 'EXISTS' || echo 'NOT_FOUND'"
                )
                assert "EXISTS" in verify_result.output
            
        finally:
            # Cleanup all test files
            for path in paths:
                await sandbox.exec_command(
                    session_id="default",
                    exec_dir="/workspace",
                    command=f"rm -f {path}"
                )
            await sandbox.destroy()
    
    async def test_file_upload_large_content(self, get_available_sandbox):
        """Test uploading a larger file"""
        sandbox_info = get_available_sandbox
        sandbox = DockerSandbox(
            ip=sandbox_info["ip"],
            container_name=sandbox_info["container_name"]
        )
        
        # Create a larger file (10KB)
        large_content = b"A" * 10240
        temp_path = f"/workspace/large_file_{os.urandom(4).hex()}.txt"
        
        try:
            # Upload large file
            file_stream = BytesIO(large_content)
            result = await sandbox.upload_file(
                file_path=temp_path,
                file_content=file_stream,
                filename="large_file.txt"
            )
            assert result.get("success") == True or result.get("status") == "success"
            
            # Verify file size
            size_result = await sandbox.exec_command(
                session_id="default",
                exec_dir="/workspace",
                command=f"wc -c < {temp_path}"
            )
            
            # Check file size (should be 10240 bytes)
            assert size_result.exit_code == 0
            assert "10240" in size_result.output
            
        finally:
            # Cleanup
            await sandbox.exec_command(
                session_id="default",
                exec_dir="/workspace",
                command=f"rm -f {temp_path}"
            )
            await sandbox.destroy()
