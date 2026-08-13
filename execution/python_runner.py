"""
Controlled Python Subprocess Runner.

Executes Python code scripts inside workspace directory context with timeout limits
and stdout/stderr output capturing.
"""

import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Union, Dict, Any
from sandbox.fs_sandbox import WorkspaceSandbox
from utils.logging import logger
from utils.security import sanitize_error_message


@dataclass
class ExecutionResult:
    """Dataclass encapsulating subprocess execution outcome."""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration_seconds: float
    timed_out: bool = False
    error_message: str = ""


class PythonRunner:
    """
    Subprocess execution manager running Python code under controlled workspace conditions.
    """

    def __init__(self, sandbox: WorkspaceSandbox, default_timeout: int = 10):
        self.sandbox = sandbox
        self.default_timeout = max(1, default_timeout)

    def run_code(self, code_snippet: str, timeout_seconds: int = None) -> ExecutionResult:
        """
        Executes Python code snippet as a temporary script inside workspace sandbox root.
        Captures stdout, stderr, exit code, and handles process timeouts safely.
        """
        if not code_snippet.strip():
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="Empty code snippet provided.",
                exit_code=1,
                duration_seconds=0.0,
                error_message="Empty code snippet."
            )

        timeout = timeout_seconds if timeout_seconds is not None else self.default_timeout
        workspace_dir = self.sandbox.workspace_root

        # Create temporary script file inside workspace
        temp_script_name = f"_temp_run_{int(time.time() * 1000)}.py"
        try:
            script_rel_path = self.sandbox.write_file(temp_script_name, code_snippet, overwrite=True)
            script_abs_path = self.sandbox.resolve_path(script_rel_path)

            start_time = time.time()
            logger.info(f"Executing Python script '{temp_script_name}' (timeout: {timeout}s)")

            # Execute subprocess using python executable
            proc = subprocess.run(
                [sys.executable, str(script_abs_path)],
                cwd=str(workspace_dir),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            duration = round(time.time() - start_time, 3)

            return ExecutionResult(
                success=(proc.returncode == 0),
                stdout=proc.stdout or "",
                stderr=proc.stderr or "",
                exit_code=proc.returncode,
                duration_seconds=duration,
                timed_out=False
            )

        except subprocess.TimeoutExpired:
            duration = float(timeout)
            logger.warning(f"Python script execution timed out after {timeout} seconds.")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Execution Timed Out: Script exceeded maximum allowed time limit of {timeout} seconds.",
                exit_code=-1,
                duration_seconds=duration,
                timed_out=True,
                error_message=f"Process timed out after {timeout} seconds."
            )

        except Exception as e:
            clean_err = sanitize_error_message(e)
            logger.error(f"Python runner error: {clean_err}")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=clean_err,
                exit_code=1,
                duration_seconds=0.0,
                error_message=clean_err
            )

        finally:
            # Clean up temporary script
            try:
                temp_file = workspace_dir / temp_script_name
                if temp_file.exists():
                    temp_file.unlink()
            except Exception:
                pass
