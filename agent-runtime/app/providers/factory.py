"""
Provider Factory for Agent Runtime.
"""

from typing import Optional
from app.providers.base import BaseLLMProvider
from app.providers.offline_provider import OfflineProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.nvidia_nim_provider import NvidiaNimProvider
from app.config import RuntimeConfig


class ProviderFactory:
    """Creates configured LLM provider instances."""

    @staticmethod
    def create_provider(provider_name: Optional[str] = None, model_name: Optional[str] = None) -> BaseLLMProvider:
        name = (provider_name or RuntimeConfig.get_default_provider()).strip().lower()

        if name == "openai":
            key = RuntimeConfig.get_openai_api_key()
            if not key:
                return OfflineProvider()
            model = model_name or RuntimeConfig.get_openai_chat_model()
            return OpenAIProvider(api_key=key, model_name=model)

        elif name == "gemini":
            key = RuntimeConfig.get_gemini_api_key()
            if not key:
                return OfflineProvider()
            model = model_name or RuntimeConfig.get_gemini_chat_model()
            return GeminiProvider(api_key=key, model_name=model)

        elif name in ("nvidia", "nvidia_nim", "nim"):
            key = RuntimeConfig.get_nvidia_api_key()
            if not key:
                return OfflineProvider()
            model = model_name or RuntimeConfig.get_nvidia_chat_model()
            base_url = RuntimeConfig.get_nvidia_base_url()
            return NvidiaNimProvider(api_key=key, model_name=model, base_url=base_url)

        return OfflineProvider(model_name=model_name or "deterministic-offline")
