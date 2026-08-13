"""
Unit tests for Workstation Agent Orchestrator.
"""

import unittest
import tempfile
from pathlib import Path
from sandbox.fs_sandbox import WorkspaceSandbox
from agent.orchestrator import WorkstationAgentOrchestrator


class TestWorkstationAgentOrchestrator(unittest.TestCase):
    """Test suite verifying agent tool registration, execution, and confirmation gates."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sandbox = WorkspaceSandbox(Path(self.temp_dir.name))
        self.orchestrator = WorkstationAgentOrchestrator(self.sandbox)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_registered_tools(self):
        """All workstation tools should be registered upon initialization."""
        tools = self.orchestrator.tools
        self.assertIn("list_files", tools)
        self.assertIn("read_file", tools)
        self.assertIn("write_file", tools)
        self.assertIn("delete_file", tools)
        self.assertIn("execute_python", tools)
        self.assertIn("inspect_schema", tools)
        self.assertIn("query_database", tools)

    def test_read_tool_execution(self):
        """Read tool call should execute directly without confirmation pause."""
        res = self.orchestrator.execute_tool_call("list_files", {"sub_dir": "."})
        self.assertEqual(res["status"], "success")

    def test_destructive_tool_requires_confirmation(self):
        """Destructive tool call without user confirmation must return NEEDS_CONFIRMATION status."""
        res = self.orchestrator.execute_tool_call("delete_file", {"file_path": "test.txt"})
        self.assertEqual(res["status"], "NEEDS_CONFIRMATION")
        self.assertEqual(res["tool_name"], "delete_file")

    def test_destructive_tool_with_user_confirmation(self):
        """Destructive tool call with user confirmation should proceed."""
        # Write file first
        self.sandbox.write_file("to_del.txt", "Content")

        res = self.orchestrator.execute_tool_call(
            "delete_file",
            {"file_path": "to_del.txt"},
            user_confirmed=True
        )
        self.assertEqual(res["status"], "success")


if __name__ == "__main__":
    unittest.main()
