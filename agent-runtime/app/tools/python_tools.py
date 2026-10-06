"""
Hardened Python Code Execution Tool for Agent Runtime.

Implements SEC-01 mitigation: subprocess execution with strict environment variable
scrubbing, working-directory confinement, and execution timeouts.
"""

import subprocess
import sys
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional
from app.tools.base import BaseTool, ToolResult
from app.security.permissions import PermissionLevel
from app.security.fs_sandbox import WorkspaceSandbox
from app.security.sanitizer import sanitize_error_message


class ExecutePythonTool(BaseTool):
    """Tool for running Python scripts inside workspace context with sanitized environment."""

    def __init__(self, sandbox: WorkspaceSandbox, default_timeout: int = 10):
        super().__init__(
            name="execute_python",
            description="Executes a Python code script inside workspace context with strict timeout and environment scrubbing.",
            permission_level=PermissionLevel.EXECUTE,
            is_destructive=False
        )
        self.sandbox = sandbox
        self.default_timeout = max(1, default_timeout)

    def run(self, code_snippet: str, timeout_seconds: Optional[int] = None) -> ToolResult:
        if not code_snippet.strip():
            return ToolResult(success=False, output=None, error="Empty code snippet provided.")

        timeout = timeout_seconds if timeout_seconds is not None else self.default_timeout
        workspace_dir = self.sandbox.workspace_root
        temp_script_name = f"_temp_run_{int(time.time() * 1000)}.py"

        # SEC-01 Mitigation: Minimal sanitized environment without parent API keys or secrets
        sanitized_env = {
            "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
            "PYTHONPATH": ".",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8"
        }

        try:
            script_rel_path = self.sandbox.write_file(temp_script_name, code_snippet, overwrite=True)
            script_abs_path = self.sandbox.resolve_path(script_rel_path)

            start_time = time.time()
            proc = subprocess.run(
                [sys.executable, str(script_abs_path)],
                cwd=str(workspace_dir),
                env=sanitized_env,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            duration = round(time.time() - start_time, 3)

            if proc.returncode == 0:
                out_msg = proc.stdout if proc.stdout.strip() else "(Execution completed with no stdout output)"
                return ToolResult(success=True, output=f"Exit Code 0 ({duration}s):\n{out_msg}")
            else:
                err_msg = proc.stderr if proc.stderr.strip() else f"Process exited with code {proc.returncode}"
                return ToolResult(success=False, output=None, error=f"Exit Code {proc.returncode} ({duration}s):\n{err_msg}")

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output=None,
                error=f"Execution Timed Out: Script exceeded maximum allowed time limit of {timeout} seconds."
            )
        except Exception as e:
            clean_err = sanitize_error_message(e)
            return ToolResult(success=False, output=None, error=clean_err)
        finally:
            try:
                temp_file = workspace_dir / temp_script_name
                if temp_file.exists():
                    temp_file.unlink()
            except Exception:
                pass
