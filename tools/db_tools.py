"""
SQLite Database Workstation Tools.
"""

from tools.base import BaseTool, ToolResult
from security.permissions import PermissionLevel
from database.sqlite_engine import SQLiteEngine
from database.sql_guard import SQLGuard, SQLClassification
from utils.security import sanitize_error_message


class InspectSchemaTool(BaseTool):
    """Tool for inspecting SQLite database schema."""

    def __init__(self, db_engine: SQLiteEngine):
        super().__init__(
            name="inspect_schema",
            description="Inspects tables and columns in SQLite database.",
            permission_level=PermissionLevel.READ,
            is_destructive=False
        )
        self.db_engine = db_engine

    def run(self, db_filename: str = "app_data.db") -> ToolResult:
        try:
            res = self.db_engine.get_schema(db_filename)
            if res.get("status") == "success":
                return ToolResult(success=True, output=res["tables"])
            else:
                return ToolResult(success=False, output=None, error=res.get("message", "Error fetching schema."))
        except Exception as e:
            clean_err = sanitize_error_message(e)
            return ToolResult(success=False, output=None, error=clean_err)


class QueryDatabaseTool(BaseTool):
    """Tool for executing SQL queries on SQLite database."""

    def __init__(self, db_engine: SQLiteEngine):
        super().__init__(
            name="query_database",
            description="Executes a SQL query on SQLite database.",
            permission_level=PermissionLevel.DATABASE,
            is_destructive=False
        )
        self.db_engine = db_engine

    def run(self, sql_query: str, db_filename: str = "app_data.db", allow_mutation: bool = False) -> ToolResult:
        try:
            # Check SQL analysis
            analysis = SQLGuard.analyze_query(sql_query)

            if analysis.classification in (SQLClassification.DESTRUCTIVE, SQLClassification.MUTATING):
                if not allow_mutation:
                    return ToolResult(
                        success=False,
                        output=None,
                        error=f"Security Blocked: Query '{sql_query}' is mutating ({analysis.reason}). Human confirmation required.",
                        requires_confirmation=True,
                        confirmation_reason=analysis.reason
                    )

            res = self.db_engine.execute_query(sql_query, db_filename=db_filename, allow_mutation=allow_mutation)
            if res.get("success"):
                if "rows" in res:
                    cols = res.get("columns", [])
                    rows = res.get("rows", [])
                    return ToolResult(success=True, output={"columns": cols, "rows": rows, "count": len(rows)})
                else:
                    return ToolResult(success=True, output=res.get("message", "Executed successfully."))
            else:
                return ToolResult(success=False, output=None, error=res.get("error", "SQL Execution failed."))

        except Exception as e:
            clean_err = sanitize_error_message(e)
            return ToolResult(success=False, output=None, error=clean_err)
