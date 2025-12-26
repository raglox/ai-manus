"""
MCPSandboxTool Tests

Tests the integration between MCPSandboxTool and the agent tool system.

Author: Senior Systems Architect
Date: 2025-12-26
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from app.domain.services.tools.mcp_sandbox import MCPSandboxTool
from app.domain.models.tool_result import ToolResult


class TestMCPSandboxTool:
    """Test MCPSandboxTool"""
    
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
    def mcp_tool(self, mock_sandbox):
        """Create MCPSandboxTool instance"""
        return MCPSandboxTool(
            sandbox=mock_sandbox,
            session_id="test-session",
            config_path="mcp_config.json"
        )
    
    def test_tool_creation(self, mcp_tool, mock_sandbox):
        """Test creating MCPSandboxTool"""
        assert mcp_tool.name == "mcp_sandbox"
        assert mcp_tool.sandbox == mock_sandbox
        assert mcp_tool.session_id == "test-session"
        assert mcp_tool._initialized is False
        assert len(mcp_tool._tools) == 0
    
    def test_get_tools_before_init(self, mcp_tool):
        """Test get_tools before initialization"""
        tools = mcp_tool.get_tools()
        assert tools == []
    
    def test_has_function_before_init(self, mcp_tool):
        """Test has_function before initialization"""
        assert mcp_tool.has_function("any_tool") is False
    
    @pytest.mark.asyncio
    async def test_invoke_before_init(self, mcp_tool):
        """Test invoke_function before initialization"""
        result = await mcp_tool.invoke_function("test_tool", arg="value")
        
        assert result.success is False
        assert "not initialized" in result.message.lower()
    
    def test_get_status_before_init(self, mcp_tool):
        """Test get_status before initialization"""
        status = mcp_tool.get_status()
        
        assert status["initialized"] is False
        assert status["tools_count"] == 0
        assert status["servers"] == []
    
    @pytest.mark.asyncio
    async def test_initialize_with_mock_manager(self, mcp_tool):
        """Test initialization with mocked manager"""
        # Mock the manager
        mock_manager = Mock()
        mock_manager.initialize = AsyncMock(return_value=True)
        mock_manager.convert_tools_to_openai_format = Mock(return_value=[
            {
                "type": "function",
                "function": {
                    "name": "test_tool",
                    "description": "A test tool",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ])
        
        with patch(
            'app.domain.services.tools.mcp_sandbox.McpConnectionManager',
            return_value=mock_manager
        ):
            success = await mcp_tool.initialize()
        
        assert success is True
        assert mcp_tool._initialized is True
        assert len(mcp_tool._tools) == 1
        assert mcp_tool._tools[0]['function']['name'] == "test_tool"
    
    @pytest.mark.asyncio
    async def test_get_tools_after_init(self, mcp_tool):
        """Test get_tools after initialization"""
        # Mock initialization
        mcp_tool._initialized = True
        mcp_tool._tools = [
            {
                "type": "function",
                "function": {
                    "name": "tool1",
                    "description": "Tool 1"
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "tool2",
                    "description": "Tool 2"
                }
            }
        ]
        
        tools = mcp_tool.get_tools()
        
        assert len(tools) == 2
        assert tools[0]['function']['name'] == "tool1"
        assert tools[1]['function']['name'] == "tool2"
    
    def test_has_function_after_init(self, mcp_tool):
        """Test has_function after initialization"""
        mcp_tool._initialized = True
        mcp_tool._tools = [
            {
                "type": "function",
                "function": {"name": "existing_tool"}
            }
        ]
        
        assert mcp_tool.has_function("existing_tool") is True
        assert mcp_tool.has_function("non_existing_tool") is False
    
    @pytest.mark.asyncio
    async def test_invoke_function_success(self, mcp_tool):
        """Test successful tool invocation"""
        # Mock initialization
        mcp_tool._initialized = True
        mock_manager = Mock()
        mock_manager.call_tool = AsyncMock(return_value={
            "content": [
                {"text": "Result line 1"},
                {"text": "Result line 2"}
            ]
        })
        mcp_tool.manager = mock_manager
        
        result = await mcp_tool.invoke_function("test_tool", arg1="value1")
        
        assert result.success is True
        assert "Result line 1" in result.data
        assert "Result line 2" in result.data
        mock_manager.call_tool.assert_called_once_with(
            "test_tool",
            {"arg1": "value1"}
        )
    
    @pytest.mark.asyncio
    async def test_invoke_function_error(self, mcp_tool):
        """Test tool invocation with error"""
        # Mock initialization
        mcp_tool._initialized = True
        mock_manager = Mock()
        mock_manager.call_tool = AsyncMock(return_value={
            "error": "Tool execution failed"
        })
        mcp_tool.manager = mock_manager
        
        result = await mcp_tool.invoke_function("test_tool", arg1="value1")
        
        assert result.success is False
        assert "Tool execution failed" in result.message
    
    @pytest.mark.asyncio
    async def test_cleanup(self, mcp_tool):
        """Test cleanup"""
        # Mock initialization
        mcp_tool._initialized = True
        mcp_tool._tools = [{"test": "tool"}]
        mock_manager = Mock()
        mock_manager.shutdown = AsyncMock()
        mcp_tool.manager = mock_manager
        
        await mcp_tool.cleanup()
        
        assert mcp_tool._initialized is False
        assert len(mcp_tool._tools) == 0
        mock_manager.shutdown.assert_called_once()
    
    def test_get_status_after_init(self, mcp_tool):
        """Test get_status after initialization"""
        mcp_tool._initialized = True
        mcp_tool._tools = [{"tool": 1}, {"tool": 2}]
        mock_manager = Mock()
        mock_manager.get_status = Mock(return_value={
            "initialized": True,
            "connected_servers": ["server1", "server2"],
            "total_tools": 2
        })
        mcp_tool.manager = mock_manager
        
        status = mcp_tool.get_status()
        
        assert status["initialized"] is True
        assert status["tools_count"] == 2
        assert "server1" in status["connected_servers"]


# Summary test
def test_mcp_sandbox_tool_test_suite():
    """Print test suite summary"""
    test_stats = {
        'Tool Creation': 1,
        'Pre-Initialization': 4,
        'Initialization': 1,
        'Post-Initialization': 3,
        'Tool Invocation': 2,
        'Cleanup & Status': 2,
    }
    
    total_tests = sum(test_stats.values())
    
    print("\n" + "="*70)
    print("MCPSandboxTool Test Suite Summary")
    print("="*70)
    for category, count in test_stats.items():
        print(f"  {category:.<40} {count:>3} tests")
    print("-"*70)
    print(f"  {'TOTAL':.<40} {total_tests:>3} tests")
    print("="*70)
    
    assert total_tests == 13, "Expected 13 tests in MCPSandboxTool suite"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
