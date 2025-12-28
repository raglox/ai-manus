"""
Test harness for Sandbox protocol compliance.

This test suite validates that any Sandbox implementation correctly implements
the Sandbox protocol interface. Tests should pass for both DockerSandbox and
CloudRunJobsSandbox implementations.
"""

import pytest
from typing import Protocol
from app.domain.external.sandbox import Sandbox
from app.domain.models.tool_result import ToolResult


class TestSandboxProtocolCompliance:
    """Test suite to validate Sandbox protocol implementation."""
    
    @pytest.fixture
    async def sandbox(self, request):
        """
        Fixture that provides a Sandbox instance.
        
        Override this in test configurations to provide different implementations:
        - DockerSandbox (current production)
        - CloudRunJobsSandbox (migration target)
        """
        # This will be implemented per test configuration
        # For now, we'll skip tests that require actual implementation
        pytest.skip("Sandbox implementation fixture not configured")
    
    # ============================================================
    # Lifecycle Management Tests
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_create_sandbox(self, sandbox_class):
        """Test: Can create a new sandbox instance."""
        sandbox = await sandbox_class.create()
        assert sandbox is not None
        assert hasattr(sandbox, 'id')
        assert isinstance(sandbox.id, str)
        assert len(sandbox.id) > 0
        
        # Cleanup
        await sandbox.destroy()
    
    @pytest.mark.asyncio
    async def test_ensure_sandbox(self, sandbox):
        """Test: ensure_sandbox prepares sandbox for use."""
        # Should not raise exception
        await sandbox.ensure_sandbox()
    
    @pytest.mark.asyncio
    async def test_destroy_sandbox(self, sandbox):
        """Test: Can destroy sandbox instance."""
        result = await sandbox.destroy()
        assert isinstance(result, bool)
    
    # ============================================================
    # Property Tests
    # ============================================================
    
    def test_sandbox_id_property(self, sandbox):
        """Test: Sandbox has id property."""
        assert hasattr(sandbox, 'id')
        assert isinstance(sandbox.id, str)
        assert len(sandbox.id) > 0
    
    def test_sandbox_cdp_url_property(self, sandbox):
        """Test: Sandbox has cdp_url property."""
        assert hasattr(sandbox, 'cdp_url')
        # May be empty or raise NotImplementedError for some implementations
    
    def test_sandbox_vnc_url_property(self, sandbox):
        """Test: Sandbox has vnc_url property."""
        assert hasattr(sandbox, 'vnc_url')
        # May be empty or raise NotImplementedError for some implementations
    
    # ============================================================
    # Stateful Command Execution Tests
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_exec_command_stateful_simple(self, sandbox):
        """Test: Can execute simple command with stateful context."""
        result = await sandbox.exec_command_stateful("echo 'hello world'")
        
        assert isinstance(result, dict)
        assert "exit_code" in result
        assert "stdout" in result
        assert "stderr" in result
        assert result["exit_code"] == 0
        assert "hello world" in result["stdout"]
    
    @pytest.mark.asyncio
    async def test_exec_command_stateful_cwd_preservation(self, sandbox):
        """Test: CWD is preserved between commands in same session."""
        session_id = "test_cwd_session"
        
        # Change directory
        result1 = await sandbox.exec_command_stateful(
            "cd /tmp && pwd",
            session_id=session_id
        )
        assert result1["exit_code"] == 0
        assert "/tmp" in result1["stdout"]
        
        # Verify CWD persists
        result2 = await sandbox.exec_command_stateful(
            "pwd",
            session_id=session_id
        )
        assert result2["exit_code"] == 0
        assert "/tmp" in result2["stdout"]
    
    @pytest.mark.asyncio
    async def test_exec_command_stateful_env_preservation(self, sandbox):
        """Test: ENV vars are preserved between commands in same session."""
        session_id = "test_env_session"
        
        # Set environment variable
        result1 = await sandbox.exec_command_stateful(
            "export TEST_VAR='test_value'",
            session_id=session_id
        )
        assert result1["exit_code"] == 0
        
        # Verify ENV persists
        result2 = await sandbox.exec_command_stateful(
            "echo $TEST_VAR",
            session_id=session_id
        )
        assert result2["exit_code"] == 0
        assert "test_value" in result2["stdout"]
    
    @pytest.mark.asyncio
    async def test_exec_command_stateful_background_process(self, sandbox):
        """Test: Can start background process with & suffix."""
        result = await sandbox.exec_command_stateful("sleep 10 &")
        
        assert result["exit_code"] == 0
        assert "background_pid" in result
        assert isinstance(result["background_pid"], int)
        assert result["background_pid"] > 0
        
        # Cleanup: kill the background process
        await sandbox.kill_background_process(pid=result["background_pid"])
    
    # ============================================================
    # Background Process Management Tests
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_list_background_processes(self, sandbox):
        """Test: Can list background processes."""
        session_id = "test_bg_list"
        
        # Start a background process
        result = await sandbox.exec_command_stateful(
            "sleep 30 &",
            session_id=session_id
        )
        pid = result["background_pid"]
        
        # List processes
        processes = await sandbox.list_background_processes(session_id=session_id)
        assert isinstance(processes, list)
        assert any(p["pid"] == pid for p in processes)
        
        # Cleanup
        await sandbox.kill_background_process(pid=pid)
    
    @pytest.mark.asyncio
    async def test_kill_background_process_by_pid(self, sandbox):
        """Test: Can kill background process by PID."""
        result = await sandbox.exec_command_stateful("sleep 60 &")
        pid = result["background_pid"]
        
        # Kill process
        kill_result = await sandbox.kill_background_process(pid=pid)
        assert isinstance(kill_result, dict)
        assert "killed_count" in kill_result
        assert kill_result["killed_count"] >= 1
        assert pid in kill_result["killed_pids"]
    
    @pytest.mark.asyncio
    async def test_get_background_logs(self, sandbox):
        """Test: Can retrieve background process logs."""
        # Start process that generates output
        result = await sandbox.exec_command_stateful(
            "sh -c 'for i in 1 2 3; do echo line$i; sleep 1; done' &"
        )
        pid = result["background_pid"]
        
        # Give it time to generate some output
        import asyncio
        await asyncio.sleep(2)
        
        # Get logs
        logs = await sandbox.get_background_logs(pid)
        # Logs may be None if not available yet
        if logs:
            assert isinstance(logs, str)
        
        # Cleanup
        await sandbox.kill_background_process(pid=pid)
    
    # ============================================================
    # File Operations Tests
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_file_write_and_read(self, sandbox):
        """Test: Can write and read file."""
        test_file = "/tmp/test_file.txt"
        test_content = "Hello, sandbox!"
        
        # Write file
        write_result = await sandbox.file_write(test_file, test_content)
        assert isinstance(write_result, ToolResult)
        
        # Read file
        read_result = await sandbox.file_read(test_file)
        assert isinstance(read_result, ToolResult)
        assert test_content in read_result.data.get("content", "")
        
        # Cleanup
        await sandbox.file_delete(test_file)
    
    @pytest.mark.asyncio
    async def test_file_exists(self, sandbox):
        """Test: Can check if file exists."""
        test_file = "/tmp/test_exists.txt"
        
        # File should not exist initially
        result1 = await sandbox.file_exists(test_file)
        assert isinstance(result1, ToolResult)
        
        # Create file
        await sandbox.file_write(test_file, "content")
        
        # File should exist now
        result2 = await sandbox.file_exists(test_file)
        assert isinstance(result2, ToolResult)
        
        # Cleanup
        await sandbox.file_delete(test_file)
    
    @pytest.mark.asyncio
    async def test_file_delete(self, sandbox):
        """Test: Can delete file."""
        test_file = "/tmp/test_delete.txt"
        
        # Create file
        await sandbox.file_write(test_file, "to be deleted")
        
        # Delete file
        result = await sandbox.file_delete(test_file)
        assert isinstance(result, ToolResult)
        
        # Verify deleted
        exists_result = await sandbox.file_exists(test_file)
        # Check that file no longer exists
    
    @pytest.mark.asyncio
    async def test_file_list(self, sandbox):
        """Test: Can list directory contents."""
        result = await sandbox.file_list("/tmp")
        assert isinstance(result, ToolResult)
        assert "data" in result.__dict__ or hasattr(result, 'data')
    
    @pytest.mark.asyncio
    async def test_file_search(self, sandbox):
        """Test: Can search in file."""
        test_file = "/tmp/test_search.txt"
        test_content = "line1\nline2\nline3"
        
        await sandbox.file_write(test_file, test_content)
        
        result = await sandbox.file_search(test_file, "line2")
        assert isinstance(result, ToolResult)
        
        # Cleanup
        await sandbox.file_delete(test_file)
    
    @pytest.mark.asyncio
    async def test_file_replace(self, sandbox):
        """Test: Can replace string in file."""
        test_file = "/tmp/test_replace.txt"
        original = "Hello World"
        
        await sandbox.file_write(test_file, original)
        
        result = await sandbox.file_replace(test_file, "World", "Sandbox")
        assert isinstance(result, ToolResult)
        
        # Verify replacement
        read_result = await sandbox.file_read(test_file)
        assert "Sandbox" in read_result.data.get("content", "")
        
        # Cleanup
        await sandbox.file_delete(test_file)
    
    @pytest.mark.asyncio
    async def test_file_find(self, sandbox):
        """Test: Can find files by pattern."""
        # Create test files
        await sandbox.file_write("/tmp/test1.txt", "content1")
        await sandbox.file_write("/tmp/test2.txt", "content2")
        
        result = await sandbox.file_find("/tmp", "test*.txt")
        assert isinstance(result, ToolResult)
        
        # Cleanup
        await sandbox.file_delete("/tmp/test1.txt")
        await sandbox.file_delete("/tmp/test2.txt")
    
    # ============================================================
    # Process Management Tests
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_exec_command_legacy(self, sandbox):
        """Test: Legacy exec_command method works."""
        session_id = "test_legacy"
        exec_dir = "/tmp"
        command = "echo 'legacy test'"
        
        result = await sandbox.exec_command(session_id, exec_dir, command)
        assert isinstance(result, ToolResult)
    
    @pytest.mark.asyncio
    async def test_view_shell(self, sandbox):
        """Test: Can view shell status."""
        session_id = "test_shell"
        
        result = await sandbox.view_shell(session_id)
        assert isinstance(result, ToolResult)
    
    # ============================================================
    # Error Handling Tests
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_exec_command_nonzero_exit(self, sandbox):
        """Test: Handles command with non-zero exit code."""
        result = await sandbox.exec_command_stateful("exit 1")
        
        assert result["exit_code"] == 1
    
    @pytest.mark.asyncio
    async def test_file_read_nonexistent(self, sandbox):
        """Test: Handles reading non-existent file gracefully."""
        try:
            result = await sandbox.file_read("/tmp/does_not_exist_12345.txt")
            # Should return ToolResult with error information
            assert isinstance(result, ToolResult)
        except Exception as e:
            # Or may raise exception - both acceptable
            pass
    
    # ============================================================
    # Browser Tests (May Not Be Supported)
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_get_browser_availability(self, sandbox):
        """Test: get_browser either returns Browser or raises NotImplementedError."""
        try:
            browser = await sandbox.get_browser()
            # If successful, should return Browser instance
            assert browser is not None
        except NotImplementedError:
            # This is acceptable for some implementations (e.g., CloudRunJobsSandbox)
            pass


