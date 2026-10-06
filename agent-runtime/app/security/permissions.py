"""
Tool Permission Matrix & Human-in-the-loop Confirmation Gate.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger("p07.security.permissions")


class PermissionLevel(Enum):
    """Explicit permission levels for workstation tool actions."""
    READ = auto()
    WRITE = auto()
    EXECUTE = auto()
    DATABASE = auto()
    DESTRUCTIVE = auto()


@dataclass
class ActionPermissionRequest:
    """Action request details submitted to permission gate."""
    tool_name: str
    action_type: PermissionLevel
    resource: str
    details: Dict[str, Any]
    is_destructive: bool = False
    rationale: str = ""


class PermissionGate:
    """
    Evaluates tool actions against security policies and determines
    whether human approval is mandatory prior to execution.
    """

    def __init__(self, enforce_human_confirmation: bool = True):
        self.enforce_human_confirmation = enforce_human_confirmation

    def evaluate_request(self, request: ActionPermissionRequest) -> Dict[str, Any]:
        """
        Evaluates permission request.
        Returns dictionary indicating status:
        - 'ALLOWED': Proceed directly.
        - 'NEEDS_CONFIRMATION': Pause for human user approval.
        - 'DENIED': Policy violation.
        """
        # Destructive operations ALWAYS require confirmation if enforcement enabled
        if request.is_destructive or request.action_type == PermissionLevel.DESTRUCTIVE:
            if self.enforce_human_confirmation:
                logger.info(f"Human confirmation REQUIRED for destructive tool '{request.tool_name}' on '{request.resource}'")
                return {
                    "status": "NEEDS_CONFIRMATION",
                    "reason": f"Action '{request.tool_name}' on resource '{request.resource}' is destructive.",
                    "request": request
                }

        # Write, Execute or Database operations require confirmation when enforcement enabled or marked destructive
        if request.action_type in (PermissionLevel.WRITE, PermissionLevel.EXECUTE, PermissionLevel.DATABASE):
            if self.enforce_human_confirmation or request.is_destructive:
                return {
                    "status": "NEEDS_CONFIRMATION",
                    "reason": f"Mutation action '{request.tool_name}' on '{request.resource}' requires explicit user consent.",
                    "request": request
                }

        return {
            "status": "ALLOWED",
            "reason": "Operation permitted under default workspace security policy.",
            "request": request
        }
