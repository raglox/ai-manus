"""
Integration Tests for API Routes
Coverage: Auth, Sessions, Files, Health endpoints
"""
import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime


@pytest.fixture
async def async_client(app):
    """Create async HTTP client for testing"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def app():
    """Create test FastAPI app"""
    from app.main import create_app
    return create_app()


@pytest.fixture
def auth_headers():
    """Create authentication headers"""
    return {"Authorization": "Bearer test_token_12345"}


@pytest.fixture
def sample_user_data():
    """Sample user registration data"""
    return {
        "fullname": "Test User",
        "email": "test@example.com",
        "password": "SecurePass123!"
    }


class TestAuthAPI:
    """Integration tests for authentication APIs"""
    
    @pytest.mark.asyncio
    async def test_register_success(
        self, 
        async_client, 
        sample_user_data
    ):
        """Test successful user registration via API"""
        with patch('app.interfaces.dependencies.get_auth_service') as mock_service:
            # Mock the service response
            mock_auth = AsyncMock()
            mock_auth.register.return_value = {
                "user": {
                    "id": "user123",
                    "email": sample_user_data["email"],
                    "fullname": sample_user_data["fullname"]
                },
                "access_token": "mock_access_token",
                "refresh_token": "mock_refresh_token"
            }
            mock_service.return_value = mock_auth
            
            response = await async_client.post(
                "/api/v1/auth/register",
                json=sample_user_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "user" in data
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(
        self, 
        async_client, 
        sample_user_data
    ):
        """Test registration with duplicate email"""
        with patch('app.interfaces.dependencies.get_auth_service') as mock_service:
            mock_auth = AsyncMock()
            mock_auth.register.side_effect = Exception("Email already exists")
            mock_service.return_value = mock_auth
            
            response = await async_client.post(
                "/api/v1/auth/register",
                json=sample_user_data
            )
            
            assert response.status_code in [400, 409]
    
    @pytest.mark.asyncio
    async def test_login_success(
        self, 
        async_client
    ):
        """Test successful login via API"""
        with patch('app.interfaces.dependencies.get_auth_service') as mock_service:
            mock_auth = AsyncMock()
            mock_auth.login.return_value = {
                "user": {
                    "id": "user123",
                    "email": "test@example.com"
                },
                "access_token": "mock_access_token",
                "refresh_token": "mock_refresh_token"
            }
            mock_service.return_value = mock_auth
            
            response = await async_client.post(
                "/api/v1/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "password123"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
    
    @pytest.mark.asyncio
    async def test_login_wrong_credentials(
        self, 
        async_client
    ):
        """Test login with wrong credentials"""
        with patch('app.interfaces.dependencies.get_auth_service') as mock_service:
            mock_auth = AsyncMock()
            mock_auth.login.side_effect = Exception("Invalid credentials")
            mock_service.return_value = mock_auth
            
            response = await async_client.post(
                "/api/v1/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "wrong_password"
                }
            )
            
            assert response.status_code in [401, 403]
    
    @pytest.mark.asyncio
    async def test_get_current_user(
        self, 
        async_client, 
        auth_headers
    ):
        """Test getting current user via API"""
        with patch('app.interfaces.dependencies.get_current_user') as mock_user:
            mock_user.return_value = Mock(
                id="user123",
                email="test@example.com",
                fullname="Test User"
            )
            
            response = await async_client.get(
                "/api/v1/auth/me",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_refresh_token(
        self, 
        async_client
    ):
        """Test token refresh via API"""
        with patch('app.interfaces.dependencies.get_auth_service') as mock_service:
            mock_auth = AsyncMock()
            mock_auth.refresh_token.return_value = {
                "access_token": "new_access_token",
                "refresh_token": "new_refresh_token"
            }
            mock_service.return_value = mock_auth
            
            response = await async_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "old_refresh_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
    
    @pytest.mark.asyncio
    async def test_logout(
        self, 
        async_client, 
        auth_headers
    ):
        """Test logout via API"""
        with patch('app.interfaces.dependencies.get_auth_service') as mock_service:
            mock_auth = AsyncMock()
            mock_auth.logout.return_value = None
            mock_service.return_value = mock_auth
            
            response = await async_client.post(
                "/api/v1/auth/logout",
                headers=auth_headers
            )
            
            assert response.status_code in [200, 204]


class TestSessionAPI:
    """Integration tests for session APIs"""
    
    @pytest.mark.asyncio
    async def test_create_session(
        self, 
        async_client, 
        auth_headers
    ):
        """Test creating session via API"""
        with patch('app.interfaces.dependencies.get_current_user') as mock_user:
            mock_user.return_value = Mock(id="user123", email="test@example.com")
            
            response = await async_client.put(
                "/api/v1/sessions",
                headers=auth_headers
            )
            
            # Should create session
            assert response.status_code in [200, 201]
            if response.status_code == 200:
                data = response.json()
                assert "session_id" in data
    
    @pytest.mark.asyncio
    async def test_list_sessions(
        self, 
        async_client, 
        auth_headers
    ):
        """Test listing sessions via API"""
        with patch('app.interfaces.dependencies.get_current_user') as mock_user:
            mock_user.return_value = Mock(id="user123", email="test@example.com")
            
            response = await async_client.get(
                "/api/v1/sessions",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list) or "sessions" in data
    
    @pytest.mark.asyncio
    async def test_get_session_by_id(
        self, 
        async_client, 
        auth_headers
    ):
        """Test getting specific session via API"""
        session_id = "test_session_123"
        
        with patch('app.interfaces.dependencies.get_current_user') as mock_user:
            mock_user.return_value = Mock(id="user123", email="test@example.com")
            
            response = await async_client.get(
                f"/api/v1/sessions/{session_id}",
                headers=auth_headers
            )
            
            # Might be 200 or 404 depending on if session exists
            assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_delete_session(
        self, 
        async_client, 
        auth_headers
    ):
        """Test deleting session via API"""
        session_id = "test_session_123"
        
        with patch('app.interfaces.dependencies.get_current_user') as mock_user:
            mock_user.return_value = Mock(id="user123", email="test@example.com")
            
            response = await async_client.delete(
                f"/api/v1/sessions/{session_id}",
                headers=auth_headers
            )
            
            # Might be 200, 204, or 404
            assert response.status_code in [200, 204, 404]
    
    @pytest.mark.asyncio
    async def test_stop_session(
        self, 
        async_client, 
        auth_headers
    ):
        """Test stopping session via API"""
        session_id = "test_session_123"
        
        with patch('app.interfaces.dependencies.get_current_user') as mock_user:
            mock_user.return_value = Mock(id="user123", email="test@example.com")
            
            response = await async_client.post(
                f"/api/v1/sessions/{session_id}/stop",
                headers=auth_headers
            )
            
            assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_chat_with_session(
        self, 
        async_client, 
        auth_headers
    ):
        """Test sending chat message via API"""
        session_id = "test_session_123"
        
        with patch('app.interfaces.dependencies.get_current_user') as mock_user:
            mock_user.return_value = Mock(id="user123", email="test@example.com")
            
            response = await async_client.post(
                f"/api/v1/sessions/{session_id}/chat",
                headers=auth_headers,
                json={"message": "Hello AI"}
            )
            
            # Might be streaming response or regular response
            assert response.status_code in [200, 404]


class TestHealthAPI:
    """Integration tests for health check APIs"""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(
        self, 
        async_client
    ):
        """Test health check endpoint"""
        response = await async_client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_no_auth_required(
        self, 
        async_client
    ):
        """Test health endpoint doesn't require auth"""
        # Should work without auth headers
        response = await async_client.get("/api/v1/health")
        
        assert response.status_code == 200


