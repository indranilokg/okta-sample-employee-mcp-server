"""
MCP stdio Transport

Implements stdio transport for running as a subprocess.
According to: https://modelcontextprotocol.io/specification/2025-06-18/basic/transports

Usage:
    python -m mcp_server.stdio_transport

Environment:
    OKTA_DOMAIN - Okta tenant domain
    OKTA_AUTHORIZATION_SERVER_ID - Authorization server ID
"""

import asyncio
import json
import logging
import sys
import os
from typing import Dict, Any, Optional

from dotenv import load_dotenv

from mcp_server.employees_mcp import EmployeesMCP
from mcp_server.auth.okta_validator import OktaTokenValidator
from mcp_server.mcp_protocol import (
    MCPProtocolHandler,
    MCP_PROTOCOL_VERSION,
)

# Load environment variables
load_dotenv()

# Configure logging to stderr (stdout is reserved for MCP messages)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


class MCPStdioServer:
    """MCP stdio transport server"""

    def __init__(self):
        self.employees_mcp = EmployeesMCP()
        self.validator = OktaTokenValidator()
        self.initialized = False
        logger.info("MCP stdio server initialized")

    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle JSON-RPC request"""
        method = request_data.get("method")
        request_id = request_data.get("id")

        try:
            if method == "initialize":
                return await self.handle_initialize(request_data)

            elif method == "tools/list":
                return await self.handle_list_tools(request_data)

            elif method == "tools/call":
                return await self.handle_tool_call(request_data)

            else:
                logger.warning(f"Unknown method: {method}")
                return MCPProtocolHandler.error_response(
                    -32601, f"Unknown method: {method}", request_id
                )

        except Exception as e:
            logger.error(f"Error handling {method}: {e}", exc_info=True)
            return MCPProtocolHandler.error_response(
                -32603, str(e), request_id
            )

    async def handle_initialize(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request"""
        request_id = request_data.get("id")
        self.initialized = True

        result = {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": False},
            },
            "serverInfo": {
                "name": "Okta Sample Employee MCP Server",
                "version": "1.0.0",
            },
        }

        logger.info("Client initialized")
        return MCPProtocolHandler.create_response(result, request_id).to_dict()

    async def handle_list_tools(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request"""
        request_id = request_data.get("id")

        if not self.initialized:
            return MCPProtocolHandler.error_response(
                -32002, "Not initialized", request_id
            )

        tools = self.employees_mcp.list_tools()
        result = {"tools": tools}

        logger.info(f"Listed {len(tools)} tools")
        return MCPProtocolHandler.create_response(result, request_id).to_dict()

    async def handle_tool_call(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request"""
        request_id = request_data.get("id")

        if not self.initialized:
            return MCPProtocolHandler.error_response(
                -32002, "Not initialized", request_id
            )

        try:
            tool_name, arguments, _ = MCPProtocolHandler.jsonrpc_to_tool_call(
                request_data
            )
        except ValueError as e:
            logger.error(f"Invalid tool call: {e}")
            return MCPProtocolHandler.error_response(-32602, str(e), request_id)

        try:
            # For stdio, we don't have token claims (no HTTP headers)
            # Tools should work without Okta validation in stdio mode
            # Or you can pass minimal claims
            token_claims = {
                "scope": "mcp:read mcp:write",  # Default full scope for stdio
                "sub": "stdio-client",
            }

            result = await self.employees_mcp.call_tool(
                tool_name, arguments, token_claims
            )

            logger.info(f"Executed tool: {tool_name}")
            return MCPProtocolHandler.create_response(result, request_id).to_dict()

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return MCPProtocolHandler.error_response(-32603, str(e), request_id)

    async def run(self):
        """Main server loop - read from stdin, write to stdout"""
        logger.info("Starting MCP stdio server")

        while True:
            try:
                # Read line from stdin
                line = sys.stdin.readline()

                if not line:
                    # EOF - client disconnected
                    logger.info("EOF received, shutting down")
                    break

                # Parse JSON-RPC request
                request_data = json.loads(line.strip())
                logger.debug(f"Received request: {request_data.get('method')}")

                # Handle request
                response = await self.handle_request(request_data)

                # Write response to stdout
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
                logger.debug(f"Sent response for: {request_data.get('method')}")

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                error = MCPProtocolHandler.error_response(
                    -32700, "Parse error"
                )
                sys.stdout.write(json.dumps(error) + "\n")
                sys.stdout.flush()

            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                error = MCPProtocolHandler.error_response(
                    -32603, "Internal server error"
                )
                sys.stdout.write(json.dumps(error) + "\n")
                sys.stdout.flush()


async def main():
    """Entry point for stdio transport"""
    server = MCPStdioServer()
    await server.run()


if __name__ == "__main__":
    # Validate required environment variables
    if not os.getenv("OKTA_DOMAIN"):
        logger.error("OKTA_DOMAIN environment variable is required")
        sys.exit(1)

    logger.info(
        f"Okta Domain: {os.getenv('OKTA_DOMAIN')}"
    )
    logger.info(
        f"Auth Server: {os.getenv('OKTA_AUTHORIZATION_SERVER_ID', 'employee-mcp-server')}"
    )

    asyncio.run(main())
