"""
Workspace Tools for MCP Server.

Implements Phase 3 requirements: read-oriented tools (list_files, read_file, inspect_schema).
"""

import sqlite3
from typing import Dict, Any, List
from app.security.fs_guard import MCPFileSystemGuard, MCPPathSecurityError


class WorkspaceMCPTools:
    """Read-oriented tools exposed via MCP Server."""

    def __init__(self, guard: MCPFileSystemGuard):
        self.guard = guard

    def list_files(self, sub_dir: str = ".") -> List[Dict[str, Any]]:
        """Lists files and directories inside sub_dir within workspace."""
        target_dir = self.guard.validate_and_resolve(sub_dir)
        if not target_dir.exists():
            raise FileNotFoundError(f"Directory '{sub_dir}' does not exist.")
        if not target_dir.is_dir():
            raise NotADirectoryError(f"Path '{sub_dir}' is not a directory.")

        results = []
        for entry in sorted(target_dir.iterdir()):
            results.append({
                "name": entry.name,
                "is_dir": entry.is_dir(),
                "size_bytes": entry.stat().st_size if entry.is_file() else 0
            })
        return results

    def read_file(self, file_path: str, max_bytes: int = 100000) -> str:
        """Reads text content of a file within workspace sandbox."""
        target_file = self.guard.validate_and_resolve(file_path)
        if not target_file.exists():
            raise FileNotFoundError(f"File '{file_path}' does not exist.")
        if not target_file.is_file():
            raise IsADirectoryError(f"Path '{file_path}' is not a file.")

        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            return f.read(max_bytes)

    def inspect_schema(self, db_filename: str = "app_data.db") -> Dict[str, Any]:
        """Inspects SQLite database schema and returns tables and column definitions."""
        db_path = self.guard.validate_and_resolve(db_filename)
        if not db_path.exists():
            return {"tables": {}, "message": f"Database file '{db_filename}' does not exist."}

        schema_info = {}
        conn = sqlite3.connect(str(db_path))
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [r[0] for r in cursor.fetchall()]

            for tbl in tables:
                cursor.execute(f"PRAGMA table_info('{tbl}');")
                cols = cursor.fetchall()
                schema_info[tbl] = [
                    {"name": c[1], "type": c[2], "notnull": c[3], "pk": c[5]}
                    for c in cols
                ]
            return {"tables": schema_info}
        finally:
            conn.close()

    def write_file(self, file_path: str, content: str, append: bool = False) -> Dict[str, Any]:
        """Writes text content to a file inside the sandboxed workspace."""
        target_file = self.guard.validate_and_resolve(file_path)
        if target_file == self.guard.workspace_root:
            raise MCPPathSecurityError("Cannot write to workspace root directory as a file.")
        if target_file.is_dir():
            raise IsADirectoryError(f"Path '{file_path}' is a directory.")

        target_file.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with open(target_file, mode, encoding="utf-8") as f:
            f.write(content)

        rel_path = str(target_file.relative_to(self.guard.workspace_root))
        return {
            "success": True,
            "file_path": rel_path,
            "bytes_written": len(content),
            "message": f"Successfully wrote {len(content)} characters to '{rel_path}'."
        }

    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """Deletes a file inside the sandboxed workspace."""
        target_file = self.guard.validate_and_resolve(file_path)
        if target_file == self.guard.workspace_root:
            raise MCPPathSecurityError("Cannot delete workspace root directory.")
        if not target_file.exists():
            raise FileNotFoundError(f"File '{file_path}' does not exist.")
        if target_file.is_dir():
            raise IsADirectoryError(f"Cannot delete directory '{file_path}' via delete_file.")

        target_file.unlink()
        rel_path = str(target_file.relative_to(self.guard.workspace_root))
        return {
            "success": True,
            "file_path": rel_path,
            "message": f"File '{rel_path}' deleted successfully."
        }
