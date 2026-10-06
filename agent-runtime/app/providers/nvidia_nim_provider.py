"""
NVIDIA NIM (OpenAI-compatible) Provider Implementation.
"""

from typing import Dict, Any, List, Optional
from app.providers.openai_provider import OpenAIProvider


class NvidiaNimProvider(OpenAIProvider):
    """NVIDIA NIM Provider utilizing OpenAI-compatible API protocol."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "meta/llama-3.1-8b-instruct",
        base_url: str = "https://integrate.api.nvidia.com/v1"
    ):
        super().__init__(api_key=api_key, model_name=model_name, base_url=base_url)
        self.provider_name = "nvidia"
