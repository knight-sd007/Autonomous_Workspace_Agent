"""
SQLite Database Engine for Sandboxed Workspace.

Provides schema inspection, read-only SELECT execution, and safe mutating SQL execution.
"""

import sqlite3
from typing import List, Dict, Any, Tuple
from pathlib import Path
from sandbox.fs_sandbox import WorkspaceSandbox
from database.sql_guard import SQLGuard, SQLClassification
from utils.logging import logger
from utils.security import sanitize_error_message


class SQLiteEngine:
    """Manages SQLite databases inside workspace sandbox."""

    def __init__(self, sandbox: WorkspaceSandbox):
        self.sandbox = sandbox

    def get_db_path(self, db_filename: str = "app_data.db") -> Path:
        """Resolves database file path inside workspace sandbox."""
        return self.sandbox.resolve_path(db_filename)

    def get_schema(self, db_filename: str = "app_data.db") -> Dict[str, Any]:
        """Inspects and returns database schema tables and columns."""
        db_path = self.get_db_path(db_filename)
        if not db_path.exists():
            return {"status": "empty", "message": f"Database file '{db_filename}' does not exist."}

        schema_info = {}
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [row[0] for row in cursor.fetchall()]

            for tbl in tables:
                cursor.execute(f"PRAGMA table_info('{tbl}');")
                cols = cursor.fetchall()
                schema_info[tbl] = [
                    {"cid": col[0], "name": col[1], "type": col[2], "notnull": col[3], "pk": col[5]}
                    for col in cols
                ]
            conn.close()
            return {"status": "success", "tables": schema_info}

        except Exception as e:
            clean_err = sanitize_error_message(e)
            logger.error(f"Error fetching SQLite schema for '{db_filename}': {clean_err}")
            return {"status": "error", "message": clean_err}

    def execute_query(
        self,
        sql_query: str,
        db_filename: str = "app_data.db",
        allow_mutation: bool = False
    ) -> Dict[str, Any]:
        """
        Executes SQL query against SQLite database in workspace.
        Validates query safety using SQLGuard.
        """
        analysis = SQLGuard.analyze_query(sql_query)

        if not analysis.is_safe_read and not allow_mutation:
            return {
                "success": False,
                "error": f"Security Blocked: {analysis.reason}. Mutation permission is set to False.",
                "analysis": analysis
            }

        db_path = self.get_db_path(db_filename)
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            logger.info(f"Executing SQL query ({analysis.classification.name}) on '{db_filename}'")
            cursor.execute(sql_query)

            if analysis.is_safe_read or sql_query.strip().upper().startswith("SELECT"):
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                conn.close()
                return {
                    "success": True,
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows),
                    "analysis": analysis
                }
            else:
                conn.commit()
                affected = cursor.rowcount
                conn.close()
                return {
                    "success": True,
                    "rows_affected": affected,
                    "message": f"Successfully executed mutation ({analysis.statement_type}). Rows affected: {affected}",
                    "analysis": analysis
                }

        except Exception as e:
            clean_err = sanitize_error_message(e)
            logger.error(f"SQLite execution error: {clean_err}")
            return {
                "success": False,
                "error": clean_err,
                "analysis": analysis
            }
