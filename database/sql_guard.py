"""
SQL Query Validator & Mutation Inspector.

Differentiates Read-Only SQL (SELECT, PRAGMA) from Mutating SQL (INSERT, UPDATE, DELETE, DROP, ALTER)
and identifies potentially destructive queries.
"""

from enum import Enum, auto
from dataclasses import dataclass
import re
from typing import Dict, Any


class SQLClassification(Enum):
    """SQL query operation classification."""
    READ_ONLY = auto()
    MUTATING = auto()
    DESTRUCTIVE = auto()
    INVALID = auto()


@dataclass
class SQLAnalysisResult:
    """SQL analysis details."""
    classification: SQLClassification
    statement_type: str
    is_safe_read: bool
    requires_human_confirmation: bool
    reason: str


class SQLGuard:
    """Validates SQL query strings before database execution."""

    MUTATING_KEYWORDS = {
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
        "CREATE", "REPLACE", "VACUUM", "REINDEX"
    }

    DESTRUCTIVE_KEYWORDS = {"DROP", "TRUNCATE", "DELETE"}

    @classmethod
    def analyze_query(cls, sql_query: str) -> SQLAnalysisResult:
        """
        Analyzes a SQL query statement.
        Determines if it is read-only, mutating, or destructive.
        """
        cleaned = sql_query.strip()
        if not cleaned:
            return SQLAnalysisResult(
                classification=SQLClassification.INVALID,
                statement_type="EMPTY",
                is_safe_read=False,
                requires_human_confirmation=False,
                reason="Query is empty."
            )

        # Normalize SQL for keyword scanning (ignore comments)
        sql_upper = re.sub(r'--.*$', '', cleaned, flags=re.MULTILINE).upper()
        sql_upper = re.sub(r'/\*.*?\*/', '', sql_upper, flags=re.DOTALL).strip()

        # Identify leading command keyword
        words = re.findall(r'\b[A-Z]+\b', sql_upper)
        first_word = words[0] if words else ""

        # Check for multiple statements separated by semicolon (potential injection)
        statements = [s.strip() for s in sql_upper.split(';') if s.strip()]
        if len(statements) > 1:
            # Check if any statement contains mutating keywords
            has_mutation = any(
                any(kw in stmt for kw in cls.MUTATING_KEYWORDS)
                for stmt in statements
            )
            if has_mutation:
                return SQLAnalysisResult(
                    classification=SQLClassification.MUTATING,
                    statement_type="MULTI_STATEMENT",
                    is_safe_read=False,
                    requires_human_confirmation=True,
                    reason="Multi-statement batch containing schema/data mutations requires explicit approval."
                )

        # Destructive Keyword check
        for dest_kw in cls.DESTRUCTIVE_KEYWORDS:
            if re.search(rf'\b{dest_kw}\b', sql_upper):
                return SQLAnalysisResult(
                    classification=SQLClassification.DESTRUCTIVE,
                    statement_type=dest_kw,
                    is_safe_read=False,
                    requires_human_confirmation=True,
                    reason=f"Destructive SQL operation '{dest_kw}' requires human confirmation."
                )

        # Mutating Keyword check
        for mut_kw in cls.MUTATING_KEYWORDS:
            if re.search(rf'\b{mut_kw}\b', sql_upper):
                return SQLAnalysisResult(
                    classification=SQLClassification.MUTATING,
                    statement_type=mut_kw,
                    is_safe_read=False,
                    requires_human_confirmation=True,
                    reason=f"Data/Schema mutation operation '{mut_kw}' requires human confirmation."
                )

        # If statement starts with SELECT, PRAGMA, EXPLAIN, or WITH
        if first_word in ("SELECT", "PRAGMA", "EXPLAIN", "WITH"):
            return SQLAnalysisResult(
                classification=SQLClassification.READ_ONLY,
                statement_type=first_word,
                is_safe_read=True,
                requires_human_confirmation=False,
                reason="Safe read-only query."
            )

        return SQLAnalysisResult(
            classification=SQLClassification.MUTATING,
            statement_type=first_word,
            is_safe_read=False,
            requires_human_confirmation=True,
            reason=f"Unrecognized or custom statement '{first_word}' treated as mutating for safety."
        )
