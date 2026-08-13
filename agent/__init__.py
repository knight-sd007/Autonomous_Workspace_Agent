"""Agent package entrypoint."""
from agent.prompts import WORKSTATION_AGENT_SYSTEM_PROMPT
from agent.orchestrator import WorkstationAgentOrchestrator

__all__ = ["WORKSTATION_AGENT_SYSTEM_PROMPT", "WorkstationAgentOrchestrator"]
