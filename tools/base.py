"""
Abstract Base Tool definition and ToolResult dataclass.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional
from security.permissions import PermissionLevel


@dataclass
class ToolResult:
    """Dataclass holding tool execution outcome."""
    success: bool
    output: Any
    error: str = ""
    requires_confirmation: bool = False
    confirmation_reason: str = ""


class BaseTool(ABC):
    """Abstract Base Class for Agent Workstation Tools."""

    def __init__(
        self,
        name: str,
        description: str,
        permission_level: PermissionLevel,
        is_destructive: bool = False
    ):
        self.name = name
        self.description = description
        self.permission_level = permission_level
        self.is_destructive = is_destructive

    @abstractmethod
    def run(self, **kwargs) -> ToolResult:
        """Executes tool logic."""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Returns JSON schema definition for LLM tool selection."""
        return {
            "name": self.name,
            "description": self.description,
            "permission_level": self.permission_level.name,
            "is_destructive": self.is_destructive
        }
