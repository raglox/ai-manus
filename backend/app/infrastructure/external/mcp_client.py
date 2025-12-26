"""
MCP Client - Model Context Protocol Client Implementation

This client enables the AI-Manus agent to communicate with external MCP servers
running inside the StatefulSandbox using stdio transport.

Architecture:
- MCP servers run as processes inside Docker sandbox
- Communication via stdin/stdout using JSON-RPC 2.0
- Each server connection is isolated and stateful
- Supports multiple concurrent server connections

Reference: https://modelcontextprotocol.io/

Author: Senior Systems Architect
Date: 2025-12-26
"""

import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging

from app.domain.external.sandbox import Sandbox


logger = logging.getLogger(__name__)


class MCPMessageType(Enum):
    """MCP JSON-RPC 2.0 message types"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server"""
    name: str
    command: str
    args: List[str]
    env: Dict[str, str] = None
    description: Optional[str] = None
    
    def __post_init__(self):
        if self.env is None:
            self.env = {}
    

@dataclass
class MCPTool:
    """Represents an MCP tool with its schema"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str


class MCPConnection:
    """Represents an active connection to an MCP server"""
    
    def __init__(
        self,
        server_config: MCPServerConfig,
        sandbox: Sandbox,
        session_id: str
    ):
        self.config = server_config
        self.sandbox = sandbox
        self.session_id = session_id
        self.process_id: Optional[int] = None
        self.is_connected = False
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.tools: List[MCPTool] = []
        self.logger = logging.getLogger(f"MCPConnection.{server_config.name}")
        
    async def connect(self) -> bool:
        """
        Start the MCP server process inside the sandbox
        
        Returns:
            bool: True if connection successful
        """
        try:
            self.logger.info(f"Starting MCP server: {self.config.name}")
            
            # Build command with environment variables
            env_prefix = " ".join([f"{k}={v}" for k, v in self.config.env.items()])
            full_command = f"{env_prefix} {self.config.command} {' '.join(self.config.args)}"
            
            self.logger.debug(f"Command: {full_command}")
            
            # Start server process in background
            result = await self.sandbox.run_in_background(
                command=full_command,
                session_id=self.session_id
            )
            
            if result.get('exit_code') != 0:
                self.logger.error(f"Failed to start server: {result.get('stderr')}")
                return False
                
            self.process_id = result.get('pid')
            self.logger.info(f"Server started with PID: {self.process_id}")
            
            # Wait for server to initialize
            await asyncio.sleep(1)
            
            # Send initialize request
            init_response = await self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "ai-manus",
                    "version": "1.0.0"
                }
            })
            
            if not init_response or "error" in init_response:
                self.logger.error(f"Initialize failed: {init_response}")
                return False
                
            self.is_connected = True
            self.logger.info(f"Successfully connected to {self.config.name}")
            
            # List available tools
            await self._list_tools()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Connection error: {e}", exc_info=True)
            return False
    
    async def _send_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a JSON-RPC 2.0 request to the MCP server
        
        Args:
            method: The method name (e.g., "tools/list", "tools/call")
            params: Method parameters
            
        Returns:
            Response from server
        """
        request_id = str(uuid.uuid4())
        
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }
        
        try:
            # Write request to stdin
            request_json = json.dumps(request) + "\n"
            self.logger.debug(f"Sending request: {method} (ID: {request_id[:8]})")
            
            # Use sandbox to send to process stdin
            write_result = await self.sandbox.execute_command(
                f'echo \'{request_json}\' > /proc/{self.process_id}/fd/0',
                session_id=self.session_id
            )
            
            if write_result.get('exit_code') != 0:
                self.logger.error(f"Failed to write to stdin: {write_result}")
                return {"error": "Failed to send request"}
            
            # Read response from stdout
            # Note: In production, we'd have a persistent reader task
            # For now, read from the background process output file
            await asyncio.sleep(0.5)  # Give server time to respond
            
            read_result = await self.sandbox.execute_command(
                f'tail -1 /tmp/bg_{self.process_id}.out',
                session_id=self.session_id
            )
            
            if read_result.get('exit_code') != 0:
                self.logger.error(f"Failed to read response: {read_result}")
                return {"error": "Failed to read response"}
            
            response_text = read_result.get('stdout', '').strip()
            if not response_text:
                return {"error": "Empty response"}
                
            response = json.loads(response_text)
            
            if "error" in response:
                self.logger.error(f"Server error: {response['error']}")
                
            return response
            
        except Exception as e:
            self.logger.error(f"Request error: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def _list_tools(self) -> bool:
        """
        List available tools from the MCP server
        
        Returns:
            bool: True if tools were listed successfully
        """
        try:
            response = await self._send_request("tools/list")
            
            if "error" in response:
                self.logger.error(f"Failed to list tools: {response['error']}")
                return False
            
            tools_data = response.get("result", {}).get("tools", [])
            
            self.tools = [
                MCPTool(
                    name=tool["name"],
                    description=tool.get("description", ""),
                    input_schema=tool.get("inputSchema", {}),
                    server_name=self.config.name
                )
                for tool in tools_data
            ]
            
            self.logger.info(f"Discovered {len(self.tools)} tools from {self.config.name}")
            for tool in self.tools:
                self.logger.debug(f"  - {tool.name}: {tool.description}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error listing tools: {e}", exc_info=True)
            return False
    
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
        if not self.is_connected:
            return {"error": "Not connected to server"}
        
        self.logger.info(f"Calling tool: {tool_name}")
        self.logger.debug(f"Arguments: {arguments}")
        
        try:
            response = await self._send_request("tools/call", {
                "name": tool_name,
                "arguments": arguments
            })
            
            if "error" in response:
                self.logger.error(f"Tool call error: {response['error']}")
                return response
            
            result = response.get("result", {})
            self.logger.info(f"Tool {tool_name} executed successfully")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Tool call exception: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if not self.is_connected:
            return
        
        try:
            self.logger.info(f"Disconnecting from {self.config.name}")
            
            # Send shutdown notification
            await self._send_request("shutdown")
            
            # Kill the process
            if self.process_id:
                await self.sandbox.execute_command(
                    f'kill -TERM {self.process_id}',
                    session_id=self.session_id
                )
            
            self.is_connected = False
            self.logger.info("Disconnected successfully")
            
        except Exception as e:
            self.logger.error(f"Disconnect error: {e}", exc_info=True)


class MCPClient:
    """
    Main MCP Client for managing multiple server connections
    """
    
    def __init__(self, sandbox: Sandbox, session_id: str):
        self.sandbox = sandbox
        self.session_id = session_id
        self.connections: Dict[str, MCPConnection] = {}
        self.logger = logging.getLogger("MCPClient")
    
    async def connect_server(self, config: MCPServerConfig) -> bool:
        """
        Connect to an MCP server
        
        Args:
            config: Server configuration
            
        Returns:
            bool: True if connection successful
        """
        if config.name in self.connections:
            self.logger.warning(f"Already connected to {config.name}")
            return True
        
        connection = MCPConnection(config, self.sandbox, self.session_id)
        
        success = await connection.connect()
        if success:
            self.connections[config.name] = connection
            self.logger.info(f"Added connection: {config.name}")
        
        return success
    
    async def disconnect_server(self, server_name: str):
        """Disconnect from a specific server"""
        if server_name in self.connections:
            await self.connections[server_name].disconnect()
            del self.connections[server_name]
            self.logger.info(f"Removed connection: {server_name}")
    
    async def disconnect_all(self):
        """Disconnect from all servers"""
        for server_name in list(self.connections.keys()):
            await self.disconnect_server(server_name)
    
    def get_all_tools(self) -> List[MCPTool]:
        """
        Get all available tools from all connected servers
        
        Returns:
            List of all available MCP tools
        """
        all_tools = []
        for connection in self.connections.values():
            all_tools.extend(connection.tools)
        return all_tools
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call a tool by name (finds the right server automatically)
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        # Find which server has this tool
        for connection in self.connections.values():
            for tool in connection.tools:
                if tool.name == tool_name:
                    return await connection.call_tool(tool_name, arguments)
        
        self.logger.error(f"Tool not found: {tool_name}")
        return {"error": f"Tool '{tool_name}' not found"}
    
    def get_tool_by_name(self, tool_name: str) -> Optional[MCPTool]:
        """Get tool information by name"""
        for tool in self.get_all_tools():
            if tool.name == tool_name:
                return tool
        return None
