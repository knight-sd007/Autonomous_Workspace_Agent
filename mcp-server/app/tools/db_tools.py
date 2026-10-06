"""
Database Tools for MCP Server.

Integrates SQLite query execution with SQLGuard safety validation.
"""

import sqlite3
from typing import Dict, Any, List, Optional
from pathlib import Path
from app.security.fs_guard import MCPFileSystemGuard, MCPPathSecurityError
from app.security.sql_guard import SQLGuard, SQLClassification, SQLAnalysisResult


class DatabaseMCPTools:
    """Database query and schema inspection tools for MCP Server."""

    def __init__(self, guard: MCPFileSystemGuard):
        self.guard = guard

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
                    {"cid": c[0], "name": c[1], "type": c[2], "notnull": c[3], "pk": c[5]}
                    for c in cols
                ]
            return {"tables": schema_info}
        finally:
            conn.close()

    def query_database(
        self,
        sql_query: str,
        db_filename: str = "app_data.db",
        allow_mutation: bool = False,
        params: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes a SQL query against a SQLite database inside the sandboxed workspace.
        Enforces SQLGuard validation prior to execution.
        """
        analysis = SQLGuard.analyze_query(sql_query)

        if not analysis.is_safe_read and not allow_mutation:
            return {
                "success": False,
                "error": f"Security Guard Blocked: {analysis.reason}. Mutation authorization is required.",
                "analysis": analysis.to_dict()
            }

        db_path = self.guard.validate_and_resolve(db_filename)
        # Ensure parent directory exists for new databases
        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(db_path))
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql_query, params)
            else:
                cursor.execute(sql_query)

            if analysis.is_safe_read or sql_query.strip().upper().startswith("SELECT"):
                columns = [d[0] for d in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                return {
                    "success": True,
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows),
                    "analysis": analysis.to_dict()
                }
            else:
                conn.commit()
                affected = cursor.rowcount
                return {
                    "success": True,
                    "rows_affected": affected,
                    "message": f"Successfully executed mutation ({analysis.statement_type}). Rows affected: {affected}",
                    "analysis": analysis.to_dict()
                }
        finally:
            conn.close()
