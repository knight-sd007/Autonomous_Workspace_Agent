"""
Filesystem Workstation Tools for Agent Runtime.
"""

from app.tools.base import BaseTool, ToolResult
from app.security.permissions import PermissionLevel
from app.security.fs_sandbox import WorkspaceSandbox
from app.security.sanitizer import sanitize_error_message


class ListFilesTool(BaseTool):
    """Tool for listing files inside workspace directory."""

    def __init__(self, sandbox: WorkspaceSandbox):
        super().__init__(
            name="list_files",
            description="Lists files and subdirectories inside the workspace root.",
            permission_level=PermissionLevel.READ,
            is_destructive=False
        )
        self.sandbox = sandbox

    def run(self, sub_dir: str = ".") -> ToolResult:
        try:
            files = self.sandbox.list_files(sub_dir)
            return ToolResult(success=True, output=files)
        except Exception as e:
            clean_err = sanitize_error_message(e)
            return ToolResult(success=False, output=None, error=clean_err)


class ReadFileTool(BaseTool):
    """Tool for reading text file content from workspace."""

    def __init__(self, sandbox: WorkspaceSandbox):
        super().__init__(
            name="read_file",
            description="Reads text content of a file inside workspace.",
            permission_level=PermissionLevel.READ,
            is_destructive=False
        )
        self.sandbox = sandbox

    def run(self, file_path: str) -> ToolResult:
        try:
            content = self.sandbox.read_file(file_path)
            return ToolResult(success=True, output=content)
        except Exception as e:
            clean_err = sanitize_error_message(e)
            return ToolResult(success=False, output=None, error=clean_err)


class WriteFileTool(BaseTool):
    """Tool for writing content to a workspace file."""

    def __init__(self, sandbox: WorkspaceSandbox):
        super().__init__(
            name="write_file",
            description="Creates or overwrites a text file in workspace.",
            permission_level=PermissionLevel.WRITE,
            is_destructive=False
        )
        self.sandbox = sandbox

    def run(self, file_path: str, content: str) -> ToolResult:
        try:
            rel_path = self.sandbox.write_file(file_path, content, overwrite=True)
            return ToolResult(success=True, output=f"Successfully wrote file '{rel_path}' ({len(content)} chars).")
        except Exception as e:
            clean_err = sanitize_error_message(e)
            return ToolResult(success=False, output=None, error=clean_err)


class DeleteFileTool(BaseTool):
    """Tool for deleting a workspace file (DESTRUCTIVE)."""

    def __init__(self, sandbox: WorkspaceSandbox):
        super().__init__(
            name="delete_file",
            description="Deletes a file from workspace (DESTRUCTIVE).",
            permission_level=PermissionLevel.DESTRUCTIVE,
            is_destructive=True
        )
        self.sandbox = sandbox

    def run(self, file_path: str) -> ToolResult:
        try:
            self.sandbox.delete_file(file_path)
            return ToolResult(success=True, output=f"Successfully deleted file '{file_path}'.")
        except Exception as e:
            clean_err = sanitize_error_message(e)
            return ToolResult(success=False, output=None, error=clean_err)
