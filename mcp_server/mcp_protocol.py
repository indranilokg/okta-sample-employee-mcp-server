"""
MCP JSON-RPC Protocol Handler

Implements MCP Streamable HTTP and stdio transports according to:
https://modelcontextprotocol.io/specification/2025-06-18/basic/transports
"""

import json
import logging
from typing import Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass, asdict
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# MCP Protocol version
MCP_PROTOCOL_VERSION = "2025-06-18"


@dataclass
class JsonRpcRequest:
    """JSON-RPC 2.0 Request"""
    jsonrpc: str = "2.0"
    method: str = None
    params: Dict[str, Any] = None
    id: Optional[str] = None

    def to_dict(self):
        data = {"jsonrpc": self.jsonrpc, "method": self.method}
        if self.params:
            data["params"] = self.params
        if self.id is not None:
            data["id"] = self.id
        return data


@dataclass
class JsonRpcResponse:
    """JSON-RPC 2.0 Response"""
    jsonrpc: str = "2.0"
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[str] = None

    def to_dict(self):
        """Convert to dict, excluding None fields per JSON-RPC 2.0 spec"""
        data = {"jsonrpc": self.jsonrpc}
        if self.result is not None:
            data["result"] = self.result
        if self.error is not None:
            data["error"] = self.error
        if self.id is not None:
            data["id"] = self.id
        return data


@dataclass
class JsonRpcNotification:
    """JSON-RPC 2.0 Notification (no id)"""
    jsonrpc: str = "2.0"
    method: str = None
    params: Dict[str, Any] = None

    def to_dict(self):
        data = {"jsonrpc": self.jsonrpc, "method": self.method}
        if self.params:
            data["params"] = self.params
        return data


class MCPProtocolHandler:
    """
    Handles MCP JSON-RPC protocol conversion.
    Converts between tool calls and JSON-RPC format.
    """

    @staticmethod
    def parse_request(data: Dict[str, Any]) -> JsonRpcRequest:
        """Parse incoming JSON-RPC request"""
        return JsonRpcRequest(
            method=data.get("method"),
            params=data.get("params"),
            id=data.get("id"),
        )

    @staticmethod
    def create_response(
        result: Dict[str, Any],
        request_id: Optional[str],
        error: Optional[Dict[str, Any]] = None,
    ) -> JsonRpcResponse:
        """Create JSON-RPC response"""
        return JsonRpcResponse(
            result=result if not error else None,
            error=error,
            id=request_id,
        )

    @staticmethod
    def create_notification(
        method: str, params: Dict[str, Any] = None
    ) -> JsonRpcNotification:
        """Create JSON-RPC notification"""
        return JsonRpcNotification(method=method, params=params)

    @staticmethod
    def tool_call_to_jsonrpc(
        tool_name: str, arguments: Dict[str, Any], request_id: str = None
    ) -> Dict[str, Any]:
        """Convert tool call to JSON-RPC request format"""
        request = JsonRpcRequest(
            method="tools/call",
            params={"tool_name": tool_name, "arguments": arguments},
            id=request_id or str(uuid.uuid4()),
        )
        return request.to_dict()

    @staticmethod
    def jsonrpc_to_tool_call(request_data: Dict[str, Any]) -> tuple:
        """Convert JSON-RPC request to tool call format"""
        if request_data.get("method") != "tools/call":
            raise ValueError(f"Unknown method: {request_data.get('method')}")

        params = request_data.get("params", {})
        return (
            params.get("tool_name"),
            params.get("arguments", {}),
            request_data.get("id"),
        )

    @staticmethod
    def error_response(
        error_code: int, error_message: str, request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create JSON-RPC error response"""
        return {
            "jsonrpc": "2.0",
            "error": {"code": error_code, "message": error_message},
            "id": request_id,
        }


class MCPSessionManager:
    """Manage MCP sessions with session IDs"""

    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self) -> str:
        """Create a new session, return session ID"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
        }
        logger.info(f"Created session: {session_id}")
        return session_id

    def validate_session(self, session_id: str) -> bool:
        """Check if session exists"""
        return session_id in self.sessions

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        return self.sessions.get(session_id)

    def update_session(self, session_id: str):
        """Update session last activity time"""
        if session_id in self.sessions:
            self.sessions[session_id]["last_activity"] = (
                datetime.utcnow().isoformat()
            )

    def terminate_session(self, session_id: str):
        """Terminate a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Terminated session: {session_id}")


# Global session manager
session_manager = MCPSessionManager()
