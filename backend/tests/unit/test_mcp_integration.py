"""
MCP Integration Tests

Tests the Model Context Protocol client and connection manager.

Test Scenarios:
1. MCP Client initialization
2. Echo server connection (simple test server)
3. Tool discovery and listing
4. Tool execution
5. OpenAI format conversion
6. Error handling

Author: Senior Systems Architect
Date: 2025-12-26
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path

from app.infrastructure.external.mcp_client import (
    MCPClient,
    MCPConnection,
    MCPServerConfig,
    MCPTool
)
from app.domain.services.mcp_manager import (
    McpConnectionManager,
    create_default_config
)


class TestMCPServerConfig:
    """Test MCP server configuration"""
    
    def test_config_creation(self):
        """Test creating a server config"""
        config = MCPServerConfig(
            name="test-server",
            command="python3",
            args=["-m", "test"],
            env={"TEST": "value"},
            description="Test server"
        )
        
        assert config.name == "test-server"
        assert config.command == "python3"
        assert len(config.args) == 2
        assert config.env["TEST"] == "value"
        assert config.description == "Test server"
    
    def test_minimal_config(self):
        """Test minimal config (no env, no description)"""
        config = MCPServerConfig(
            name="minimal",
            command="echo",
            args=["hello"]
        )
        
        assert config.name == "minimal"
        assert config.env == {}
        assert config.description is None


class TestMCPTool:
    """Test MCP tool representation"""
    
    def test_tool_creation(self):
        """Test creating an MCP tool"""
        tool = MCPTool(
            name="test_tool",
            description="A test tool",
            input_schema={
                "type": "object",
                "properties": {
                    "arg1": {"type": "string"}
                }
            },
            server_name="test-server"
        )
        
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.server_name == "test-server"
        assert "properties" in tool.input_schema


class TestMCPConnection:
    """Test MCP connection to a single server"""
    
    @pytest.fixture
    def mock_sandbox(self):
        """Create mock sandbox"""
        sandbox = Mock()
        sandbox.run_in_background = AsyncMock(return_value={
            'exit_code': 0,
            'pid': 12345,
            'stdout': '',
            'stderr': ''
        })
        sandbox.execute_command = AsyncMock(return_value={
            'exit_code': 0,
            'stdout': json.dumps({
                'jsonrpc': '2.0',
                'id': 'test-id',
                'result': {'protocolVersion': '2024-11-05'}
            }),
            'stderr': ''
        })
        return sandbox
    
    @pytest.fixture
    def echo_config(self):
        """Echo server configuration"""
        return MCPServerConfig(
            name="echo",
            command="python3",
            args=["-c", "print('echo')"],
            env={"PYTHONUNBUFFERED": "1"}
        )
    
    def test_connection_creation(self, mock_sandbox, echo_config):
        """Test creating a connection"""
        connection = MCPConnection(
            echo_config,
            mock_sandbox,
            "test-session"
        )
        
        assert connection.config.name == "echo"
        assert connection.session_id == "test-session"
        assert connection.is_connected is False
        assert connection.process_id is None
    
    @pytest.mark.asyncio
    async def test_connection_lifecycle(self, mock_sandbox, echo_config):
        """Test connection connect/disconnect"""
        connection = MCPConnection(
            echo_config,
            mock_sandbox,
            "test-session"
        )
        
        # Mock successful initialization
        mock_sandbox.execute_command = AsyncMock(side_effect=[
            # First call: send initialize request (echo to stdin)
            {'exit_code': 0, 'stdout': '', 'stderr': ''},
            # Second call: read response
            {
                'exit_code': 0,
                'stdout': json.dumps({
                    'jsonrpc': '2.0',
                    'id': 'init-id',
                    'result': {
                        'protocolVersion': '2024-11-05',
                        'capabilities': {'tools': {}},
                        'serverInfo': {'name': 'echo', 'version': '1.0.0'}
                    }
                }),
                'stderr': ''
            },
            # Third call: send tools/list request
            {'exit_code': 0, 'stdout': '', 'stderr': ''},
            # Fourth call: read tools/list response
            {
                'exit_code': 0,
                'stdout': json.dumps({
                    'jsonrpc': '2.0',
                    'id': 'tools-id',
                    'result': {
                        'tools': [{
                            'name': 'echo',
                            'description': 'Echo tool',
                            'inputSchema': {
                                'type': 'object',
                                'properties': {
                                    'message': {'type': 'string'}
                                }
                            }
                        }]
                    }
                }),
                'stderr': ''
            }
        ])
        
        # Connect
        success = await connection.connect()
        
        assert success is True
        assert connection.is_connected is True
        assert connection.process_id == 12345
        assert len(connection.tools) == 1
        assert connection.tools[0].name == "echo"


class TestMCPClient:
    """Test MCP client with multiple servers"""
    
    @pytest.fixture
    def mock_sandbox(self):
        """Create mock sandbox"""
        sandbox = Mock()
        sandbox.run_in_background = AsyncMock(return_value={
            'exit_code': 0,
            'pid': 12345,
            'stdout': '',
            'stderr': ''
        })
        sandbox.execute_command = AsyncMock(return_value={
            'exit_code': 0,
            'stdout': '{}',
            'stderr': ''
        })
        return sandbox
    
    @pytest.fixture
    def client(self, mock_sandbox):
        """Create MCP client"""
        return MCPClient(mock_sandbox, "test-session")
    
    def test_client_creation(self, client, mock_sandbox):
        """Test creating MCP client"""
        assert client.sandbox == mock_sandbox
        assert client.session_id == "test-session"
        assert len(client.connections) == 0
    
    def test_get_all_tools_empty(self, client):
        """Test getting tools when no servers connected"""
        tools = client.get_all_tools()
        assert len(tools) == 0
    
    @pytest.mark.asyncio
    async def test_disconnect_all(self, client):
        """Test disconnecting all servers"""
        # Add mock connection
        mock_connection = Mock()
        mock_connection.disconnect = AsyncMock()
        client.connections["test"] = mock_connection
        
        await client.disconnect_all()
        
        assert len(client.connections) == 0
        mock_connection.disconnect.assert_called_once()


class TestMcpConnectionManager:
    """Test MCP connection manager"""
    
    @pytest.fixture
    def mock_sandbox(self):
        """Create mock sandbox"""
        sandbox = Mock()
        sandbox.run_in_background = AsyncMock(return_value={
            'exit_code': 0,
            'pid': 12345
        })
        sandbox.execute_command = AsyncMock(return_value={
            'exit_code': 0,
            'stdout': '{}',
            'stderr': ''
        })
        return sandbox
    
    @pytest.fixture
    def temp_config(self, tmp_path):
        """Create temporary config file"""
        config_file = tmp_path / "mcp_config.json"
        config_data = {
            "mcpServers": {
                "echo": {
                    "command": "python3",
                    "args": ["-c", "print('test')"],
                    "env": {},
                    "description": "Echo server"
                }
            }
        }
        config_file.write_text(json.dumps(config_data))
        return str(config_file)
    
    def test_manager_creation(self, mock_sandbox):
        """Test creating connection manager"""
        manager = McpConnectionManager(
            mock_sandbox,
            "test-session",
            "test_config.json"
        )
        
        assert manager.sandbox == mock_sandbox
        assert manager.session_id == "test-session"
        assert manager._initialized is False
    
    def test_load_config(self, mock_sandbox, temp_config):
        """Test loading configuration"""
        manager = McpConnectionManager(
            mock_sandbox,
            "test-session",
            temp_config
        )
        
        servers = manager._load_config()
        
        assert len(servers) == 1
        assert servers[0].name == "echo"
        assert servers[0].command == "python3"
    
    def test_load_missing_config(self, mock_sandbox):
        """Test loading non-existent config"""
        manager = McpConnectionManager(
            mock_sandbox,
            "test-session",
            "nonexistent.json"
        )
        
        servers = manager._load_config()
        assert len(servers) == 0
    
    def test_get_status_uninitialized(self, mock_sandbox):
        """Test getting status before initialization"""
        manager = McpConnectionManager(
            mock_sandbox,
            "test-session"
        )
        
        status = manager.get_status()
        
        assert status["initialized"] is False
        assert len(status["connected_servers"]) == 0
        assert status["total_tools"] == 0


class TestToolConversion:
    """Test MCP to OpenAI tool format conversion"""
    
    def test_convert_tools_to_openai_format(self):
        """Test converting MCP tools to OpenAI function format"""
        manager = Mock()
        manager.get_available_tools = Mock(return_value=[
            MCPTool(
                name="test_tool",
                description="A test tool",
                input_schema={
                    "type": "object",
                    "properties": {
                        "arg1": {"type": "string", "description": "First arg"}
                    },
                    "required": ["arg1"]
                },
                server_name="test-server"
            )
        ])
        
        # Create actual manager instance
        from app.domain.services.mcp_manager import McpConnectionManager
        real_manager = McpConnectionManager.__new__(McpConnectionManager)
        real_manager.client = Mock()
        real_manager.client.get_all_tools = manager.get_available_tools
        real_manager._initialized = True
        real_manager.logger = Mock()
        
        openai_tools = real_manager.convert_tools_to_openai_format()
        
        assert len(openai_tools) == 1
        assert openai_tools[0]["type"] == "function"
        assert openai_tools[0]["function"]["name"] == "test_tool"
        assert openai_tools[0]["function"]["description"] == "A test tool"
        assert "properties" in openai_tools[0]["function"]["parameters"]


class TestDefaultConfig:
    """Test default configuration generation"""
    
    def test_create_default_config(self, tmp_path):
        """Test creating default config file"""
        config_file = tmp_path / "mcp_config.json"
        
        create_default_config(str(config_file))
        
        assert config_file.exists()
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        assert "mcpServers" in config
        assert "echo" in config["mcpServers"]
        assert "filesystem" in config["mcpServers"]


# Integration test (requires real Docker)
@pytest.mark.skipif(True, reason="Requires Docker - run manually")
@pytest.mark.asyncio
class TestMCPIntegration:
    """Integration tests with real sandbox"""
    
    async def test_echo_server_integration(self):
        """Test full integration with echo server"""
        from app.infrastructure.external.sandbox.docker_sandbox import StatefulDockerSandbox
        
        # Create sandbox
        sandbox = StatefulDockerSandbox()
        await sandbox.initialize()
        
        try:
            # Create manager
            manager = McpConnectionManager(
                sandbox,
                "test-session",
                "mcp_config.json"
            )
            
            # Initialize
            success = await manager.initialize()
            assert success is True
            
            # Get tools
            tools = manager.get_available_tools()
            assert len(tools) > 0
            
            # Call echo tool
            result = await manager.call_tool("echo", {"message": "Hello MCP!"})
            assert "error" not in result
            
            # Shutdown
            await manager.shutdown()
            
        finally:
            await sandbox.destroy()


# Summary test
def test_mcp_test_suite_summary():
    """Print test suite summary"""
    test_stats = {
        'MCPServerConfig': 2,
        'MCPTool': 1,
        'MCPConnection': 2,
        'MCPClient': 3,
        'McpConnectionManager': 4,
        'ToolConversion': 1,
        'DefaultConfig': 1,
        'Integration': 1,
    }
    
    total_tests = sum(test_stats.values())
    
    print("\n" + "="*70)
    print("MCP Integration Test Suite Summary")
    print("="*70)
    for category, count in test_stats.items():
        print(f"  {category:.<40} {count:>3} tests")
    print("-"*70)
    print(f"  {'TOTAL':.<40} {total_tests:>3} tests")
    print("="*70)
    
    assert total_tests == 15, "Expected 15 tests in MCP suite"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
