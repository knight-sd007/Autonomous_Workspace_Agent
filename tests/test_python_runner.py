"""
Unit tests for Python Subprocess Runner.
"""

import unittest
import tempfile
from pathlib import Path
from sandbox.fs_sandbox import WorkspaceSandbox
from execution.python_runner import PythonRunner


class TestPythonRunner(unittest.TestCase):
    """Test suite verifying controlled Python subprocess execution and timeout protection."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sandbox = WorkspaceSandbox(Path(self.temp_dir.name))
        self.runner = PythonRunner(self.sandbox, default_timeout=5)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_valid_python_execution(self):
        """Valid Python code should execute cleanly and capture stdout."""
        code = "print('Hello from Python runner')"
        res = self.runner.run_code(code)
        self.assertTrue(res.success)
        self.assertEqual(res.exit_code, 0)
        self.assertIn("Hello from Python runner", res.stdout)

    def test_python_execution_timeout(self):
        """Long running script exceeding timeout limit should be terminated safely."""
        code = "import time; time.sleep(10)"
        res = self.runner.run_code(code, timeout_seconds=1)
        self.assertFalse(res.success)
        self.assertTrue(res.timed_out)
        self.assertIn("Timed Out", res.stderr)

    def test_python_execution_syntax_error(self):
        """Python script with syntax error should return exit_code 1 with error message."""
        code = "invalid python code format !!!"
        res = self.runner.run_code(code)
        self.assertFalse(res.success)
        self.assertEqual(res.exit_code, 1)
        self.assertIn("SyntaxError", res.stderr)


if __name__ == "__main__":
    unittest.main()
