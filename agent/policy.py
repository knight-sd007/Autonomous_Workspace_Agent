"""
Agent Execution Policy Rules.
"""

from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class ExecutionPolicy:
    """Configurable agent execution policy rules."""
    max_steps: int = 10
    require_human_confirmation_for_destructive: bool = True
    require_human_confirmation_for_python_exec: bool = False
    require_human_confirmation_for_db_mutation: bool = True
