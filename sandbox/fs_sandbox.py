"""
Workspace Filesystem Sandbox Manager.

Enforces workspace-level filesystem isolation, preventing path traversal attacks,
absolute path escapes, or symlink dereferencing outside the configured workspace root directory.
"""

from pathlib import Path
from typing import Union, List, Dict, Any
import os
from utils.logging import logger


class PathTraversalError(SecurityException := Exception):
    """Raised when a path traversal escape attempt is detected."""
    pass


class SecurityViolationError(SecurityException):
    """Raised when a security policy boundary is breached."""
    pass


class WorkspaceSandbox:
    """
    Guards workspace filesystem operations.
    All file operations MUST be validated against the workspace root.
    """

    def __init__(self, workspace_root: Union[str, Path]):
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        logger.info(f"Workspace Sandbox initialized at: '{self.workspace_root}'")

    def resolve_path(self, relative_or_absolute_path: Union[str, Path]) -> Path:
        """
        Resolves a user or agent path string against the workspace root.
        Throws PathTraversalError if resolved path falls outside workspace_root.
        """
        raw_str = str(relative_or_absolute_path).strip()
        if not raw_str:
            raise PathTraversalError("Path argument cannot be empty.")

        path_obj = Path(raw_str)

        # Handle absolute path or relative path
        if path_obj.is_absolute():
            target_path = path_obj.resolve()
        else:
            target_path = (self.workspace_root / path_obj).resolve()

        # Strict boundary check: target_path must start with workspace_root
        try:
            target_path.relative_to(self.workspace_root)
        except ValueError:
            logger.warning(f"Path traversal blocked: '{raw_str}' -> '{target_path}' (outside root '{self.workspace_root}')")
            raise PathTraversalError(
                f"Security Violation: Target path '{raw_str}' resolves outside the allowed workspace boundary."
            )

        # Symlink escape check if path exists
        if target_path.is_symlink():
            real_target = target_path.readlink().resolve()
            try:
                real_target.relative_to(self.workspace_root)
            except ValueError:
                logger.warning(f"Symlink escape blocked: '{target_path}' -> '{real_target}'")
                raise PathTraversalError("Security Violation: Symlink targets path outside workspace sandbox.")

        return target_path

    def get_relative_path(self, absolute_path: Path) -> str:
        """Converts an absolute resolved workspace path back to relative path string."""
        resolved = absolute_path.resolve()
        try:
            return str(resolved.relative_to(self.workspace_root))
        except ValueError:
            return str(resolved)

    def list_files(self, sub_dir: str = ".") -> List[Dict[str, Any]]:
        """Lists files and directories inside sub_dir within workspace."""
        target_dir = self.resolve_path(sub_dir)
        if not target_dir.exists():
            raise FileNotFoundError(f"Directory '{sub_dir}' does not exist.")
        if not target_dir.is_dir():
            raise NotADirectoryError(f"Path '{sub_dir}' is not a directory.")

        results = []
        for entry in target_dir.iterdir():
            rel_path = self.get_relative_path(entry)
            results.append({
                "name": entry.name,
                "relative_path": rel_path,
                "is_dir": entry.is_dir(),
                "size_bytes": entry.stat().st_size if entry.is_file() else 0
            })
        return results

    def read_file(self, file_path: str, max_bytes: int = 100000) -> str:
        """Reads text content of a file within workspace sandbox."""
        target_file = self.resolve_path(file_path)
        if not target_file.exists():
            raise FileNotFoundError(f"File '{file_path}' does not exist in workspace.")
        if not target_file.is_file():
            raise IsADirectoryError(f"Path '{file_path}' is a directory, not a file.")

        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(max_bytes)
        return content

    def write_file(self, file_path: str, content: str, overwrite: bool = True) -> str:
        """Writes text content to a file inside workspace sandbox."""
        target_file = self.resolve_path(file_path)
        if target_file.exists() and not overwrite:
            raise FileExistsError(f"File '{file_path}' already exists and overwrite is False.")

        target_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Wrote {len(content)} characters to '{target_file.name}' in workspace.")
        return self.get_relative_path(target_file)

    def delete_file(self, file_path: str) -> bool:
        """Deletes a file inside workspace sandbox."""
        target_file = self.resolve_path(file_path)
        if not target_file.exists():
            raise FileNotFoundError(f"File '{file_path}' does not exist.")
        if target_file.is_dir():
            raise IsADirectoryError(f"Cannot delete directory '{file_path}' via delete_file.")

        target_file.unlink()
        logger.info(f"Deleted file '{file_path}' from workspace sandbox.")
        return True
