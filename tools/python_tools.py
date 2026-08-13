"""
Python Code Execution Tool.
"""

from tools.base import BaseTool, ToolResult
from security.permissions import PermissionLevel
from execution.python_runner import PythonRunner
from utils.security import sanitize_error_message


class ExecutePythonTool(BaseTool):
    """Tool for running Python scripts inside workspace context."""

    def __init__(self, runner: PythonRunner):
        super().__init__(
            name="execute_python",
            description="Executes a Python code script inside workspace context.",
            permission_level=PermissionLevel.EXECUTE,
            is_destructive=False
        )
        self.runner = runner

    def run(self, code_snippet: str, timeout_seconds: int = 10) -> ToolResult:
        try:
            res = self.runner.run_code(code_snippet, timeout_seconds=timeout_seconds)
            if res.success:
                out_msg = res.stdout if res.stdout.strip() else "(Execution completed with no stdout output)"
                return ToolResult(success=True, output=f"Exit Code 0 ({res.duration_seconds}s):\n{out_msg}")
            else:
                err_msg = res.stderr if res.stderr.strip() else res.error_message
                return ToolResult(success=False, output=None, error=f"Exit Code {res.exit_code}:\n{err_msg}")
        except Exception as e:
            clean_err = sanitize_error_message(e)
            return ToolResult(success=False, output=None, error=clean_err)
