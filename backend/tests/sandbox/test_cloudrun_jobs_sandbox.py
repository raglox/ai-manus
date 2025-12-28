"""
Unit tests for CloudRunJobsSandbox implementation.

Tests cover:
- Initialization and configuration
- SessionStateManager
- CloudRunJobManager
- exec_command_stateful
- Sandbox protocol methods

Author: Kilo Code
Date: 2025-12-28
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, MagicMock, patch, call
from datetime import datetime
from io import BytesIO

from app.infrastructure.external.sandbox.cloudrun_jobs_sandbox import (
    CloudRunJobsSandbox,
    SessionStateManager,
    CloudRunJobManager
)
from app.domain.models.tool_result import ToolResult


class TestSessionStateManager:
    """Test SessionStateManager functionality"""
    
    @pytest.fixture
    def mock_storage_client(self):
        """Mock Google Cloud Storage client"""
        client = Mock()
        bucket = Mock()
        client.bucket.return_value = bucket
        return client
    
    @pytest.fixture
    def state_manager(self, mock_storage_client):
        """Create SessionStateManager instance"""
        return SessionStateManager(
            storage_client=mock_storage_client,
            bucket_name="test-bucket"
        )
    
    @pytest.mark.asyncio
    async def test_load_state_new_session(self, state_manager, mock_storage_client):
        """Test loading state for new session creates default state"""
        # Mock blob doesn't exist
        blob = Mock()
        blob.exists.return_value = False
        mock_storage_client.bucket.return_value.blob.return_value = blob
        
        state = await state_manager.load_state("new-session")
        
        assert state["session_id"] == "new-session"
        assert state["cwd"] == "/workspace"
        assert state["env_vars"] == {}
        assert state["background_pids"] == {}
        assert "created_at" in state
    
    @pytest.mark.asyncio
    async def test_load_state_existing_session(self, state_manager, mock_storage_client):
        """Test loading state for existing session"""
        # Mock blob exists with state data
        existing_state = {
            "session_id": "existing-session",
            "cwd": "/tmp",
            "env_vars": {"USER": "test"},
            "background_pids": {"sleep 100": 12345},
            "created_at": "2025-12-28T10:00:00"
        }
        
        blob = Mock()
        blob.exists.return_value = True
        blob.download_as_text.return_value = json.dumps(existing_state)
        mock_storage_client.bucket.return_value.blob.return_value = blob
        
        state = await state_manager.load_state("existing-session")
        
        assert state["session_id"] == "existing-session"
        assert state["cwd"] == "/tmp"
        assert state["env_vars"]["USER"] == "test"
        assert state["background_pids"]["sleep 100"] == 12345
    
    @pytest.mark.asyncio
    async def test_save_state(self, state_manager, mock_storage_client):
        """Test saving session state"""
        state = {
            "session_id": "test-session",
            "cwd": "/workspace",
            "env_vars": {},
            "background_pids": {}
        }
        
        blob = Mock()
        mock_storage_client.bucket.return_value.blob.return_value = blob
        
        await state_manager.save_state("test-session", state)
        
        # Verify upload was called
        blob.upload_from_string.assert_called_once()
        call_args = blob.upload_from_string.call_args
        
        # Verify state was serialized correctly
        saved_data = json.loads(call_args[0][0])
        assert saved_data["session_id"] == "test-session"
        assert "last_updated" in saved_data
    
    @pytest.mark.asyncio
    async def test_save_execution_result(self, state_manager, mock_storage_client):
        """Test saving execution result"""
        result = {
            "exit_code": 0,
            "stdout": "test output",
            "stderr": "",
            "cwd": "/workspace"
        }
        
        blob = Mock()
        mock_storage_client.bucket.return_value.blob.return_value = blob
        
        await state_manager.save_execution_result("exec-123", result)
        
        # Verify result was saved
        blob.upload_from_string.assert_called_once()
        call_args = blob.upload_from_string.call_args
        saved_data = json.loads(call_args[0][0])
        assert saved_data["exit_code"] == 0
        assert saved_data["stdout"] == "test output"
    
    @pytest.mark.asyncio
    async def test_load_execution_result(self, state_manager, mock_storage_client):
        """Test loading execution result"""
        result = {
            "exit_code": 0,
            "stdout": "test output",
            "stderr": ""
        }
        
        blob = Mock()
        blob.exists.return_value = True
        blob.download_as_text.return_value = json.dumps(result)
        mock_storage_client.bucket.return_value.blob.return_value = blob
        
        loaded_result = await state_manager.load_execution_result("exec-123")
        
        assert loaded_result["exit_code"] == 0
        assert loaded_result["stdout"] == "test output"
    
    @pytest.mark.asyncio
    async def test_load_execution_result_not_found(self, state_manager, mock_storage_client):
        """Test loading non-existent execution result"""
        blob = Mock()
        blob.exists.return_value = False
        mock_storage_client.bucket.return_value.blob.return_value = blob
        
        result = await state_manager.load_execution_result("nonexistent")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_state(self, state_manager, mock_storage_client):
        """Test deleting session state"""
        blob = Mock()
        mock_storage_client.bucket.return_value.blob.return_value = blob
        
        await state_manager.delete_state("test-session")
        
        blob.delete.assert_called_once()


class TestCloudRunJobManager:
    """Test CloudRunJobManager functionality"""
    
    @pytest.fixture
    def job_manager(self):
        """Create CloudRunJobManager instance with mocked clients"""
        with patch('app.infrastructure.external.sandbox.cloudrun_jobs_sandbox.run_v2'):
            manager = CloudRunJobManager(
                project_id="test-project",
                region="us-central1",
                executor_image="gcr.io/test/executor:latest",
                state_bucket="test-bucket"
            )
            
            # Mock the clients
            manager.jobs_client = Mock()
            manager.executions_client = Mock()
            
            return manager
    
    @pytest.mark.asyncio
    async def test_create_job(self, job_manager):
        """Test job creation"""
        # Mock successful job creation
        mock_operation = Mock()
        mock_job = Mock()
        mock_job.name = "projects/test/locations/us-central1/jobs/sandbox-abc123"
        mock_operation.result.return_value = mock_job
        
        job_manager.jobs_client.create_job.return_value = mock_operation
        
        job_name = await job_manager.create_job(
            execution_id="exec-abc123",
            session_id="test-session",
            command="echo test",
            timeout=120
        )
        
        assert "sandbox-" in job_name
        job_manager.jobs_client.create_job.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_job(self, job_manager):
        """Test job execution"""
        # Mock successful execution
        mock_operation = Mock()
        mock_execution = Mock()
        mock_execution.name = "projects/test/locations/us-central1/jobs/sandbox-abc123/executions/exec-1"
        mock_operation.result.return_value = mock_execution
        
        job_manager.jobs_client.run_job.return_value = mock_operation
        
        execution_name = await job_manager.execute_job("job-name")
        
        assert "executions" in execution_name
        job_manager.jobs_client.run_job.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_wait_for_completion_success(self, job_manager):
        """Test waiting for successful completion"""
        # Mock execution that completes successfully
        mock_execution = Mock()
        mock_execution.completion_time = datetime.utcnow()
        mock_execution.succeeded_count = 1
        mock_execution.failed_count = 0
        
        job_manager.executions_client.get_execution.return_value = mock_execution
        
        result = await job_manager.wait_for_completion("execution-name", timeout=10)
        
        assert result["completed"] is True
        assert result["success"] is True
        assert result["succeeded_count"] == 1
    
    @pytest.mark.asyncio
    async def test_wait_for_completion_failure(self, job_manager):
        """Test waiting for failed completion"""
        # Mock execution that fails
        mock_execution = Mock()
        mock_execution.completion_time = datetime.utcnow()
        mock_execution.succeeded_count = 0
        mock_execution.failed_count = 1
        
        job_manager.executions_client.get_execution.return_value = mock_execution
        
        result = await job_manager.wait_for_completion("execution-name", timeout=10)
        
        assert result["completed"] is True
        assert result["success"] is False
        assert result["failed_count"] == 1
    
    @pytest.mark.asyncio
    async def test_wait_for_completion_timeout(self, job_manager):
        """Test timeout while waiting for completion"""
        # Mock execution that never completes
        mock_execution = Mock()
        mock_execution.completion_time = None
        
        job_manager.executions_client.get_execution.return_value = mock_execution
        
        result = await job_manager.wait_for_completion(
            "execution-name",
            timeout=1,
            poll_interval=0.1
        )
        
        assert result["completed"] is False
        assert result["success"] is False
        assert "timeout" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_delete_job(self, job_manager):
        """Test job deletion"""
        mock_operation = Mock()
        mock_operation.result.return_value = None
        
        job_manager.jobs_client.delete_job.return_value = mock_operation
        
        await job_manager.delete_job("job-name")
        
        job_manager.jobs_client.delete_job.assert_called_once()


class TestCloudRunJobsSandbox:
    """Test CloudRunJobsSandbox main class"""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings"""
        settings = Mock()
        settings.sandbox_gcp_project = "test-project"
        settings.sandbox_gcp_region = "us-central1"
        settings.sandbox_executor_image = "gcr.io/test/executor:latest"
        settings.sandbox_gcs_bucket = "test-bucket"
        return settings
    
    @pytest.fixture
    async def sandbox(self, mock_settings):
        """Create CloudRunJobsSandbox instance with mocked components"""
        with patch('app.infrastructure.external.sandbox.cloudrun_jobs_sandbox.storage.Client'), \
             patch('app.infrastructure.external.sandbox.cloudrun_jobs_sandbox.run_v2'), \
             patch('app.infrastructure.external.sandbox.cloudrun_jobs_sandbox.get_settings', return_value=mock_settings):
            
            sandbox = CloudRunJobsSandbox(
                project_id="test-project",
                region="us-central1",
                executor_image="gcr.io/test/executor:latest",
                state_bucket="test-bucket"
            )
            
            # Mock the managers
            sandbox.state_manager = AsyncMock()
            sandbox.job_manager = AsyncMock()
            
            return sandbox
    
    def test_initialization(self, sandbox):
        """Test sandbox initialization"""
        assert sandbox.project_id == "test-project"
        assert sandbox.region == "us-central1"
        assert sandbox.executor_image == "gcr.io/test/executor:latest"
        assert sandbox.state_bucket == "test-bucket"
        assert sandbox.id is not None
    
    def test_properties(self, sandbox):
        """Test sandbox properties"""
        assert isinstance(sandbox.id, str)
        assert sandbox.cdp_url == ""  # Not supported
        assert sandbox.vnc_url == ""  # Not supported
    
    @pytest.mark.asyncio
    async def test_ensure_sandbox(self, sandbox):
        """Test sandbox readiness check"""
        # Mock bucket exists
        mock_bucket = AsyncMock()
        mock_bucket.exists.return_value = True
        sandbox.storage_client.bucket.return_value = mock_bucket
        
        await sandbox.ensure_sandbox()
        
        # Should not raise exception
    
    @pytest.mark.asyncio
    async def test_exec_command_stateful_success(self, sandbox):
        """Test successful command execution"""
        # Mock state manager
        sandbox.state_manager.load_state.return_value = {
            "session_id": "default",
            "cwd": "/workspace",
            "env_vars": {},
            "background_pids": {}
        }
        
        sandbox.state_manager.load_execution_result.return_value = {
            "exit_code": 0,
            "stdout": "test output",
            "stderr": "",
            "cwd": "/workspace",
            "new_state": {
                "cwd": "/workspace",
                "env_vars": {},
                "background_pids": {}
            }
        }
        
        # Mock job manager
        sandbox.job_manager.create_job.return_value = "job-name"
        sandbox.job_manager.execute_job.return_value = "execution-name"
        sandbox.job_manager.wait_for_completion.return_value = {
            "completed": True,
            "success": True
        }
        
        result = await sandbox.exec_command_stateful("echo test")
        
        assert result["exit_code"] == 0
        assert result["stdout"] == "test output"
        assert result["session_id"] == "default"
        
        # Verify job was deleted
        sandbox.job_manager.delete_job.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_exec_command_stateful_with_session_id(self, sandbox):
        """Test command execution with custom session ID"""
        sandbox.state_manager.load_state.return_value = {
            "session_id": "custom",
            "cwd": "/tmp",
            "env_vars": {},
            "background_pids": {}
        }
        
        sandbox.state_manager.load_execution_result.return_value = {
            "exit_code": 0,
            "stdout": "output",
            "stderr": "",
            "cwd": "/tmp",
            "new_state": {"cwd": "/tmp", "env_vars": {}, "background_pids": {}}
        }
        
        sandbox.job_manager.create_job.return_value = "job-name"
        sandbox.job_manager.execute_job.return_value = "execution-name"
        sandbox.job_manager.wait_for_completion.return_value = {
            "completed": True,
            "success": True
        }
        
        result = await sandbox.exec_command_stateful("pwd", session_id="custom")
        
        assert result["session_id"] == "custom"
        
        # Verify state was loaded for custom session
        sandbox.state_manager.load_state.assert_called_with("custom")
    
    @pytest.mark.asyncio
    async def test_exec_command_stateful_failure(self, sandbox):
        """Test command execution failure"""
        sandbox.state_manager.load_state.return_value = {
            "session_id": "default",
            "cwd": "/workspace",
            "env_vars": {},
            "background_pids": {}
        }
        
        sandbox.state_manager.load_execution_result.return_value = {
            "exit_code": 1,
            "stdout": "",
            "stderr": "command not found",
            "cwd": "/workspace",
            "new_state": {"cwd": "/workspace", "env_vars": {}, "background_pids": {}}
        }
        
        sandbox.job_manager.create_job.return_value = "job-name"
        sandbox.job_manager.execute_job.return_value = "execution-name"
        sandbox.job_manager.wait_for_completion.return_value = {
            "completed": True,
            "success": False
        }
        
        result = await sandbox.exec_command_stateful("nonexistent")
        
        assert result["exit_code"] == 1
        assert "command not found" in result["stderr"]
    
    @pytest.mark.asyncio
    async def test_exec_command_stateful_no_result(self, sandbox):
        """Test command execution when result is not found"""
        sandbox.state_manager.load_state.return_value = {
            "session_id": "default",
            "cwd": "/workspace",
            "env_vars": {},
            "background_pids": {}
        }
        
        # No result found
        sandbox.state_manager.load_execution_result.return_value = None
        
        sandbox.job_manager.create_job.return_value = "job-name"
        sandbox.job_manager.execute_job.return_value = "execution-name"
        sandbox.job_manager.wait_for_completion.return_value = {
            "completed": False,
            "success": False
        }
        
        result = await sandbox.exec_command_stateful("echo test")
        
        assert result["exit_code"] == -1
        assert "no result found" in result["stderr"].lower()
    
    @pytest.mark.asyncio
    async def test_exec_command_stateful_exception(self, sandbox):
        """Test command execution with exception"""
        sandbox.state_manager.load_state.side_effect = Exception("Connection error")
        
        result = await sandbox.exec_command_stateful("echo test")
        
        assert result["exit_code"] == -1
        assert "connection error" in result["stderr"].lower()
    
    @pytest.mark.asyncio
    async def test_exec_command_legacy(self, sandbox):
        """Test legacy exec_command method"""
        # Mock exec_command_stateful
        sandbox.exec_command_stateful = AsyncMock(return_value={
            "exit_code": 0,
            "stdout": "test output",
            "stderr": "",
            "cwd": "/workspace",
            "session_id": "test"
        })
        
        result = await sandbox.exec_command(
            session_id="test",
            exec_dir="/workspace",
            command="echo test"
        )
        
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.data["exit_code"] == 0
        assert result.data["stdout"] == "test output"
    
    @pytest.mark.asyncio
    async def test_view_shell(self, sandbox):
        """Test view_shell method"""
        sandbox.state_manager.load_state.return_value = {
            "session_id": "test",
            "cwd": "/tmp",
            "env_vars": {"USER": "test"},
            "background_pids": {}
        }
        
        result = await sandbox.view_shell("test")
        
        assert result.success is True
        assert result.data["session_id"] == "test"
        assert result.data["cwd"] == "/tmp"
    
    @pytest.mark.asyncio
    async def test_wait_for_process(self, sandbox):
        """Test wait_for_process method"""
        result = await sandbox.wait_for_process("test", seconds=0)
        
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_write_to_process_not_supported(self, sandbox):
        """Test write_to_process is not supported"""
        result = await sandbox.write_to_process("test", "input")
        
        assert result.success is False
        assert "not supported" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_kill_process_not_supported(self, sandbox):
        """Test kill_process is not supported"""
        result = await sandbox.kill_process("test")
        
        assert result.success is False
        assert "not supported" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_destroy(self, sandbox):
        """Test sandbox destruction"""
        success = await sandbox.destroy()
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_get_browser_not_supported(self, sandbox):
        """Test get_browser raises NotImplementedError"""
        with pytest.raises(NotImplementedError) as exc_info:
            await sandbox.get_browser()
        
        assert "not available" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_create_classmethod(self, mock_settings):
        """Test create class method"""
        with patch('app.infrastructure.external.sandbox.cloudrun_jobs_sandbox.storage.Client'), \
             patch('app.infrastructure.external.sandbox.cloudrun_jobs_sandbox.run_v2'), \
             patch('app.infrastructure.external.sandbox.cloudrun_jobs_sandbox.get_settings', return_value=mock_settings):
            
            with patch.object(CloudRunJobsSandbox, 'ensure_sandbox', new_callable=AsyncMock):
                sandbox = await CloudRunJobsSandbox.create()
                
                assert isinstance(sandbox, CloudRunJobsSandbox)
                assert sandbox.project_id == "test-project"
    
    @pytest.mark.asyncio
    async def test_create_classmethod_missing_project_id(self):
        """Test create method with missing project ID"""
        mock_settings = Mock()
        mock_settings.sandbox_gcp_project = None
        
        with patch('app.infrastructure.external.sandbox.cloudrun_jobs_sandbox.get_settings', return_value=mock_settings):
            with pytest.raises(ValueError) as exc_info:
                await CloudRunJobsSandbox.create()
            
            assert "SANDBOX_GCP_PROJECT" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_list_background_processes(self, sandbox):
        """Test listing background processes"""
        processes = await sandbox.list_background_processes()
        
        assert isinstance(processes, list)
        # Currently returns empty list (not yet implemented)
    
    @pytest.mark.asyncio
    async def test_kill_background_process(self, sandbox):
        """Test killing background process"""
        result = await sandbox.kill_background_process(pid=12345)
        
        assert "killed_count" in result
        assert "killed_pids" in result
        # Currently returns 0 (not yet implemented)
    
    @pytest.mark.asyncio
    async def test_get_background_logs(self, sandbox):
        """Test getting background logs"""
        logs = await sandbox.get_background_logs(12345)
        
        # Currently returns None (not yet implemented)
        assert logs is None
    
    @pytest.mark.asyncio
    async def test_file_operations_not_implemented(self, sandbox):
        """Test that file operations return not implemented"""
        result = await sandbox.file_write("/tmp/test.txt", "content")
        assert result.success is False
        assert "not yet implemented" in result.message.lower()
        
        result = await sandbox.file_read("/tmp/test.txt")
        assert result.success is False
        
        result = await sandbox.file_exists("/tmp/test.txt")
        assert result.success is False
        
        result = await sandbox.file_delete("/tmp/test.txt")
        assert result.success is False
        
        result = await sandbox.file_list("/tmp")
        assert result.success is False
        
        result = await sandbox.file_replace("/tmp/test.txt", "old", "new")
        assert result.success is False
        
        result = await sandbox.file_search("/tmp/test.txt", "pattern")
        assert result.success is False
        
        result = await sandbox.file_find("/tmp", "*.txt")
        assert result.success is False
        
        result = await sandbox.file_upload(BytesIO(b"data"), "/tmp/test.txt")
        assert result.success is False
        
        with pytest.raises(NotImplementedError):
            await sandbox.file_download("/tmp/test.txt")


