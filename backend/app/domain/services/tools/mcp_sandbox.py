"""
MCP Sandbox Tool - MCP integration using StatefulDockerSandbox

This tool wraps McpConnectionManager to integrate MCP servers running
inside the Docker sandbox with the AI-Manus agent tool system.

Differences from MCPTool (app/domain/services/tools/mcp.py):
- MCPTool: Uses official mcp library, runs on host
- MCPSandboxTool: Uses McpConnectionManager, runs in Docker sandbox

Author: Senior Systems Architect
Date: 2025-12-26
"""

import logging
from typing import Dict, Any, List, Optional

from app.domain.services.tools.base import BaseTool
from app.domain.models.tool_result import ToolResult
from app.domain.services.mcp_manager import McpConnectionManager
from app.domain.external.sandbox import Sandbox


logger = logging.getLogger(__name__)


class MCPSandboxTool(BaseTool):
    """
    MCP Tool that runs servers inside Docker sandbox for security isolation
    """
    
    name = "mcp_sandbox"
    
    def __init__(
        self,
        sandbox: Sandbox,
        session_id: str,
        config_path: str = "mcp_config.json"
    ):
        super().__init__()
        self.sandbox = sandbox
        self.session_id = session_id
        self.config_path = config_path
        self.manager: Optional[McpConnectionManager] = None
        self._initialized = False
        self._tools = []
        logger.info(f"MCPSandboxTool created for session {session_id}")
    
    async def initialize(self) -> bool:
        """
        Initialize the MCP manager and connect to all configured servers
        
        Returns:
            bool: True if at least one server connected successfully
        """
        if self._initialized:
            logger.warning("MCPSandboxTool already initialized")
            return True
        
        try:
            logger.info("Initializing MCPSandboxTool...")
            
            # Create manager
            self.manager = McpConnectionManager(
                sandbox=self.sandbox,
                session_id=self.session_id,
                config_path=self.config_path
            )
            
            # Initialize (connects to all servers)
            success = await self.manager.initialize()
            
            if not success:
                logger.error("Failed to connect to any MCP servers")
                return False
            
            # Get tools in OpenAI format
            self._tools = self.manager.convert_tools_to_openai_format()
            
            self._initialized = True
            
            logger.info(
                f"MCPSandboxTool initialized successfully with {len(self._tools)} tools"
            )
            
            # Log discovered tools
            for tool in self._tools:
                tool_name = tool['function']['name']
                tool_desc = tool['function']['description']
                logger.debug(f"  - {tool_name}: {tool_desc}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize MCPSandboxTool: {e}", exc_info=True)
            return False
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get all available MCP tools in OpenAI function format
        
        Returns:
            List of tool definitions
        """
        if not self._initialized:
            logger.warning("MCPSandboxTool not initialized, returning empty tools list")
            return []
        
        return self._tools
    
    def has_function(self, function_name: str) -> bool:
        """
        Check if a specific function exists
        
        Args:
            function_name: Name of the function to check
            
        Returns:
            bool: True if function exists
        """
        if not self._initialized:
            return False
        
        for tool in self._tools:
            if tool['function']['name'] == function_name:
                return True
        
        return False
    
    async def invoke_function(self, function_name: str, **kwargs) -> ToolResult:
        """
        Invoke an MCP tool function
        
        Args:
            function_name: Name of the tool to call
            **kwargs: Tool arguments
            
        Returns:
            ToolResult with execution result
        """
        if not self._initialized:
            return ToolResult(
                success=False,
                message="MCPSandboxTool not initialized. Call initialize() first."
            )
        
        try:
            logger.info(f"Invoking MCP tool: {function_name}")
            logger.debug(f"Arguments: {kwargs}")
            
            # Call tool via manager
            result = await self.manager.call_tool(function_name, kwargs)
            
            if "error" in result:
                error_msg = result["error"]
                logger.error(f"MCP tool {function_name} failed: {error_msg}")
                return ToolResult(
                    success=False,
                    message=f"MCP tool execution failed: {error_msg}"
                )
            
            # Extract content from result
            content = []
            if "content" in result:
                for item in result["content"]:
                    if "text" in item:
                        content.append(item["text"])
                    else:
                        content.append(str(item))
            
            result_text = "\n".join(content) if content else "Tool executed successfully"
            
            logger.info(f"MCP tool {function_name} executed successfully")
            
            return ToolResult(
                success=True,
                data=result_text
            )
            
        except Exception as e:
            logger.error(
                f"Exception calling MCP tool {function_name}: {e}",
                exc_info=True
            )
            return ToolResult(
                success=False,
                message=f"MCP tool execution failed: {str(e)}"
            )
    
    async def cleanup(self):
        """Clean up MCP connections"""
        if self.manager:
            logger.info("Cleaning up MCPSandboxTool...")
            await self.manager.shutdown()
            self._initialized = False
            self._tools = []
            logger.info("MCPSandboxTool cleaned up successfully")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of MCP tool
        
        Returns:
            Status information
        """
        if not self._initialized or not self.manager:
            return {
                "initialized": False,
                "tools_count": 0,
                "servers": []
            }
        
        status = self.manager.get_status()
        status["tools_count"] = len(self._tools)
        
        return status
