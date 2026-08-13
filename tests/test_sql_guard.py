"""
Unit tests for SQL Guard Query Validation.
"""

import unittest
from database.sql_guard import SQLGuard, SQLClassification


class TestSQLGuard(unittest.TestCase):
    """Test suite verifying safe SELECT vs mutating/destructive SQL detection."""

    def test_safe_select_query(self):
        """Standard SELECT queries should be classified as safe READ_ONLY."""
        res = SQLGuard.analyze_query("SELECT id, name FROM users WHERE active = 1;")
        self.assertEqual(res.classification, SQLClassification.READ_ONLY)
        self.assertTrue(res.is_safe_read)
        self.assertFalse(res.requires_human_confirmation)

    def test_mutating_insert_query(self):
        """INSERT queries should be classified as MUTATING requiring confirmation."""
        res = SQLGuard.analyze_query("INSERT INTO users (name) VALUES ('Alice');")
        self.assertEqual(res.classification, SQLClassification.MUTATING)
        self.assertFalse(res.is_safe_read)
        self.assertTrue(res.requires_human_confirmation)

    def test_destructive_drop_query(self):
        """DROP TABLE queries must be classified as DESTRUCTIVE requiring confirmation."""
        res = SQLGuard.analyze_query("DROP TABLE users;")
        self.assertEqual(res.classification, SQLClassification.DESTRUCTIVE)
        self.assertFalse(res.is_safe_read)
        self.assertTrue(res.requires_human_confirmation)

    def test_multi_statement_mutation(self):
        """Multi-statement query with mutations requires human confirmation."""
        res = SQLGuard.analyze_query("SELECT 1; DELETE FROM users;")
        self.assertTrue(res.requires_human_confirmation)


if __name__ == "__main__":
    unittest.main()
