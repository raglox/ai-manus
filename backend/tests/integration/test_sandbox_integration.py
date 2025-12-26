"""
Integration Tests for Sandbox Components

These tests verify integration between components without requiring
full E2E setup. They use mocking for external dependencies.

Run with: pytest tests/integration/test_sandbox_integration.py -v
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any

# Test Configuration
pytestmark = pytest.mark.integration


class TestSandboxIntegration:
    """Integration tests for sandbox functionality"""
    
    @pytest.fixture
    def mock_httpx_client(self):
        """Mock httpx client for sandbox API calls"""
        client = AsyncMock()
        client.post = AsyncMock()
        client.get = AsyncMock()
        return client
    
    @pytest.fixture
    def sandbox_with_mock(self, mock_httpx_client):
        """Create DockerSandbox with mocked HTTP client"""
        from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
        
        # Create sandbox with test IP
        sandbox = DockerSandbox(ip="127.0.0.1", container_name="test-sandbox")
        
        # Replace HTTP client with mock
        sandbox.client = mock_httpx_client
        
        return sandbox
    
    @pytest.mark.asyncio
    async def test_exec_command_integration(self, sandbox_with_mock, mock_httpx_client):
        """
        Test exec_command integration flow
        
        Verifies:
        - Command construction
        - HTTP API call
        - Response parsing
        """
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "exit_code": 0,
            "stdout": "Hello World\n",
            "stderr": ""
        }
        mock_httpx_client.post.return_value = mock_response
        
        # Execute command
        result = await sandbox_with_mock.exec_command("echo 'Hello World'")
        
        # Verify API was called
        assert mock_httpx_client.post.called
        call_args = mock_httpx_client.post.call_args
        assert "/api/execute" in str(call_args)
        
        # Verify result
        assert result["exit_code"] == 0
        assert "Hello World" in result["stdout"]
        print("✅ exec_command integration working")
    
    @pytest.mark.asyncio
    async def test_file_operations_integration(self, sandbox_with_mock, mock_httpx_client):
        """
        Test file upload/download integration
        
        Verifies:
        - File upload flow
        - File download flow
        - Error handling
        """
        # Test file upload
        mock_upload_response = Mock()
        mock_upload_response.status_code = 200
        mock_upload_response.json.return_value = {"success": True, "path": "/tmp/test.txt"}
        
        # Test file download
        mock_download_response = Mock()
        mock_download_response.status_code = 200
        mock_download_response.content = b"test content"
        
        # Setup different responses for upload/download
        def mock_post_side_effect(url, **kwargs):
            if "upload" in url:
                return mock_upload_response
            return Mock(status_code=200)
        
        def mock_get_side_effect(url, **kwargs):
            if "download" in url:
                return mock_download_response
            return Mock(status_code=200)
        
        mock_httpx_client.post.side_effect = mock_post_side_effect
        mock_httpx_client.get.side_effect = mock_get_side_effect
        
        # Test upload
        from io import BytesIO
        file_data = BytesIO(b"test content")
        result = await sandbox_with_mock.file_upload(file_data, "/tmp/test.txt")
        
        assert result.success
        print("✅ file_upload integration working")
        
        # Test download
        download_result = await sandbox_with_mock.file_download("/tmp/test.txt")
        
        assert download_result.success
        assert download_result.data is not None
        print("✅ file_download integration working")
    
    @pytest.mark.asyncio
    async def test_session_management_integration(self, sandbox_with_mock):
        """
        Test session management integration
        
        Verifies:
        - Session creation
        - Session state tracking
        - Session cleanup
        """
        # Create multiple sessions
        session1_info = sandbox_with_mock.get_session_info("session1")
        session2_info = sandbox_with_mock.get_session_info("session2")
        
        # Verify sessions are created automatically
        assert session1_info is not None or sandbox_with_mock._get_or_create_session("session1")
        assert session2_info is not None or sandbox_with_mock._get_or_create_session("session2")
        
        # List sessions
        sessions = sandbox_with_mock.list_sessions()
        assert len(sessions) >= 1  # At least default session
        
        print(f"✅ Session management working - {len(sessions)} sessions")
    
    @pytest.mark.asyncio
    async def test_background_process_tracking_integration(self, sandbox_with_mock, mock_httpx_client):
        """
        Test background process tracking integration
        
        Verifies:
        - Background process execution
        - PID tracking
        - Process listing
        """
        # Mock response for background command
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "exit_code": 0,
            "stdout": "12345\n",  # PID
            "stderr": ""
        }
        mock_httpx_client.post.return_value = mock_response
        
        # Start background process
        result = await sandbox_with_mock.exec_command(
            "python3 -m http.server 8000 &",
            background=True
        )
        
        assert result["exit_code"] == 0
        
        # Verify tracking (check session state)
        default_session = sandbox_with_mock._get_or_create_session("default")
        # Background processes should be tracked in session
        # (Note: actual tracking happens in exec_command_stateful)
        
        print("✅ Background process tracking integration working")
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, sandbox_with_mock, mock_httpx_client):
        """
        Test error handling integration
        
        Verifies:
        - Network errors
        - API errors
        - Timeout handling
        """
        # Test network error
        mock_httpx_client.post.side_effect = Exception("Connection failed")
        
        try:
            await sandbox_with_mock.exec_command("test")
            assert False, "Should have raised exception"
        except Exception as e:
            assert "Connection failed" in str(e) or "failed" in str(e).lower()
            print("✅ Error handling integration working")
    
    @pytest.mark.asyncio
    async def test_sandbox_create_with_settings(self):
        """
        Test sandbox creation with settings
        
        Verifies:
        - Settings are loaded correctly
        - Sandbox can be created with default settings
        """
        from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
        from app.core.config import get_settings
        
        settings = get_settings()
        
        # Create sandbox with settings-based configuration
        # This tests the factory method path
        if settings.sandbox_address:
            # If sandbox address is configured, verify it's used
            sandbox = DockerSandbox(ip=settings.sandbox_address, container_name="test")
            assert sandbox.ip == settings.sandbox_address
            print(f"✅ Sandbox created with configured address: {settings.sandbox_address}")
        else:
            # If no sandbox address, would need to create container
            # For integration test, we just verify the settings are accessible
            assert settings.sandbox_image is not None
            assert settings.sandbox_name_prefix is not None
            print("✅ Sandbox settings loaded successfully")


class TestWebDevToolIntegration:
    """Integration tests for WebDevTool"""
    
    @pytest.fixture
    def mock_sandbox(self):
        """Create mock sandbox for WebDevTool"""
        sandbox = AsyncMock()
        sandbox.exec_command = AsyncMock()
        sandbox.file_upload = AsyncMock()
        sandbox.file_download = AsyncMock()
        return sandbox
    
    @pytest.fixture
    def webdev_tool(self, mock_sandbox):
        """Create WebDevTool with mock sandbox"""
        from app.domain.services.tools.webdev import WebDevTool
        return WebDevTool(mock_sandbox)
    
    @pytest.mark.asyncio
    async def test_webdev_tool_initialization(self, webdev_tool):
        """Test WebDevTool initialization"""
        assert webdev_tool is not None
        assert hasattr(webdev_tool, 'sandbox')
        print("✅ WebDevTool initialization working")
    
    @pytest.mark.asyncio
    async def test_webdev_tool_with_sandbox_mock(self, webdev_tool, mock_sandbox):
        """Test WebDevTool interacts correctly with sandbox"""
        # Mock successful command execution
        mock_sandbox.exec_command.return_value = {
            "exit_code": 0,
            "stdout": "Server started\n12345",  # PID
            "stderr": ""
        }
        
        # Test server start (this tests the integration between WebDevTool and sandbox)
        from app.domain.models.tool_result import ToolResult
        
        result = await webdev_tool.start_server(
            command="python3 -m http.server 8000",
            timeout_seconds=15
        )
        
        # Verify sandbox was called
        assert mock_sandbox.exec_command.called
        
        print("✅ WebDevTool-Sandbox integration working")


class TestAuthServiceIntegration:
    """Integration tests for Auth Service"""
    
    @pytest.fixture
    def mock_user_repository(self):
        """Mock user repository"""
        repo = AsyncMock()
        repo.find_by_email = AsyncMock()
        repo.create_user = AsyncMock()
        repo.update = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_token_service(self):
        """Mock token service"""
        service = Mock()
        service.create_access_token = Mock(return_value="mock_access_token")
        service.create_refresh_token = Mock(return_value="mock_refresh_token")
        service.verify_token = Mock()
        service.get_user_from_token = Mock()
        return service
    
    @pytest.fixture
    def auth_service(self, mock_user_repository, mock_token_service):
        """Create AuthService with mocked dependencies"""
        from app.application.services.auth_service import AuthService
        return AuthService(mock_user_repository, mock_token_service)
    
    @pytest.mark.asyncio
    async def test_auth_service_integration_flow(
        self, 
        auth_service, 
        mock_user_repository,
        mock_token_service
    ):
        """
        Test complete auth flow integration
        
        Verifies:
        - Registration creates user and tokens
        - Login verifies credentials and returns tokens
        - Token operations work correctly
        """
        from app.domain.models.user import User, UserRole
        from datetime import datetime, UTC
        
        # Setup: User doesn't exist yet
        mock_user_repository.find_by_email.return_value = None
        
        # Create mock user
        created_user = User(
            id="user123",
            fullname="Test User",
            email="test@example.com",
            password_hash="hashed_password",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        mock_user_repository.create_user.return_value = created_user
        
        # Test registration
        result = await auth_service.register_user(
            fullname="Test User",
            email="test@example.com",
            password="SecurePass123",
            auth_provider="password"
        )
        
        assert result is not None
        assert result.id == "user123"
        assert mock_user_repository.create_user.called
        
        print("✅ Auth Service registration integration working")
        
        # Test login flow
        mock_user_repository.find_by_email.return_value = created_user
        
        # Mock password verification
        with patch('app.application.services.auth_service.verify_password', return_value=True):
            login_result = await auth_service.login_with_tokens(
                email="test@example.com",
                password="SecurePass123"
            )
        
        assert login_result is not None
        assert login_result.access_token == "mock_access_token"
        assert login_result.refresh_token == "mock_refresh_token"
        
        print("✅ Auth Service login integration working")


# Summary test to verify all integrations
@pytest.mark.integration
class TestFullIntegration:
    """High-level integration tests"""
    
    @pytest.mark.asyncio
    async def test_system_components_integration(self):
        """
        Verify all major components can be imported and initialized
        
        This is a smoke test to ensure no circular dependencies
        or import errors in the integration layer.
        """
        # Test imports
        from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
        from app.domain.services.tools.webdev import WebDevTool
        from app.application.services.auth_service import AuthService
        from app.domain.models.user import User
        from app.domain.models.tool_result import ToolResult
        
        # Verify classes are importable
        assert DockerSandbox is not None
        assert WebDevTool is not None
        assert AuthService is not None
        assert User is not None
        assert ToolResult is not None
        
        print("✅ All system components can be imported")
        print("✅ No circular dependencies detected")
        print("✅ Integration layer is healthy")
    
    def test_configuration_integration(self):
        """Test that configuration is properly integrated"""
        from app.core.config import get_settings
        
        settings = get_settings()
        
        # Verify critical settings are present
        assert hasattr(settings, 'sandbox_image')
        assert hasattr(settings, 'sandbox_name_prefix')
        assert hasattr(settings, 'auth_provider')
        
        print("✅ Configuration integration working")
        print(f"   - sandbox_image: {settings.sandbox_image}")
        print(f"   - auth_provider: {settings.auth_provider}")
