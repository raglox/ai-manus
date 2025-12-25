"""
Integration tests for Stateful Sandbox implementation
Tests ENV persistence, CWD persistence, background processes, and file_editor
"""

import pytest
import asyncio
from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
from app.domain.services.tools.shell import ShellTool
from app.domain.services.tools.file import FileTool


@pytest.mark.asyncio
class TestStatefulSandbox:
    """Test suite for Stateful Sandbox features"""
    
    @pytest.fixture
    async def sandbox(self):
        """Create a sandbox instance for testing"""
        sandbox = await DockerSandbox.start_sandbox()
        yield sandbox
        # Cleanup
        # await sandbox.stop()
    
    @pytest.fixture
    def shell_tool(self, sandbox):
        """Create ShellTool instance"""
        return ShellTool(sandbox)
    
    @pytest.fixture
    def file_tool(self, sandbox):
        """Create FileTool instance"""
        return FileTool(sandbox)
    
    # ============================================================
    # Test 1: ENV Persistence (Definition of Done - Requirement 1)
    # ============================================================
    
    async def test_env_persistence_basic(self, sandbox):
        """Test basic ENV variable persistence between commands
        
        Requirement: Agent can execute 'export USER=Test' then in a 
        subsequent message 'echo $USER' and get 'Test'
        """
        # Set environment variable
        result1 = await sandbox.exec_command_stateful(
            "export USER=Test",
            session_id="default"
        )
        assert result1["exit_code"] == 0, f"Failed to set USER: {result1['stderr']}"
        
        # Verify persistence
        result2 = await sandbox.exec_command_stateful(
            "echo $USER",
            session_id="default"
        )
        assert result2["exit_code"] == 0, f"Failed to echo USER: {result2['stderr']}"
        assert "Test" in result2["stdout"], f"Expected 'Test', got: {result2['stdout']}"
    
    async def test_env_persistence_multiple_vars(self, sandbox):
        """Test multiple ENV variables persist"""
        # Set multiple variables
        await sandbox.exec_command_stateful("export VAR1=value1", session_id="default")
        await sandbox.exec_command_stateful("export VAR2=value2", session_id="default")
        await sandbox.exec_command_stateful("export VAR3=value3", session_id="default")
        
        # Verify all persist
        result = await sandbox.exec_command_stateful(
            "echo $VAR1-$VAR2-$VAR3",
            session_id="default"
        )
        assert "value1-value2-value3" in result["stdout"]
    
    async def test_env_persistence_session_isolation(self, sandbox):
        """Test ENV variables are isolated between sessions"""
        # Set VAR in session1
        await sandbox.exec_command_stateful(
            "export VAR=session1_value",
            session_id="session1"
        )
        
        # Set different VAR in session2
        await sandbox.exec_command_stateful(
            "export VAR=session2_value",
            session_id="session2"
        )
        
        # Verify isolation
        result1 = await sandbox.exec_command_stateful("echo $VAR", session_id="session1")
        result2 = await sandbox.exec_command_stateful("echo $VAR", session_id="session2")
        
        assert "session1_value" in result1["stdout"]
        assert "session2_value" in result2["stdout"]
    
    # ============================================================
    # Test 2: CWD Persistence (Definition of Done - Requirement 2)
    # ============================================================
    
    async def test_cwd_persistence_basic(self, sandbox):
        """Test CWD persistence between commands
        
        Requirement: Agent can execute 'cd /tmp' then in a subsequent
        message 'pwd' and get '/tmp'
        """
        # Change directory
        result1 = await sandbox.exec_command_stateful(
            "cd /tmp",
            session_id="default"
        )
        assert result1["exit_code"] == 0, f"Failed to cd: {result1['stderr']}"
        
        # Verify persistence
        result2 = await sandbox.exec_command_stateful(
            "pwd",
            session_id="default"
        )
        assert result2["exit_code"] == 0, f"Failed pwd: {result2['stderr']}"
        assert "/tmp" in result2["stdout"], f"Expected '/tmp', got: {result2['stdout']}"
    
    async def test_cwd_persistence_nested_dirs(self, sandbox):
        """Test CWD persistence with nested directories"""
        # Create nested structure
        await sandbox.exec_command_stateful("mkdir -p /tmp/test/nested/deep")
        
        # Navigate through directories
        await sandbox.exec_command_stateful("cd /tmp/test")
        result1 = await sandbox.exec_command_stateful("pwd")
        assert "/tmp/test" in result1["stdout"]
        
        await sandbox.exec_command_stateful("cd nested/deep")
        result2 = await sandbox.exec_command_stateful("pwd")
        assert "/tmp/test/nested/deep" in result2["stdout"]
        
        # Go back
        await sandbox.exec_command_stateful("cd ../..")
        result3 = await sandbox.exec_command_stateful("pwd")
        assert "/tmp/test" in result3["stdout"]
    
    async def test_cwd_persistence_session_isolation(self, sandbox):
        """Test CWD is isolated between sessions"""
        # Set different CWDs in different sessions
        await sandbox.exec_command_stateful("cd /tmp", session_id="session1")
        await sandbox.exec_command_stateful("cd /home", session_id="session2")
        
        # Verify isolation
        result1 = await sandbox.exec_command_stateful("pwd", session_id="session1")
        result2 = await sandbox.exec_command_stateful("pwd", session_id="session2")
        
        assert "/tmp" in result1["stdout"]
        assert "/home" in result2["stdout"]
    
    # ============================================================
    # Test 3: Combined ENV + CWD Persistence
    # ============================================================
    
    async def test_combined_env_cwd_persistence(self, sandbox):
        """Test ENV and CWD persist together"""
        session_id = "combined_test"
        
        # Set both ENV and CWD
        await sandbox.exec_command_stateful("export PROJECT=myapp", session_id=session_id)
        await sandbox.exec_command_stateful("cd /tmp", session_id=session_id)
        
        # Verify both persist
        result = await sandbox.exec_command_stateful(
            "pwd && echo $PROJECT",
            session_id=session_id
        )
        assert "/tmp" in result["stdout"]
        assert "myapp" in result["stdout"]
    
    # ============================================================
    # Test 4: Background Processes
    # ============================================================
    
    async def test_background_process_basic(self, sandbox):
        """Test background process execution with & suffix"""
        # Start background process
        result = await sandbox.exec_command_stateful(
            "sleep 5 &",
            session_id="default"
        )
        
        # Should return immediately with PID
        assert result["exit_code"] == 0
        assert "background_pid" in result
        assert result["background_pid"] > 0
        
        # Verify process is running
        check_result = await sandbox.exec_command_stateful(
            f"ps -p {result['background_pid']}",
            session_id="default"
        )
        assert "sleep" in check_result["stdout"]
    
    async def test_background_web_server(self, sandbox):
        """Test starting a web server in background
        
        Requirement: Agent can start web server and connect to it
        """
        # Start Python HTTP server in background
        result = await sandbox.exec_command_stateful(
            "cd /tmp && python3 -m http.server 8000 &",
            session_id="default"
        )
        
        assert result["exit_code"] == 0
        assert "background_pid" in result
        pid = result["background_pid"]
        
        # Wait for server to start
        await asyncio.sleep(2)
        
        # Test connection
        curl_result = await sandbox.exec_command_stateful(
            "curl -s http://localhost:8000",
            session_id="default"
        )
        
        # Should get HTML response
        assert curl_result["exit_code"] == 0
        assert "Directory listing" in curl_result["stdout"] or "<html" in curl_result["stdout"].lower()
        
        # Cleanup: kill the server
        await sandbox.exec_command_stateful(f"kill {pid}", session_id="default")
    
    async def test_multiple_background_processes(self, sandbox):
        """Test multiple background processes tracked separately"""
        session_id = "multi_bg"
        
        # Start multiple background processes
        result1 = await sandbox.exec_command_stateful("sleep 10 &", session_id=session_id)
        result2 = await sandbox.exec_command_stateful("sleep 20 &", session_id=session_id)
        result3 = await sandbox.exec_command_stateful("sleep 30 &", session_id=session_id)
        
        pid1 = result1["background_pid"]
        pid2 = result2["background_pid"]
        pid3 = result3["background_pid"]
        
        # All PIDs should be different
        assert pid1 != pid2
        assert pid2 != pid3
        assert pid1 != pid3
        
        # All should be running
        for pid in [pid1, pid2, pid3]:
            result = await sandbox.exec_command_stateful(f"ps -p {pid}", session_id=session_id)
            assert result["exit_code"] == 0
        
        # Cleanup
        await sandbox.exec_command_stateful(f"kill {pid1} {pid2} {pid3}", session_id=session_id)
    
    # ============================================================
    # Test 5: File Editor Integration (via ShellTool & FileTool)
    # ============================================================
    
    async def test_file_editor_create_and_view(self, file_tool):
        """Test file creation and viewing using file_editor"""
        test_content = "line1\\nline2\\nline3"
        test_path = "/tmp/test_file.txt"
        
        # Create file
        create_result = await file_tool.file_create(
            path=test_path,
            file_text=test_content
        )
        assert create_result.success, f"Failed to create: {create_result.message}"
        
        # View file
        view_result = await file_tool.file_view(path=test_path)
        assert view_result.success, f"Failed to view: {view_result.message}"
        assert "line1" in view_result.message
        assert "line2" in view_result.message
    
    async def test_file_editor_str_replace(self, file_tool):
        """Test string replacement in files"""
        test_path = "/tmp/replace_test.py"
        
        # Create file
        await file_tool.file_create(
            path=test_path,
            file_text="x = 1\\ny = 2\\nz = 3"
        )
        
        # Replace string
        replace_result = await file_tool.file_str_replace(
            path=test_path,
            old_str="y = 2",
            new_str="y = 999"
        )
        assert replace_result.success
        
        # Verify replacement
        view_result = await file_tool.file_view(path=test_path)
        assert "y = 999" in view_result.message
        assert "y = 2" not in view_result.message
    
    async def test_file_editor_view_range(self, file_tool):
        """Test viewing specific line ranges"""
        test_path = "/tmp/range_test.txt"
        lines = "\\n".join([f"line{i}" for i in range(1, 101)])
        
        # Create file with 100 lines
        await file_tool.file_create(path=test_path, file_text=lines)
        
        # View specific range
        view_result = await file_tool.file_view(
            path=test_path,
            view_range=[10, 20]
        )
        assert view_result.success
        assert "line10" in view_result.message
        assert "line20" in view_result.message
        assert "line1" not in view_result.message  # Outside range
        assert "line50" not in view_result.message  # Outside range
    
    # ============================================================
    # Test 6: grep Integration (Definition of Done - Requirement 3)
    # ============================================================
    
    async def test_grep_search(self, shell_tool, file_tool):
        """Test grep search using file_editor + shell
        
        Requirement: Agent can use grep to search files
        """
        test_path = "/tmp/grep_test.txt"
        test_content = "hello world\\nfoo bar\\nhello again\\ntest line"
        
        # Create test file
        await file_tool.file_create(path=test_path, file_text=test_content)
        
        # Search for pattern
        grep_result = await shell_tool.shell_exec(
            command=f"grep 'hello' {test_path}"
        )
        
        assert grep_result.success
        assert "hello world" in grep_result.message
        assert "hello again" in grep_result.message
        assert "foo bar" not in grep_result.message
    
    async def test_grep_recursive_search(self, shell_tool, file_tool):
        """Test recursive grep search"""
        # Create directory structure with files
        await shell_tool.shell_exec("mkdir -p /tmp/grep_test/subdir")
        await file_tool.file_create(
            path="/tmp/grep_test/file1.txt",
            file_text="pattern found here"
        )
        await file_tool.file_create(
            path="/tmp/grep_test/subdir/file2.txt",
            file_text="pattern also here"
        )
        
        # Recursive search
        grep_result = await shell_tool.shell_exec(
            command="grep -r 'pattern' /tmp/grep_test/"
        )
        
        assert grep_result.success
        assert "file1.txt" in grep_result.message
        assert "file2.txt" in grep_result.message
    
    # ============================================================
    # Test 7: Complex Workflow (Combined Features)
    # ============================================================
    
    async def test_complex_workflow(self, sandbox, shell_tool, file_tool):
        """Test complex workflow combining all features"""
        session_id = "workflow_test"
        
        # 1. Set up environment
        await sandbox.exec_command_stateful(
            "export PROJECT_NAME=MyApp",
            session_id=session_id
        )
        await sandbox.exec_command_stateful(
            "mkdir -p /tmp/myapp && cd /tmp/myapp",
            session_id=session_id
        )
        
        # 2. Create project structure
        await file_tool.file_create(
            path="/tmp/myapp/main.py",
            file_text="#!/usr/bin/env python3\\nprint('Hello from MyApp')"
        )
        await file_tool.file_create(
            path="/tmp/myapp/config.json",
            file_text='{"name": "MyApp", "version": "1.0"}'
        )
        
        # 3. Verify environment and CWD persist
        verify_result = await sandbox.exec_command_stateful(
            "pwd && echo $PROJECT_NAME && ls",
            session_id=session_id
        )
        assert "/tmp/myapp" in verify_result["stdout"]
        assert "MyApp" in verify_result["stdout"]
        assert "main.py" in verify_result["stdout"]
        
        # 4. Start background process
        bg_result = await sandbox.exec_command_stateful(
            "python3 -m http.server 9000 &",
            session_id=session_id
        )
        assert "background_pid" in bg_result
        
        # 5. Test the server
        await asyncio.sleep(1)
        curl_result = await sandbox.exec_command_stateful(
            "curl -s http://localhost:9000",
            session_id=session_id
        )
        assert "main.py" in curl_result["stdout"]
        
        # 6. Cleanup
        await sandbox.exec_command_stateful(
            f"kill {bg_result['background_pid']}",
            session_id=session_id
        )
    
    # ============================================================
    # Test 8: Error Handling
    # ============================================================
    
    async def test_invalid_command_handling(self, sandbox):
        """Test graceful handling of invalid commands"""
        result = await sandbox.exec_command_stateful(
            "nonexistent_command_xyz",
            session_id="default"
        )
        
        assert result["exit_code"] != 0
        assert len(result["stderr"]) > 0
    
    async def test_cd_to_nonexistent_dir(self, sandbox):
        """Test cd to non-existent directory"""
        result = await sandbox.exec_command_stateful(
            "cd /nonexistent/path",
            session_id="default"
        )
        
        # CWD should remain unchanged
        pwd_result = await sandbox.exec_command_stateful("pwd", session_id="default")
        assert "/nonexistent" not in pwd_result["stdout"]


# ============================================================
# Performance Tests
# ============================================================

@pytest.mark.asyncio
class TestStatefulSandboxPerformance:
    """Performance and stress tests"""
    
    async def test_session_creation_overhead(self):
        """Test overhead of creating multiple sessions"""
        import time
        sandbox = await DockerSandbox.start_sandbox()
        
        start = time.time()
        for i in range(100):
            await sandbox.exec_command_stateful(
                f"export VAR{i}=value{i}",
                session_id=f"session_{i}"
            )
        elapsed = time.time() - start
        
        # Should complete in reasonable time
        assert elapsed < 30, f"Too slow: {elapsed}s for 100 sessions"
    
    async def test_many_env_vars(self):
        """Test handling many ENV variables"""
        sandbox = await DockerSandbox.start_sandbox()
        session_id = "many_vars"
        
        # Set 100 ENV variables
        for i in range(100):
            await sandbox.exec_command_stateful(
                f"export VAR_{i}=value_{i}",
                session_id=session_id
            )
        
        # Verify a few random ones
        result = await sandbox.exec_command_stateful(
            "echo $VAR_0-$VAR_50-$VAR_99",
            session_id=session_id
        )
        assert "value_0-value_50-value_99" in result["stdout"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
