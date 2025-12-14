"""
Standalone HTTP MCP Server for Employee Data

FastAPI-based MCP server that validates Okta tokens on every request.

Usage:
    uvicorn mcp_server.main:app --host 0.0.0.0 --port 8001

Environment:
    OKTA_DOMAIN - Okta tenant domain
    OKTA_AUTHORIZATION_SERVER_ID - Authorization server ID
    OKTA_AUDIENCE - Expected token audience
    PORT - Server port (default: 8001)
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from mcp_server.employees_mcp import EmployeesMCP
from mcp_server.auth.okta_validator import validate_authorization_header, get_validator
from mcp_server.mcp_protocol import (
    MCPProtocolHandler,
    MCPSessionManager,
    MCP_PROTOCOL_VERSION,
    session_manager,
)

# Load environment variables
load_dotenv()

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validate required environment variables
required_env_vars = ["OKTA_DOMAIN"]
for var in required_env_vars:
    if not os.getenv(var):
        logger.error(f"Required environment variable not set: {var}")
        sys.exit(1)

logger.info("=" * 80)
logger.info("Okta Sample Employee MCP Server")
logger.info("=" * 80)
logger.info(f"Okta Domain: {os.getenv('OKTA_DOMAIN')}")
logger.info(f"Authorization Server ID: {os.getenv('OKTA_AUTHORIZATION_SERVER_ID', 'employee-mcp-server')}")
logger.info("Note: Audience and other config auto-discovered from OAuth 2.0 endpoint")
logger.info("=" * 80)

# Initialize MCP server globally
employees_mcp = EmployeesMCP()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    logger.info("MCP server startup completed")
    try:
        # Test Okta token validator initialization
        validator = get_validator()
        logger.info(f"Okta token validator initialized: {validator.__class__.__name__}")
    except Exception as e:
        logger.error(f"Failed to initialize Okta token validator: {e}")
        logger.warning("Server will reject all requests until Okta is properly configured")
    
    yield
    
    # Shutdown
    logger.info("MCP server shutting down")


# Create FastAPI app
app = FastAPI(
    title="Okta Sample Employee MCP Server",
    description="Standalone HTTP MCP server for employee data with Okta token validation",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ToolCallRequest(BaseModel):
    """Request to call an MCP tool"""
    tool_name: str
    arguments: dict = {}


class ToolCallResponse(BaseModel):
    """Response from MCP tool call"""
    result: dict
    token_info: Optional[dict] = None


# Routes

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "okta-sample-employee-mcp-server",
        "version": "1.0.0"
    }


@app.get("/tools")
async def list_tools(authorization: Optional[str] = Header(None)):
    """
    List available MCP tools.
    
    Requires valid Okta token in Authorization header.
    """
    # Validate token
    token_claims = await validate_authorization_header(authorization)
    if not token_claims:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    
    tools = employees_mcp.list_tools()
    
    return {
        "tools": tools,
        "count": len(tools),
        "token_info": {
            "sub": token_claims.get("sub"),
            "scope": token_claims.get("scope"),
            "exp": token_claims.get("exp")
        }
    }


@app.post("/call_tool")
async def call_tool(
    request: ToolCallRequest,
    authorization: Optional[str] = Header(None)
) -> ToolCallResponse:
    """
    Call an MCP tool.
    
    Requires valid Okta token in Authorization header.
    
    Example request:
    ```
    POST /call_tool
    Authorization: Bearer <okta_mcp_token>
    
    {
        "tool_name": "list_employees",
        "arguments": {
            "status_filter": "Active"
        }
    }
    ```
    
    Returns:
    ```
    {
        "result": {
            "employees": [...],
            "total_count": 15,
            "status_filter": "Active"
        },
        "token_info": {
            "sub": "user_id",
            "scope": "mcp:read",
            "exp": 1234567890
        }
    }
    ```
    """
    try:
        # STEP 1: Validate Okta token
        logger.info(f"Tool call request: {request.tool_name}")
        
        token_claims = await validate_authorization_header(authorization)
        if not token_claims:
            logger.warning(f"Invalid token for tool: {request.tool_name}")
            raise HTTPException(status_code=401, detail="Invalid or missing token")
        
        logger.info(f"Token validated for user: {token_claims.get('sub')}")
        logger.debug(f"Token scope: {token_claims.get('scope')}")
        
        # STEP 2: Call the tool with validated claims
        logger.info(f"Calling tool: {request.tool_name} with args: {request.arguments}")
        
        result = await employees_mcp.call_tool(
            tool_name=request.tool_name,
            arguments=request.arguments,
            token_claims=token_claims
        )
        
        # STEP 3: Return result with token info
        logger.info(f"Tool executed successfully: {request.tool_name}")
        
        return ToolCallResponse(
            result=result,
            token_info={
                "sub": token_claims.get("sub"),
                "scope": token_claims.get("scope"),
                "exp": token_claims.get("exp"),
                "aud": token_claims.get("aud")
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calling tool {request.tool_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error calling tool: {str(e)}")


@app.post("/tools/{tool_name}")
async def call_tool_by_name(
    tool_name: str,
    arguments: dict = {},
    authorization: Optional[str] = Header(None)
) -> ToolCallResponse:
    """
    Call a specific MCP tool by name (alternative endpoint).
    
    Requires valid Okta token in Authorization header.
    
    Example:
    ```
    POST /tools/list_employees
    Authorization: Bearer <okta_mcp_token>
    
    {
        "status_filter": "Active"
    }
    ```
    """
    # Use the main call_tool handler
    return await call_tool(
        ToolCallRequest(tool_name=tool_name, arguments=arguments),
        authorization=authorization
    )


@app.post("/mcp")
async def mcp_streamable_http_post(
    request: Request,
    authorization: Optional[str] = Header(None),
    mcp_session_id: Optional[str] = Header(None),
    mcp_protocol_version: Optional[str] = Header(None),
):
    """
    MCP Streamable HTTP transport - POST endpoint
    Handles JSON-RPC requests and returns JSON or SSE stream.
    
    Spec: https://modelcontextprotocol.io/specification/2025-06-18/basic/transports
    """
    try:
        # Validate protocol version
        if mcp_protocol_version and mcp_protocol_version != MCP_PROTOCOL_VERSION:
            logger.warning(f"Unsupported protocol version: {mcp_protocol_version}")
            return JSONResponse(
                status_code=400,
                content=MCPProtocolHandler.error_response(
                    -32700,
                    f"Unsupported protocol version: {mcp_protocol_version}",
                ),
            )

        # Parse JSON-RPC request
        try:
            body = await request.json()
        except Exception as e:
            logger.error(f"Invalid JSON in MCP request: {e}")
            return JSONResponse(
                status_code=400,
                content=MCPProtocolHandler.error_response(
                    -32700, "Invalid JSON-RPC request"
                ),
            )

        # Validate token for non-initialization requests
        if body.get("method") != "initialize":
            token_claims = await validate_authorization_header(authorization)
            if not token_claims:
                logger.warning("Invalid token for MCP request")
                return JSONResponse(
                    status_code=401,
                    content=MCPProtocolHandler.error_response(
                        -32001, "Unauthorized"
                    ),
                )
        else:
            token_claims = None

        # Handle session management
        if mcp_session_id:
            if not session_manager.validate_session(mcp_session_id):
                logger.warning(f"Invalid session: {mcp_session_id}")
                return JSONResponse(status_code=404, content={})
            session_manager.update_session(mcp_session_id)
        elif body.get("method") == "initialize":
            # Create new session for initialize
            mcp_session_id = session_manager.create_session()

        # Handle JSON-RPC methods
        method = body.get("method")
        request_id = body.get("id")

        if method == "initialize":
            # Initialize request
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
            response = MCPProtocolHandler.create_response(result, request_id)
            return JSONResponse(
                status_code=200,
                content=response.to_dict(),
                headers={"Mcp-Session-Id": mcp_session_id} if mcp_session_id else {},
            )

        elif method == "tools/call":
            # Tool call request
            try:
                tool_name, arguments, _ = MCPProtocolHandler.jsonrpc_to_tool_call(
                    body
                )
            except ValueError as e:
                logger.error(f"Invalid tool call: {e}")
                return JSONResponse(
                    status_code=400,
                    content=MCPProtocolHandler.error_response(-32602, str(e), request_id),
                )

            # Execute tool
            try:
                result = await employees_mcp.call_tool(
                    tool_name, arguments, token_claims
                )
                response = MCPProtocolHandler.create_response(result, request_id)
                return JSONResponse(
                    status_code=200,
                    content=response.to_dict(),
                    headers={"Mcp-Session-Id": mcp_session_id} if mcp_session_id else {},
                )
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                return JSONResponse(
                    status_code=200,
                    content=MCPProtocolHandler.error_response(
                        -32603, str(e), request_id
                    ),
                    headers={"Mcp-Session-Id": mcp_session_id}
                    if mcp_session_id
                    else {},
                )

        elif method == "tools/list":
            # List tools request
            tools = employees_mcp.list_tools()
            result = {"tools": tools}
            response = MCPProtocolHandler.create_response(result, request_id)
            return JSONResponse(
                status_code=200,
                content=response.to_dict(),
                headers={"Mcp-Session-Id": mcp_session_id} if mcp_session_id else {},
            )

        else:
            logger.warning(f"Unknown JSON-RPC method: {method}")
            return JSONResponse(
                status_code=200,
                content=MCPProtocolHandler.error_response(
                    -32601, f"Unknown method: {method}", request_id
                ),
                headers={"Mcp-Session-Id": mcp_session_id} if mcp_session_id else {},
            )

    except Exception as e:
        logger.error(f"Unhandled error in MCP POST: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=MCPProtocolHandler.error_response(
                -32603, "Internal server error"
            ),
        )


@app.get("/mcp")
async def mcp_streamable_http_get(
    authorization: Optional[str] = Header(None),
    mcp_session_id: Optional[str] = Header(None),
):
    """
    MCP Streamable HTTP transport - GET endpoint
    Opens SSE stream for server-to-client messages.
    
    Spec: https://modelcontextprotocol.io/specification/2025-06-18/basic/transports
    """
    try:
        # For now, return 405 Method Not Allowed
        # SSE streaming can be implemented if server-to-client notifications are needed
        return JSONResponse(
            status_code=405,
            content={
                "error": "SSE streaming not currently supported",
                "message": "Use POST for JSON-RPC requests",
            },
        )
    except Exception as e:
        logger.error(f"Error in MCP GET: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": "Internal server error"})


@app.delete("/mcp")
async def mcp_streamable_http_delete(
    mcp_session_id: Optional[str] = Header(None),
):
    """
    MCP Streamable HTTP transport - DELETE endpoint
    Terminate a session.
    
    Spec: https://modelcontextprotocol.io/specification/2025-06-18/basic/transports
    """
    try:
        if mcp_session_id:
            session_manager.terminate_session(mcp_session_id)
            logger.info(f"Session terminated: {mcp_session_id}")
            return JSONResponse(status_code=200, content={"status": "terminated"})
        else:
            return JSONResponse(
                status_code=400,
                content={"error": "Mcp-Session-Id header required"},
            )
    except Exception as e:
        logger.error(f"Error in MCP DELETE: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": "Internal server error"})


# Error handlers

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "path": str(request.url.path)
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info("MCP server started")
    logger.info(f"Available tools: {len(employees_mcp.list_tools())}")
    for tool in employees_mcp.list_tools():
        logger.info(f"  - {tool['name']}: {tool['description']}")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8001))
    environment = os.getenv("ENVIRONMENT", "development")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=(environment == "development"),
        log_level=log_level.lower()
    )
