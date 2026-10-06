"""
SQLGuard: SQL Statement Classifier and Security Inspector for MCP Server.

Validates and classifies SQL statements into READ_ONLY, MUTATING, DESTRUCTIVE, or INVALID.
Guards SQLite database operations against unintended schema drops, destructive deletions,
and unauthorized data mutations.
"""

from enum import Enum, auto
from dataclasses import dataclass, asdict
import re
from typing import Dict, Any, Optional, List


class SQLClassification(Enum):
    """Classification levels for SQL operations."""
    READ_ONLY = auto()
    MUTATING = auto()
    DESTRUCTIVE = auto()
    INVALID = auto()


@dataclass
class SQLAnalysisResult:
    """Detailed result of SQLGuard query inspection."""
    classification: SQLClassification
    statement_type: str
    is_safe_read: bool
    is_destructive: bool
    requires_human_confirmation: bool
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "classification": self.classification.name,
            "statement_type": self.statement_type,
            "is_safe_read": self.is_safe_read,
            "is_destructive": self.is_destructive,
            "requires_human_confirmation": self.requires_human_confirmation,
            "reason": self.reason
        }


class SQLGuard:
    """Analyzes and enforces security boundaries on SQL queries."""

    MUTATING_KEYWORDS = {
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
        "CREATE", "REPLACE", "VACUUM", "REINDEX"
    }

    DESTRUCTIVE_KEYWORDS = {"DROP", "TRUNCATE", "ALTER"}

    @classmethod
    def analyze_query(cls, sql_query: str) -> SQLAnalysisResult:
        """
        Performs static AST/regex analysis of a SQL query string.
        Determines risk level and whether human confirmation is mandatory.
        """
        cleaned = sql_query.strip()
        if not cleaned:
            return SQLAnalysisResult(
                classification=SQLClassification.INVALID,
                statement_type="EMPTY",
                is_safe_read=False,
                is_destructive=False,
                requires_human_confirmation=False,
                reason="SQL query cannot be empty."
            )

        # Strip SQL comments to prevent bypasses
        sql_upper = re.sub(r'--.*$', '', cleaned, flags=re.MULTILINE).upper()
        sql_upper = re.sub(r'/\*.*?\*/', '', sql_upper, flags=re.DOTALL).strip()

        # Extract keywords
        words = re.findall(r'\b[A-Z]+\b', sql_upper)
        if not words:
            return SQLAnalysisResult(
                classification=SQLClassification.INVALID,
                statement_type="UNKNOWN",
                is_safe_read=False,
                is_destructive=False,
                requires_human_confirmation=False,
                reason="Unable to parse SQL keywords."
            )

        first_word = words[0]

        # Check for multiple statements separated by semicolon (potential multi-statement injection)
        statements = [s.strip() for s in sql_upper.split(';') if s.strip()]
        if len(statements) > 1:
            has_mutation = any(
                any(kw in stmt for kw in cls.MUTATING_KEYWORDS)
                for stmt in statements
            )
            has_destructive = any(
                any(kw in stmt for kw in cls.DESTRUCTIVE_KEYWORDS)
                for stmt in statements
            )
            if has_destructive:
                return SQLAnalysisResult(
                    classification=SQLClassification.DESTRUCTIVE,
                    statement_type="MULTI_STATEMENT",
                    is_safe_read=False,
                    is_destructive=True,
                    requires_human_confirmation=True,
                    reason="Multi-statement batch containing destructive operations requires explicit human approval."
                )
            if has_mutation:
                return SQLAnalysisResult(
                    classification=SQLClassification.MUTATING,
                    statement_type="MULTI_STATEMENT",
                    is_safe_read=False,
                    is_destructive=False,
                    requires_human_confirmation=True,
                    reason="Multi-statement batch containing mutations requires human approval."
                )

        # Destructive operations check (DROP, TRUNCATE, ALTER)
        for dest_kw in cls.DESTRUCTIVE_KEYWORDS:
            if re.search(rf'\b{dest_kw}\b', sql_upper):
                return SQLAnalysisResult(
                    classification=SQLClassification.DESTRUCTIVE,
                    statement_type=dest_kw,
                    is_safe_read=False,
                    is_destructive=True,
                    requires_human_confirmation=True,
                    reason=f"Destructive SQL statement '{dest_kw}' requires human confirmation."
                )

        # Unconstrained DELETE check (DELETE without WHERE is destructive)
        if re.search(r'\bDELETE\b', sql_upper):
            if not re.search(r'\bWHERE\b', sql_upper):
                return SQLAnalysisResult(
                    classification=SQLClassification.DESTRUCTIVE,
                    statement_type="DELETE_ALL",
                    is_safe_read=False,
                    is_destructive=True,
                    requires_human_confirmation=True,
                    reason="Unconstrained DELETE without WHERE clause is destructive."
                )
            else:
                return SQLAnalysisResult(
                    classification=SQLClassification.MUTATING,
                    statement_type="DELETE",
                    is_safe_read=False,
                    is_destructive=False,
                    requires_human_confirmation=True,
                    reason="DELETE statement modifies table rows and requires human approval."
                )

        # Mutating operations check (INSERT, UPDATE, CREATE, REPLACE, VACUUM, REINDEX)
        for mut_kw in cls.MUTATING_KEYWORDS:
            if re.search(rf'\b{mut_kw}\b', sql_upper):
                return SQLAnalysisResult(
                    classification=SQLClassification.MUTATING,
                    statement_type=mut_kw,
                    is_safe_read=False,
                    is_destructive=False,
                    requires_human_confirmation=True,
                    reason=f"SQL mutation operation '{mut_kw}' modifies database state and requires approval."
                )

        # Safe Read-Only statements (SELECT, PRAGMA, EXPLAIN, WITH)
        if first_word in ("SELECT", "PRAGMA", "EXPLAIN", "WITH"):
            return SQLAnalysisResult(
                classification=SQLClassification.READ_ONLY,
                statement_type=first_word,
                is_safe_read=True,
                is_destructive=False,
                requires_human_confirmation=False,
                reason="Safe read-only query."
            )

        return SQLAnalysisResult(
            classification=SQLClassification.MUTATING,
            statement_type=first_word,
            is_safe_read=False,
            is_destructive=False,
            requires_human_confirmation=True,
            reason=f"Unrecognized statement type '{first_word}' treated as mutating for security."
        )
