"""
Base Tool Interface for Agent Runtime.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional, Dict
from app.security.permissions import PermissionLevel


@dataclass
class ToolResult:
    """Standardized tool execution outcome."""
    success: bool
    output: Any
    error: Optional[str] = None
    requires_confirmation: bool = False
    confirmation_reason: Optional[str] = None


class BaseTool(ABC):
    """Abstract base class for all agent-invoked tools."""

    def __init__(
        self,
        name: str,
        description: str,
        permission_level: PermissionLevel = PermissionLevel.READ,
        is_destructive: bool = False
    ):
        self.name = name
        self.description = description
        self.permission_level = permission_level
        self.is_destructive = is_destructive

    @abstractmethod
    def run(self, **kwargs) -> ToolResult:
        """Executes tool action."""
        pass
