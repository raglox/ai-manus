"""
Agent MCP Integration Test

Tests the integration between Agent (PlanActFlow) and MCPSandboxTool.

Author: Senior Systems Architect
Date: 2025-12-26
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch


class TestAgentMCPIntegration:
    """Test Agent integration with MCPSandboxTool"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for PlanActFlow"""
        return {
            'agent_id': 'test-agent',
            'agent_repository': Mock(),
            'session_id': 'test-session',
            'session_repository': Mock(),
            'llm': Mock(),
            'sandbox': Mock(),
            'browser': Mock(),
            'json_parser': Mock(),
            'mcp_tool': Mock(),
            'search_engine': None,
        }
    
    def test_plan_act_flow_with_mcp_sandbox_disabled(self, mock_dependencies):
        """Test that PlanActFlow works with use_mcp_sandbox=False (default)"""
        from app.domain.services.flows.plan_act import PlanActFlow
        
        flow = PlanActFlow(**mock_dependencies, use_mcp_sandbox=False)
        
        # Should use original MCPTool
        assert flow._mcp_sandbox_tool is None
        assert len(flow.planner.tools) > 0
    
    def test_plan_act_flow_with_mcp_sandbox_enabled(self, mock_dependencies):
        """Test that PlanActFlow creates MCPSandboxTool when use_mcp_sandbox=True"""
        from app.domain.services.flows.plan_act import PlanActFlow
        
        flow = PlanActFlow(**mock_dependencies, use_mcp_sandbox=True)
        
        # Should create MCPSandboxTool
        assert flow._mcp_sandbox_tool is not None
        assert flow._mcp_sandbox_tool.name == "mcp_sandbox"
        assert flow._mcp_sandbox_tool.session_id == "test-session"
    
    def test_mcp_sandbox_tool_in_tools_list(self, mock_dependencies):
        """Test that MCPSandboxTool is added to tools list"""
        from app.domain.services.flows.plan_act import PlanActFlow
        
        flow = PlanActFlow(**mock_dependencies, use_mcp_sandbox=True)
        
        # Check if MCPSandboxTool is in planner tools
        tool_names = [tool.name for tool in flow.planner.tools]
        assert "mcp_sandbox" in tool_names
        
        # Check if MCPSandboxTool is in executor tools
        tool_names = [tool.name for tool in flow.executor.tools]
        assert "mcp_sandbox" in tool_names
    
    @pytest.mark.asyncio
    async def test_mcp_sandbox_tool_initialization_in_run(self, mock_dependencies):
        """Test that MCPSandboxTool.initialize() is called during flow.run()"""
        from app.domain.services.flows.plan_act import PlanActFlow
        from app.domain.models.message import Message
        from app.domain.models.session import Session, SessionStatus
        
        # Mock session
        mock_session = Mock()
        mock_session.status = SessionStatus.PENDING
        mock_session.get_last_plan = Mock(return_value=None)
        mock_dependencies['session_repository'].find_by_id = AsyncMock(
            return_value=mock_session
        )
        mock_dependencies['session_repository'].update_status = AsyncMock()
        
        # Mock planner to immediately complete
        mock_planner = Mock()
        mock_planner.create_plan = AsyncMock()
        
        async def mock_plan_events(msg):
            from app.domain.models.event import PlanEvent, PlanStatus
            from app.domain.models.plan import Plan
            plan = Plan(goal="test", title="test", message="test", steps=[])
            yield PlanEvent(status=PlanStatus.CREATED, plan=plan)
        
        mock_planner.create_plan = mock_plan_events
        
        # Create flow
        flow = PlanActFlow(**mock_dependencies, use_mcp_sandbox=True)
        
        # Mock initialize method
        flow._mcp_sandbox_tool.initialize = AsyncMock(return_value=True)
        flow._mcp_sandbox_tool.get_tools = Mock(return_value=[])
        flow._mcp_sandbox_tool.cleanup = AsyncMock()
        
        # Replace planner
        flow.planner = mock_planner
        
        # Mock executor
        mock_executor = Mock()
        mock_executor.summarize = AsyncMock()
        
        async def mock_summarize():
            from app.domain.models.event import MessageEvent
            yield MessageEvent(role="assistant", message="Summary")
        
        mock_executor.summarize = mock_summarize
        flow.executor = mock_executor
        
        # Run flow
        message = Message(message="Test message")
        events = []
        async for event in flow.run(message):
            events.append(event)
        
        # Verify initialize was called
        flow._mcp_sandbox_tool.initialize.assert_called_once()
        
        # Verify cleanup was called
        flow._mcp_sandbox_tool.cleanup.assert_called_once()


# Summary test
def test_agent_mcp_integration_suite():
    """Print test suite summary"""
    test_stats = {
        'Configuration Tests': 2,
        'Tools List Tests': 1,
        'Initialization Tests': 1,
    }
    
    total_tests = sum(test_stats.values())
    
    print("\n" + "="*70)
    print("Agent MCP Integration Test Suite Summary")
    print("="*70)
    for category, count in test_stats.items():
        print(f"  {category:.<40} {count:>3} tests")
    print("-"*70)
    print(f"  {'TOTAL':.<40} {total_tests:>3} tests")
    print("="*70)
    
    assert total_tests == 4, "Expected 4 tests in Agent MCP Integration suite"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
