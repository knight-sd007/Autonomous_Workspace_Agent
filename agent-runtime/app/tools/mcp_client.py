"""
MCP Client for Python Agent Runtime.

Provides high-level integration with the MCP Server over HTTP / JSON-RPC
with graceful local in-process fallback for isolated testing and offline execution.
"""

from typing import Dict, Any, List, Optional
import os
import logging
import httpx
from pathlib import Path
from app.config import RuntimeConfig
from app.security.sanitizer import sanitize_error_message

logger = logging.getLogger("p07.mcp_client")


class MCPClient:
    """Client for querying and executing tools exposed by MCP Server."""

    def __init__(
        self,
        mcp_base_url: Optional[str] = None,
        service_key: Optional[str] = None,
        workspace_root: Optional[Path] = None
    ):
        self.mcp_base_url = mcp_base_url or os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8002")
        self.service_key = service_key or RuntimeConfig.get_service_key()
        self.workspace_root = workspace_root or RuntimeConfig.get_workspace_dir()
        self._in_process_server = None

    def _get_in_process_server(self):
        """Lazy in-process server initialization when HTTP endpoint is unreachable."""
        if self._in_process_server is None:
            try:
                # Add mcp-server to sys.path if needed
                import sys
                base_dir = Path(__file__).resolve().parent.parent.parent.parent / "mcp-server"
                if str(base_dir) not in sys.path:
                    sys.path.insert(0, str(base_dir))

                from app.server import WorkspaceMCPServer
                self._in_process_server = WorkspaceMCPServer(workspace_root=self.workspace_root)
            except Exception as e:
                logger.error(f"Failed to initialize in-process WorkspaceMCPServer: {e}")
                raise
        return self._in_process_server

    async def list_tools_async(self) -> List[Dict[str, Any]]:
        """Discovers tools available on the MCP Server."""
        try:
            async with httpx.AsyncClient(base_url=self.mcp_base_url, timeout=5.0) as client:
                res = await client.get("/tools/list", headers={"X-Internal-Service-Key": self.service_key})
                if res.status_code == 200:
                    data = res.json()
                    return data.get("tools", [])
        except Exception as ex:
            logger.debug(f"MCP HTTP list_tools unreachable ({ex}), utilizing in-process server.")

        # Fallback to in-process server
        server = self._get_in_process_server()
        return server.list_tools()

    def list_tools(self) -> List[Dict[str, Any]]:
        """Synchronous tool discovery."""
        server = self._get_in_process_server()
        return server.list_tools()

    async def call_tool_async(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Calls an MCP tool over HTTP or in-process fallback."""
        try:
            async with httpx.AsyncClient(base_url=self.mcp_base_url, timeout=10.0) as client:
                res = await client.post(
                    "/tools/call",
                    json={"name": name, "arguments": arguments},
                    headers={"X-Internal-Service-Key": self.service_key}
                )
                if res.status_code == 200:
                    return res.json()
                elif res.status_code == 401:
                    return {"isError": True, "content": [{"type": "text", "text": "Unauthorized MCP request."}]}
        except Exception as ex:
            logger.debug(f"MCP HTTP call_tool unreachable ({ex}), executing via in-process engine.")

        # Fallback to in-process execution
        try:
            server = self._get_in_process_server()
            return server.call_tool(name, arguments)
        except Exception as e:
            return {"isError": True, "content": [{"type": "text", "text": f"MCP Client Error: {sanitize_error_message(e)}"}]}

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous tool call execution."""
        try:
            server = self._get_in_process_server()
            return server.call_tool(name, arguments)
        except Exception as e:
            return {"isError": True, "content": [{"type": "text", "text": f"MCP Client Error: {sanitize_error_message(e)}"}]}
