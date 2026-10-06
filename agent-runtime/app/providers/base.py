"""
Base Provider Interface for LLM Integrations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class ToolCallRequest:
    """Standardized representation of an agent tool call."""
    id: str
    tool_name: str
    arguments: Dict[str, Any]


@dataclass
class ProviderResponse:
    """Standardized provider response."""
    content: Optional[str] = None
    tool_calls: List[ToolCallRequest] = field(default_factory=list)
    raw_response: Optional[Any] = None
    finish_reason: str = "stop"


class BaseLLMProvider(ABC):
    """Abstract interface for all supported LLM providers."""

    def __init__(self, provider_name: str, model_name: str):
        self.provider_name = provider_name
        self.model_name = model_name

    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 1024,
        temperature: float = 0.2
    ) -> ProviderResponse:
        """Executes LLM chat completion request."""
        pass