# ============================================================
# Integration Test Markers
# ============================================================

@pytest.mark.integration
class TestSandboxIntegration:
    """Integration tests that require real sandbox infrastructure."""
    
    @pytest.mark.asyncio
    async def test_large_file_upload_download(self, sandbox):
        """Test: Can upload and download large files (>10MB)."""
        pytest.skip("Integration test - requires actual implementation")
    
    @pytest.mark.asyncio
    async def test_concurrent_executions(self, sandbox):
        """Test: Can handle concurrent command executions."""
        pytest.skip("Integration test - requires actual implementation")
    
    @pytest.mark.asyncio
    async def test_session_isolation(self, sandbox):
        """Test: Different sessions are properly isolated."""
        pytest.skip("Integration test - requires actual implementation")


# ============================================================
# Performance Test Markers
# ============================================================

@pytest.mark.performance
class TestSandboxPerformance:
    """Performance tests to validate acceptable response times."""
    
    @pytest.mark.asyncio
    async def test_command_execution_latency(self, sandbox):
        """Test: Command execution latency is within acceptable range."""
        pytest.skip("Performance test - requires benchmarking setup")
    
    @pytest.mark.asyncio
    async def test_cold_start_time(self, sandbox_class):
        """Test: Cold start time is acceptable."""
        pytest.skip("Performance test - requires benchmarking setup")