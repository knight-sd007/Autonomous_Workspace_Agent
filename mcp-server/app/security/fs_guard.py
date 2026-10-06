"""
Filesystem Guard for MCP Server Tools.
"""

from pathlib import Path
from typing import Union


class MCPPathSecurityError(Exception):
    """Raised when an MCP tool path resolution escapes the workspace boundary."""
    pass


class MCPFileSystemGuard:
    """Enforces strict path confinement for all MCP file operations."""

    def __init__(self, workspace_root: Union[str, Path]):
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def validate_and_resolve(self, raw_path: str) -> Path:
        cleaned = raw_path.strip()
        if not cleaned:
            raise MCPPathSecurityError("Path cannot be empty.")

        path_obj = Path(cleaned)
        if path_obj.is_absolute():
            target_path = path_obj.resolve()
        else:
            target_path = (self.workspace_root / path_obj).resolve()

        try:
            target_path.relative_to(self.workspace_root)
        except ValueError:
            raise MCPPathSecurityError(f"Path traversal blocked: '{raw_path}' resolves outside workspace boundary.")

        if target_path.is_symlink():
            real_target = target_path.readlink().resolve()
            try:
                real_target.relative_to(self.workspace_root)
            except ValueError:
                raise MCPPathSecurityError("Symlink escape blocked: link targets path outside workspace.")

        return target_path
