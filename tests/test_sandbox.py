"""
Unit tests for Workspace Filesystem Sandbox & Path Traversal Defenses.
"""

import unittest
import tempfile
from pathlib import Path
from sandbox.fs_sandbox import WorkspaceSandbox, PathTraversalError


class TestWorkspaceSandbox(unittest.TestCase):
    """Test suite verifying workspace path resolution and security boundaries."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = Path(self.temp_dir.name)
        self.sandbox = WorkspaceSandbox(self.workspace_root)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_valid_workspace_path_resolution(self):
        """Relative path inside workspace should resolve cleanly."""
        resolved = self.sandbox.resolve_path("data/test.txt")
        self.assertTrue(str(resolved).startswith(str(self.workspace_root)))
        self.assertEqual(resolved, self.workspace_root / "data" / "test.txt")

    def test_path_traversal_double_dot_blocked(self):
        """Path attempting '../' traversal outside workspace root must raise PathTraversalError."""
        with self.assertRaises(PathTraversalError):
            self.sandbox.resolve_path("../../etc/passwd")

    def test_absolute_path_escape_blocked(self):
        """Absolute path pointing outside workspace root must raise PathTraversalError."""
        with self.assertRaises(PathTraversalError):
            self.sandbox.resolve_path("/etc/passwd")

    def test_write_and_read_file_inside_sandbox(self):
        """Writing and reading file inside sandbox should work correctly."""
        rel_path = self.sandbox.write_file("sample.txt", "Hello Sandbox World")
        self.assertEqual(rel_path, "sample.txt")

        content = self.sandbox.read_file("sample.txt")
        self.assertEqual(content, "Hello Sandbox World")

    def test_delete_file_inside_sandbox(self):
        """Deleting file inside sandbox should work correctly."""
        self.sandbox.write_file("to_delete.txt", "Delete me")
        res = self.sandbox.delete_file("to_delete.txt")
        self.assertTrue(res)

        with self.assertRaises(FileNotFoundError):
            self.sandbox.read_file("to_delete.txt")


if __name__ == "__main__":
    unittest.main()
