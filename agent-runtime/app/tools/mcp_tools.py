"""
MCP-backed Tool Implementations for Agent Runtime.

Connects the Agent Orchestrator to the Model Context Protocol (MCP) Server.
"""

from typing import Dict, Any, Optional
from app.tools.base import BaseTool, ToolResult
from app.security.permissions import PermissionLevel
from app.tools.mcp_client import MCPClient
from app.security.sanitizer import sanitize_error_message


class MCPListFilesTool(BaseTool):
    """Tool for listing files inside sandboxed workspace via MCP."""

    def __init__(self, mcp_client: MCPClient):
        super().__init__(
            name="list_files",
            description="Lists files and subdirectories inside the workspace root via MCP.",
            permission_level=PermissionLevel.READ,
            is_destructive=False
        )
        self.mcp_client = mcp_client

    def run(self, sub_dir: str = ".") -> ToolResult:
        try:
            res = self.mcp_client.call_tool("list_files", {"sub_dir": sub_dir})
            if res.get("isError"):
                err_text = res["content"][0]["text"] if res.get("content") else "MCP tool error"
                return ToolResult(success=False, output=None, error=err_text)
            text_content = res["content"][0]["text"] if res.get("content") else "[]"
            return ToolResult(success=True, output=text_content)
        except Exception as e:
            return ToolResult(success=False, output=None, error=sanitize_error_message(e))


class MCPReadFileTool(BaseTool):
    """Tool for reading file text content inside sandboxed workspace via MCP."""

    def __init__(self, mcp_client: MCPClient):
        super().__init__(
            name="read_file",
            description="Reads text content of a file inside workspace via MCP.",
            permission_level=PermissionLevel.READ,
            is_destructive=False
        )
        self.mcp_client = mcp_client

    def run(self, file_path: str, max_bytes: int = 100000) -> ToolResult:
        try:
            res = self.mcp_client.call_tool("read_file", {"file_path": file_path, "max_bytes": max_bytes})
            if res.get("isError"):
                err_text = res["content"][0]["text"] if res.get("content") else "MCP tool error"
                return ToolResult(success=False, output=None, error=err_text)
            text_content = res["content"][0]["text"] if res.get("content") else ""
            return ToolResult(success=True, output=text_content)
        except Exception as e:
            return ToolResult(success=False, output=None, error=sanitize_error_message(e))


class MCPInspectSchemaTool(BaseTool):
    """Tool for inspecting SQLite database tables and columns via MCP."""

    def __init__(self, mcp_client: MCPClient):
        super().__init__(
            name="inspect_schema",
            description="Inspects SQLite database schema inside workspace via MCP.",
            permission_level=PermissionLevel.READ,
            is_destructive=False
        )
        self.mcp_client = mcp_client

    def run(self, db_filename: str = "app_data.db") -> ToolResult:
        try:
            res = self.mcp_client.call_tool("inspect_schema", {"db_filename": db_filename})
            if res.get("isError"):
                err_text = res["content"][0]["text"] if res.get("content") else "MCP tool error"
                return ToolResult(success=False, output=None, error=err_text)
            text_content = res["content"][0]["text"] if res.get("content") else "{}"
            return ToolResult(success=True, output=text_content)
        except Exception as e:
            return ToolResult(success=False, output=None, error=sanitize_error_message(e))


class MCPWriteFileTool(BaseTool):
    """Tool for creating or updating files in workspace via MCP (Requires Approval)."""

    def __init__(self, mcp_client: MCPClient):
        super().__init__(
            name="write_file",
            description="Writes or appends text content to a workspace file via MCP.",
            permission_level=PermissionLevel.WRITE,
            is_destructive=False
        )
        self.mcp_client = mcp_client

    def run(self, file_path: str, content: str, append: bool = False) -> ToolResult:
        try:
            res = self.mcp_client.call_tool("write_file", {"file_path": file_path, "content": content, "append": append})
            if res.get("isError"):
                err_text = res["content"][0]["text"] if res.get("content") else "MCP tool error"
                return ToolResult(success=False, output=None, error=err_text)
            text_content = res["content"][0]["text"] if res.get("content") else "File written successfully."
            return ToolResult(success=True, output=text_content)
        except Exception as e:
            return ToolResult(success=False, output=None, error=sanitize_error_message(e))


class MCPDeleteFileTool(BaseTool):
    """Tool for deleting workspace files via MCP (DESTRUCTIVE - Requires Approval)."""

    def __init__(self, mcp_client: MCPClient):
        super().__init__(
            name="delete_file",
            description="Deletes a file from the workspace sandbox via MCP (DESTRUCTIVE).",
            permission_level=PermissionLevel.DESTRUCTIVE,
            is_destructive=True
        )
        self.mcp_client = mcp_client

    def run(self, file_path: str) -> ToolResult:
        try:
            res = self.mcp_client.call_tool("delete_file", {"file_path": file_path})
            if res.get("isError"):
                err_text = res["content"][0]["text"] if res.get("content") else "MCP tool error"
                return ToolResult(success=False, output=None, error=err_text)
            text_content = res["content"][0]["text"] if res.get("content") else "File deleted successfully."
            return ToolResult(success=True, output=text_content)
        except Exception as e:
            return ToolResult(success=False, output=None, error=sanitize_error_message(e))


class MCPQueryDatabaseTool(BaseTool):
    """Tool for querying SQLite database via MCP (Validated by SQLGuard)."""

    def __init__(self, mcp_client: MCPClient):
        super().__init__(
            name="query_database",
            description="Executes SQL query against SQLite database inside workspace via MCP.",
            permission_level=PermissionLevel.DATABASE,
            is_destructive=False
        )
        self.mcp_client = mcp_client

    def run(self, sql_query: str, db_filename: str = "app_data.db", allow_mutation: bool = True) -> ToolResult:
        try:
            res = self.mcp_client.call_tool("query_database", {
                "sql_query": sql_query,
                "db_filename": db_filename,
                "allow_mutation": allow_mutation
            })
            if res.get("isError"):
                err_text = res["content"][0]["text"] if res.get("content") else "Database query error"
                return ToolResult(success=False, output=None, error=err_text)
            text_content = res["content"][0]["text"] if res.get("content") else "{}"
            return ToolResult(success=True, output=text_content)
        except Exception as e:
            return ToolResult(success=False, output=None, error=sanitize_error_message(e))