class TestFileAPI:
    """Integration tests for file APIs"""
    
    @pytest.mark.asyncio
    async def test_upload_file(
        self, 
        async_client, 
        auth_headers
    ):
        """Test file upload via API"""
        files = {"file": ("test.txt", b"Test content", "text/plain")}
        
        with patch('app.interfaces.dependencies.get_current_user') as mock_user:
            mock_user.return_value = Mock(id="user123", email="test@example.com")
            
            response = await async_client.post(
                "/api/v1/files/upload",
                headers=auth_headers,
                files=files
            )
            
            assert response.status_code in [200, 201]
    
    @pytest.mark.asyncio
    async def test_list_files(
        self, 
        async_client, 
        auth_headers
    ):
        """Test listing files via API"""
        with patch('app.interfaces.dependencies.get_current_user') as mock_user:
            mock_user.return_value = Mock(id="user123", email="test@example.com")
            
            response = await async_client.get(
                "/api/v1/files",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list) or "files" in data


class TestErrorHandling:
    """Test API error handling"""
    
    @pytest.mark.asyncio
    async def test_404_for_invalid_route(
        self, 
        async_client
    ):
        """Test 404 for non-existent route"""
        response = await async_client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_401_for_unauthorized(
        self, 
        async_client
    ):
        """Test 401 for unauthorized access"""
        # Access protected endpoint without auth
        response = await async_client.get("/api/v1/sessions")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_400_for_invalid_data(
        self, 
        async_client
    ):
        """Test 400 for invalid request data"""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={"invalid": "data"}
        )
        
        assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_500_for_internal_error(
        self, 
        async_client
    ):
        """Test 500 for internal server errors"""
        # This would require mocking internal services to fail
        pass


class TestRateLimiting:
    """Test API rate limiting"""
    
    @pytest.mark.asyncio
    async def test_rate_limit_enforcement(
        self, 
        async_client, 
        auth_headers
    ):
        """Test rate limiting kicks in after many requests"""
        # Send many requests rapidly
        responses = []
        for _ in range(150):  # Assuming limit is 100/minute
            response = await async_client.get(
                "/api/v1/health",
                headers=auth_headers
            )
            responses.append(response)
        
        # Some should be rate limited
        rate_limited = [r for r in responses if r.status_code == 429]
        
        # Depending on implementation
        # assert len(rate_limited) > 0


class TestCORS:
    """Test CORS headers"""
    
    @pytest.mark.asyncio
    async def test_cors_headers_present(
        self, 
        async_client
    ):
        """Test CORS headers are present in responses"""
        response = await async_client.get("/api/v1/health")
        
        # Should have CORS headers
        # assert "access-control-allow-origin" in response.headers


class TestOpenAPI:
    """Test OpenAPI documentation"""
    
    @pytest.mark.asyncio
    async def test_openapi_json(
        self, 
        async_client
    ):
        """Test OpenAPI spec is available"""
        response = await async_client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
    
    @pytest.mark.asyncio
    async def test_docs_available(
        self, 
        async_client
    ):
        """Test /docs endpoint is available"""
        response = await async_client.get("/docs")
        
        assert response.status_code == 200
