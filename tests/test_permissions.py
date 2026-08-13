"""
Unit tests for Tool Permission Matrix & Human Confirmation Gate.
"""

import unittest
from security.permissions import PermissionLevel, PermissionGate, ActionPermissionRequest


class TestPermissionGate(unittest.TestCase):
    """Test suite verifying tool permission classification and human approval requirements."""

    def setUp(self):
        self.gate = PermissionGate(enforce_human_confirmation=True)

    def test_read_permission_allowed_directly(self):
        """Read-only tool operations should be allowed directly without pause."""
        req = ActionPermissionRequest(
            tool_name="read_file",
            action_type=PermissionLevel.READ,
            resource="test.txt",
            details={"file_path": "test.txt"},
            is_destructive=False
        )
        res = self.gate.evaluate_request(req)
        self.assertEqual(res["status"], "ALLOWED")

    def test_destructive_operation_requires_confirmation(self):
        """Destructive operations must require human confirmation."""
        req = ActionPermissionRequest(
            tool_name="delete_file",
            action_type=PermissionLevel.DESTRUCTIVE,
            resource="important.txt",
            details={"file_path": "important.txt"},
            is_destructive=True
        )
        res = self.gate.evaluate_request(req)
        self.assertEqual(res["status"], "NEEDS_CONFIRMATION")
        self.assertIn("destructive", res["reason"])

    def test_mutating_operation_requires_confirmation(self):
        """Mutating write/execute operations marked destructive require human approval."""
        req = ActionPermissionRequest(
            tool_name="write_file",
            action_type=PermissionLevel.WRITE,
            resource="config.json",
            details={"file_path": "config.json"},
            is_destructive=True
        )
        res = self.gate.evaluate_request(req)
        self.assertEqual(res["status"], "NEEDS_CONFIRMATION")


if __name__ == "__main__":
    unittest.main()
