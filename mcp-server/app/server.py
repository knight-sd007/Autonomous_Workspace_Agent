"""
Custom MCP Server Engine for Autonomous Workspace Agent.

Implements standard MCP protocol methods for tool discovery, JSON schemas,
and safe execution over internal JSON-RPC transport.
"""

from typing import Dict, Any, List, Optional
import os
from pathlib import Path
from app.security.fs_guard import MCPFileSystemGuard
from app.tools.workspace_tools import WorkspaceMCPTools
from app.tools.db_tools import DatabaseMCPTools


class WorkspaceMCPServer:
    """Standard Model Context Protocol (MCP) Server for P07 Workspace Agent."""

    def __init__(self, workspace_root: Optional[Path] = None):
        if workspace_root is None:
            raw_path = os.getenv("WORKSPACE_DIR", "workspace")
            base_dir = Path(__file__).resolve().parent.parent.parent
            workspace_root = (base_dir / raw_path).resolve()

        self.guard = MCPFileSystemGuard(workspace_root)
        self.tools = WorkspaceMCPTools(self.guard)
        self.db_tools = DatabaseMCPTools(self.guard)


    def list_tools(self) -> List[Dict[str, Any]]:
        """Returns JSON schema definitions of all available MCP tools."""
        return [
            {
                "name": "list_files",
                "description": "Lists files and directories inside the sandboxed workspace root.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sub_dir": {
                            "type": "string",
                            "description": "Relative subdirectory path (defaults to root '.')",
                            "default": "."
                        }
                    }
                }
            },
            {
                "name": "read_file",
                "description": "Reads text content from a file inside the sandboxed workspace root.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Relative path to target file in workspace"
                        },
                        "max_bytes": {
                            "type": "integer",
                            "description": "Maximum bytes to read (default 100000)",
                            "default": 100000
                        }
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "inspect_schema",
                "description": "Inspects SQLite tables and columns inside workspace database.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "db_filename": {
                            "type": "string",
                            "description": "Relative SQLite database filename (default app_data.db)",
                            "default": "app_data.db"
                        }
                    }
                }
            },
            {
                "name": "write_file",
                "description": "Writes or appends text content to a file inside the sandboxed workspace.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Relative path to target file in workspace"
                        },
                        "content": {
                            "type": "string",
                            "description": "Text content to write to the file"
                        },
                        "append": {
                            "type": "boolean",
                            "description": "Whether to append to file instead of overwriting (default false)",
                            "default": False
                        }
                    },
                    "required": ["file_path", "content"]
                }
            },
            {
                "name": "delete_file",
                "description": "Deletes a file from the sandboxed workspace root (DESTRUCTIVE).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Relative path to target file to delete"
                        }
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "query_database",
                "description": "Executes SQL query against SQLite database inside workspace. Safe read queries execute directly; mutating/destructive queries require explicit confirmation.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql_query": {
                            "type": "string",
                            "description": "SQL query statement to execute"
                        },
                        "db_filename": {
                            "type": "string",
                            "description": "Target SQLite database filename (default app_data.db)",
                            "default": "app_data.db"
                        },
                        "allow_mutation": {
                            "type": "boolean",
                            "description": "Whether mutation is explicitly authorized (default false)",
                            "default": False
                        }
                    },
                    "required": ["sql_query"]
                }
            }
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Executes tool action and returns structured MCP response."""
        try:
            if name == "list_files":
                sub_dir = arguments.get("sub_dir", ".")
                data = self.tools.list_files(sub_dir)
                return {"isError": False, "content": [{"type": "text", "text": str(data)}]}

            elif name == "read_file":
                file_path = arguments.get("file_path", "")
                max_bytes = int(arguments.get("max_bytes", 100000))
                data = self.tools.read_file(file_path, max_bytes)
                return {"isError": False, "content": [{"type": "text", "text": data}]}

            elif name == "inspect_schema":
                db_filename = arguments.get("db_filename", "app_data.db")
                data = self.db_tools.inspect_schema(db_filename)
                return {"isError": False, "content": [{"type": "text", "text": str(data)}]}

            elif name == "write_file":
                file_path = arguments.get("file_path", "")
                content = arguments.get("content", "")
                append = bool(arguments.get("append", False))
                data = self.tools.write_file(file_path, content, append=append)
                return {"isError": False, "content": [{"type": "text", "text": str(data)}]}

            elif name == "delete_file":
                file_path = arguments.get("file_path", "")
                data = self.tools.delete_file(file_path)
                return {"isError": False, "content": [{"type": "text", "text": str(data)}]}

            elif name == "query_database":
                sql_query = arguments.get("sql_query", "")
                db_filename = arguments.get("db_filename", "app_data.db")
                allow_mutation = bool(arguments.get("allow_mutation", False))
                data = self.db_tools.query_database(sql_query, db_filename=db_filename, allow_mutation=allow_mutation)
                if not data.get("success", False):
                    return {"isError": True, "content": [{"type": "text", "text": data.get("error", "Database error")}]}
                return {"isError": False, "content": [{"type": "text", "text": str(data)}]}

            else:
                return {"isError": True, "content": [{"type": "text", "text": f"Unknown tool '{name}'"}]}

        except Exception as e:
            return {"isError": True, "content": [{"type": "text", "text": f"MCP Tool Error: {str(e)}"}]}
