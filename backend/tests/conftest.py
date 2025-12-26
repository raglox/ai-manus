"""
Pytest Configuration and Shared Fixtures

Provides mocks for:
- DockerClient (no real containers in unit tests)
- LLM Providers (no token consumption)
- Sandbox environment
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from typing import Dict, Any, List
import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Base URL for API tests
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


# ==================== FastAPI TestClient ====================

@pytest.fixture
def client():
    """Create FastAPI TestClient for API integration tests"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_user_data():
    """Test user data for authentication"""
    return {
        "fullname": "Test User",
        "password": "password123",
        "email": "testuser@example.com"
    }


@pytest.fixture
def authenticated_user(client, test_user_data):
    """Create and authenticate a test user"""
    # First register the user
    register_url = "/api/v1/auth/register"
    register_response = client.post(register_url, json=test_user_data)
    
    if register_response.status_code == 200:
        auth_data = register_response.json()["data"]
        return {
            "user_data": test_user_data,
            "auth_data": auth_data,
            "access_token": auth_data["access_token"],
            "refresh_token": auth_data["refresh_token"]
        }
    
    # If registration fails, try login (user might already exist)
    login_url = "/api/v1/auth/login"
    login_response = client.post(login_url, json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    
    if login_response.status_code == 200:
        auth_data = login_response.json()["data"]
        return {
            "user_data": test_user_data,
            "auth_data": auth_data,
            "access_token": auth_data["access_token"],
            "refresh_token": auth_data["refresh_token"]
        }
    
    # If both fail, raise error
    raise Exception("Failed to authenticate test user")


# ==================== Pytest Configuration ====================

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end (use real docker)"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (mocked dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


@pytest.fixture(scope="function")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ==================== Docker Mocks ====================

@pytest.fixture
def mock_docker_client():
    """Mock Docker client for unit tests"""
    client = MagicMock()
    
    # Mock container
    container = MagicMock()
    container.id = "test_container_123"
    container.status = "running"
    container.attrs = {
        "NetworkSettings": {
            "IPAddress": "172.17.0.2"
        }
    }
    
    # Mock exec_run results
    exec_result = MagicMock()
    exec_result.exit_code = 0
    exec_result.output = b"command output"
    container.exec_run.return_value = exec_result
    
    # Mock container operations
    container.start.return_value = None
    container.stop.return_value = None
    container.remove.return_value = None
    container.logs.return_value = b"container logs"
    
    # Mock client operations
    client.containers.run.return_value = container
    client.containers.get.return_value = container
    client.containers.list.return_value = [container]
    
    return client


@pytest.fixture
def mock_docker_container():
    """Mock Docker container"""
    container = MagicMock()
    container.id = "test_container_456"
    container.status = "running"
    container.short_id = "test456"
    container.name = "test_container"
    
    # Mock attrs
    container.attrs = {
        "NetworkSettings": {
            "IPAddress": "172.17.0.3",
            "Ports": {
                "8000/tcp": [{"HostPort": "8000"}]
            }
        },
        "State": {
            "Running": True,
            "Status": "running"
        }
    }
    
    # Mock exec operations
    exec_result = MagicMock()
    exec_result.exit_code = 0
    exec_result.output = b"exec output"
    container.exec_run.return_value = exec_result
    
    return container


# ==================== Sandbox Mocks ====================

@pytest.fixture
def mock_sandbox():
    """Mock Sandbox for tool tests"""
    sandbox = AsyncMock()
    
    # Mock exec_command_stateful
    async def mock_exec(command, session_id=None, timeout=None):
        return {
            "exit_code": 0,
            "stdout": "mocked output",
            "stderr": "",
            "background_pid": None
        }
    
    sandbox.exec_command_stateful = AsyncMock(side_effect=mock_exec)
    
    # Mock kill_background_process
    async def mock_kill(pid=None, session_id=None, pattern=None):
        return {
            "killed_count": 1,
            "killed_pids": [pid] if pid else []
        }
    
    sandbox.kill_background_process = AsyncMock(side_effect=mock_kill)
    
    # Mock list_background_processes
    async def mock_list(session_id=None):
        return []
    
    sandbox.list_background_processes = AsyncMock(side_effect=mock_list)
    
    # Mock get_background_logs
    async def mock_logs(pid):
        return "background process logs"
    
    sandbox.get_background_logs = AsyncMock(side_effect=mock_logs)
    
    return sandbox


# ==================== LLM Mocks ====================

@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider to avoid token consumption"""
    provider = AsyncMock()
    
    # Mock completion
    async def mock_completion(*args, **kwargs):
        return {
            "choices": [{
                "message": {
                    "content": "Mocked LLM response",
                    "role": "assistant"
                }
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }
    
    provider.create_completion = AsyncMock(side_effect=mock_completion)
    provider.create_chat_completion = AsyncMock(side_effect=mock_completion)
    
    return provider


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    client = AsyncMock()
    
    # Mock chat completions
    completion_response = MagicMock()
    completion_response.choices = [
        MagicMock(
            message=MagicMock(
                content="Mocked response",
                role="assistant"
            )
        )
    ]
    completion_response.usage = MagicMock(
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30
    )
    
    client.chat.completions.create = AsyncMock(return_value=completion_response)
    
    return client


# ==================== Agent Mocks ====================

@pytest.fixture
def mock_agent_state():
    """Mock agent state"""
    return {
        "messages": [],
        "current_plan": None,
        "tools_used": [],
        "iteration": 0,
        "max_iterations": 10
    }


# ==================== File System Mocks ====================

@pytest.fixture
def mock_file_system(tmp_path):
    """Provide a temporary directory for file tests"""
    # Create test directory structure
    test_dir = tmp_path / "test_workspace"
    test_dir.mkdir()
    
    (test_dir / "src").mkdir()
    (test_dir / "tests").mkdir()
    
    return test_dir


# ==================== Async Helpers ====================

@pytest.fixture
def async_mock():
    """Helper to create async mocks easily"""
    def _async_mock(*args, **kwargs):
        mock = AsyncMock(*args, **kwargs)
        return mock
    return _async_mock


# ==================== Test Data ====================

@pytest.fixture
def sample_command_outputs():
    """Sample command outputs for testing"""
    return {
        "ps_output": """  PID TTY          TIME CMD
    1 ?        00:00:00 bash
12345 ?        00:00:01 python3
12346 ?        00:00:00 node""",
        
        "netstat_output": """tcp        0      0 0.0.0.0:8080            0.0.0.0:*               LISTEN
tcp        0      0 0.0.0.0:3000            0.0.0.0:*               LISTEN""",
        
        "server_log_clean": """Starting development server...
Server running on http://localhost:8080
Ready to accept connections""",
        
        "server_log_ansi": """\x1b[32mStarting\x1b[0m development server...
Server running on \x1b[1mhttp://localhost:8080\x1b[0m
\x1b[32mReady\x1b[0m to accept connections""",
        
        "lsof_output": """12345""",
    }


# ==================== Environment Setup ====================

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Setup test environment variables"""
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")


# ==================== Cleanup ====================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test"""
    yield
    # Cleanup code here if needed
    pass
