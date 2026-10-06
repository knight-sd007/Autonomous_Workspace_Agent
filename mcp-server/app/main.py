"""
FastAPI Entrypoint for Model Context Protocol (MCP) Server.
"""

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import hmac
import os
from app.server import WorkspaceMCPServer

app = FastAPI(
    title="P07 MCP Server",
    version="1.0.0",
    docs_url=None,
    redoc_url=None
)

server = WorkspaceMCPServer()


def verify_service_key(provided_key: Optional[str]) -> bool:
    expected_key = os.getenv("INTERNAL_SERVICE_KEY", "p07_dev_internal_key")
    if not provided_key:
        return False
    return hmac.compare_digest(provided_key.strip(), expected_key.strip())


class ToolCallRequest(BaseModel):
    name: str = Field(..., min_length=1)
    arguments: Dict[str, Any] = Field(default_factory=dict)


class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None


@app.get("/health")
async def health_check():
    return {
        "status": "Healthy",
        "service": "P07.MCPServer",
        "version": "1.0.0"
    }


@app.get("/tools/list")
@app.post("/tools/list")
async def list_tools(x_internal_service_key: Optional[str] = Header(None)):
    if not verify_service_key(x_internal_service_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid internal service key."
        )
    return {"tools": server.list_tools()}


@app.post("/tools/call")
async def call_tool(
    req: ToolCallRequest,
    x_internal_service_key: Optional[str] = Header(None)
):
    if not verify_service_key(x_internal_service_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid internal service key."
        )
    return server.call_tool(req.name, req.arguments)


@app.post("/mcp")
async def jsonrpc_handler(
    req: JsonRpcRequest,
    x_internal_service_key: Optional[str] = Header(None)
):
    if not verify_service_key(x_internal_service_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid internal service key."
        )

    if req.method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "result": {"tools": server.list_tools()}
        }
    elif req.method == "tools/call":
        params = req.params or {}
        name = params.get("name", "")
        arguments = params.get("arguments", {})
        res = server.call_tool(name, arguments)
        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "result": res
        }
    else:
        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "error": {"code": -32601, "message": f"Method '{req.method}' not found"}
        }