class TestIntegration:
    """Integration-style tests (still mocked but test full flow)"""
    
    @pytest.mark.asyncio
    async def test_full_execution_flow(self):
        """Test complete execution flow from start to finish"""
        mock_settings = Mock()
        mock_settings.sandbox_gcp_project = "test-project"
        mock_settings.sandbox_gcp_region = "us-central1"
        mock_settings.sandbox_executor_image = "gcr.io/test/executor:latest"
        mock_settings.sandbox_gcs_bucket = "test-bucket"
        
        with patch('app.infrastructure.external.sandbox.cloudrun_jobs_sandbox.storage.Client'), \
             patch('app.infrastructure.external.sandbox.cloudrun_jobs_sandbox.run_v2'), \
             patch('app.infrastructure.external.sandbox.cloudrun_jobs_sandbox.get_settings', return_value=mock_settings):
            
            sandbox = CloudRunJobsSandbox(
                project_id="test-project",
                region="us-central1"
            )
            
            # Mock state manager
            sandbox.state_manager = AsyncMock()
            sandbox.state_manager.load_state.return_value = {
                "session_id": "default",
                "cwd": "/workspace",
                "env_vars": {},
                "background_pids": {}
            }
            
            sandbox.state_manager.load_execution_result.return_value = {
                "exit_code": 0,
                "stdout": "Hello World",
                "stderr": "",
                "cwd": "/workspace",
                "new_state": {
                    "cwd": "/workspace",
                    "env_vars": {},
                    "background_pids": {}
                }
            }
            
            # Mock job manager
            sandbox.job_manager = AsyncMock()
            sandbox.job_manager.create_job.return_value = "job-name"
            sandbox.job_manager.execute_job.return_value = "execution-name"
            sandbox.job_manager.wait_for_completion.return_value = {
                "completed": True,
                "success": True
            }
            
            # Execute command
            result = await sandbox.exec_command_stateful("echo 'Hello World'")
            
            # Verify complete flow
            assert result["exit_code"] == 0
            assert result["stdout"] == "Hello World"
            
            # Verify all steps were called
            sandbox.state_manager.load_state.assert_called_once()
            sandbox.job_manager.create_job.assert_called_once()
            sandbox.job_manager.execute_job.assert_called_once()
            sandbox.job_manager.wait_for_completion.assert_called_once()
            sandbox.state_manager.load_execution_result.assert_called_once()
            sandbox.state_manager.save_state.assert_called_once()
            sandbox.job_manager.delete_job.assert_called_once()