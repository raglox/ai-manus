"""
MCP Connection Manager

Manages MCP server connections and provides high-level interface
for the agent to discover and use external tools.

Features:
- Load server configurations from mcp_config.json
- Automatic connection management
- Dynamic tool discovery
- Tool schema conversion to OpenAI function format

Author: Senior Systems Architect
Date: 2025-12-26
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.infrastructure.external.mcp_client import (
    MCPClient,
    MCPServerConfig,
    MCPTool
)
from app.domain.external.sandbox import Sandbox


logger = logging.getLogger(__name__)


class McpConnectionManager:
    """
    High-level manager for MCP server connections
    """
    
    def __init__(
        self,
        sandbox: Sandbox,
        session_id: str,
        config_path: Optional[str] = None
    ):
        self.sandbox = sandbox
        self.session_id = session_id
        self.config_path = config_path or "mcp_config.json"
        self.client = MCPClient(sandbox, session_id)
        self.logger = logging.getLogger("McpConnectionManager")
        self._initialized = False
    
    async def initialize(self) -> bool:
        """
        Initialize the manager by loading config and connecting to servers
        
        Returns:
            bool: True if at least one server connected successfully
        """
        if self._initialized:
            self.logger.warning("Already initialized")
            return True
        
        self.logger.info("Initializing MCP Connection Manager")
        
        # Load configuration
        servers = self._load_config()
        if not servers:
            self.logger.warning("No MCP servers configured")
            return False
        
        # Connect to each server
        success_count = 0
        for server_config in servers:
            try:
                success = await self.client.connect_server(server_config)
                if success:
                    success_count += 1
                    self.logger.info(f"✅ Connected to {server_config.name}")
                else:
                    self.logger.error(f"❌ Failed to connect to {server_config.name}")
            except Exception as e:
                self.logger.error(
                    f"Error connecting to {server_config.name}: {e}",
                    exc_info=True
                )
        
        self._initialized = success_count > 0
        
        if self._initialized:
            self.logger.info(
                f"Initialized with {success_count}/{len(servers)} servers"
            )
        else:
            self.logger.error("Failed to connect to any MCP servers")
        
        return self._initialized
    
    def _load_config(self) -> List[MCPServerConfig]:
        """
        Load MCP server configurations from config file
        
        Returns:
            List of server configurations
        """
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            self.logger.warning(f"Config file not found: {self.config_path}")
            return []
        
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            servers = []
            for server_name, server_info in config_data.get("mcpServers", {}).items():
                servers.append(MCPServerConfig(
                    name=server_name,
                    command=server_info["command"],
                    args=server_info.get("args", []),
                    env=server_info.get("env", {}),
                    description=server_info.get("description")
                ))
            
            self.logger.info(f"Loaded {len(servers)} server configurations")
            return servers
            
        except Exception as e:
            self.logger.error(f"Error loading config: {e}", exc_info=True)
            return []
    
    def get_available_tools(self) -> List[MCPTool]:
        """
        Get all available tools from connected servers
        
        Returns:
            List of MCP tools
        """
        if not self._initialized:
            self.logger.warning("Manager not initialized")
            return []
        
        return self.client.get_all_tools()
    
    def convert_tools_to_openai_format(self) -> List[Dict[str, Any]]:
        """
        Convert MCP tools to OpenAI function calling format
        
        Returns:
            List of OpenAI function definitions
        """
        tools = self.get_available_tools()
        openai_tools = []
        
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or f"Tool from {tool.server_name}",
                    "parameters": tool.input_schema
                }
            })
        
        self.logger.debug(f"Converted {len(openai_tools)} tools to OpenAI format")
        return openai_tools
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call an MCP tool
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        if not self._initialized:
            return {"error": "Manager not initialized"}
        
        return await self.client.call_tool(tool_name, arguments)
    
    def get_tool_info(self, tool_name: str) -> Optional[MCPTool]:
        """Get detailed information about a specific tool"""
        return self.client.get_tool_by_name(tool_name)
    
    async def shutdown(self):
        """Shutdown all connections"""
        self.logger.info("Shutting down MCP Connection Manager")
        await self.client.disconnect_all()
        self._initialized = False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of all connections
        
        Returns:
            Status information
        """
        return {
            "initialized": self._initialized,
            "connected_servers": list(self.client.connections.keys()),
            "total_tools": len(self.get_available_tools()),
            "tools_by_server": {
                name: len(conn.tools)
                for name, conn in self.client.connections.items()
            }
        }


def create_default_config(output_path: str = "mcp_config.json"):
    """
    Create a default MCP configuration file
    
    Args:
        output_path: Path to write the config file
    """
    default_config = {
        "mcpServers": {
            "filesystem": {
                "description": "File system operations",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
                "env": {}
            },
            "echo": {
                "description": "Simple echo server for testing",
                "command": "python3",
                "args": ["-c", """
import sys
import json

# Simple MCP echo server
while True:
    try:
        line = sys.stdin.readline()
        if not line:
            break
        
        request = json.loads(line)
        request_id = request.get('id')
        method = request.get('method')
        params = request.get('params', {})
        
        if method == 'initialize':
            response = {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': {
                    'protocolVersion': '2024-11-05',
                    'capabilities': {'tools': {}},
                    'serverInfo': {'name': 'echo', 'version': '1.0.0'}
                }
            }
        elif method == 'tools/list':
            response = {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': {
                    'tools': [{
                        'name': 'echo',
                        'description': 'Echo back the input',
                        'inputSchema': {
                            'type': 'object',
                            'properties': {
                                'message': {'type': 'string', 'description': 'Message to echo'}
                            },
                            'required': ['message']
                        }
                    }]
                }
            }
        elif method == 'tools/call':
            tool_name = params.get('name')
            arguments = params.get('arguments', {})
            response = {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': {
                    'content': [{
                        'type': 'text',
                        'text': f'Echo: {arguments.get(\"message\", \"\")}'
                    }]
                }
            }
        else:
            response = {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': {}
            }
        
        print(json.dumps(response), flush=True)
    except Exception as e:
        error_response = {
            'jsonrpc': '2.0',
            'id': request_id if 'request_id' in locals() else None,
            'error': {'code': -32603, 'message': str(e)}
        }
        print(json.dumps(error_response), flush=True)
"""],
                "env": {"PYTHONUNBUFFERED": "1"}
            }
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    logger.info(f"Created default MCP config at {output_path}")
    
    return output_path
