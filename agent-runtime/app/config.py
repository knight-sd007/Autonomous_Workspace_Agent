"""
Configuration layer for Python Agent Runtime.
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class RuntimeConfig:
    """Type-safe configuration settings retrieval for agent runtime."""

    @staticmethod
    def get_service_key() -> str:
        return os.getenv("INTERNAL_SERVICE_KEY", "p07_dev_internal_key").strip()

    @staticmethod
    def get_default_provider() -> str:
        return os.getenv("AI_PROVIDER", "offline").strip().lower()

    @staticmethod
    def get_openai_api_key() -> str:
        return os.getenv("OPENAI_API_KEY", "").strip()

    @staticmethod
    def get_openai_chat_model() -> str:
        return os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini").strip()

    @staticmethod
    def get_gemini_api_key() -> str:
        return os.getenv("GEMINI_API_KEY", "").strip()

    @staticmethod
    def get_gemini_chat_model() -> str:
        return os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash").strip()

    @staticmethod
    def get_nvidia_api_key() -> str:
        return os.getenv("NVIDIA_API_KEY", "").strip()

    @staticmethod
    def get_nvidia_base_url() -> str:
        return os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1").strip()

    @staticmethod
    def get_nvidia_chat_model() -> str:
        return os.getenv("NVIDIA_CHAT_MODEL", "meta/llama-3.1-8b-instruct").strip()

    @staticmethod
    def get_workspace_dir() -> Path:
        raw_path = os.getenv("WORKSPACE_DIR", "workspace").strip()
        # Resolve relative to project root
        base_dir = Path(__file__).resolve().parent.parent.parent
        resolved = (base_dir / raw_path).resolve()
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved

    @staticmethod
    def get_python_timeout() -> int:
        val = os.getenv("MAX_PYTHON_TIMEOUT_SECONDS", "10")
        try:
            return max(1, int(val))
        except ValueError:
            return 10

    @staticmethod
    def require_human_confirmation() -> bool:
        val = os.getenv("REQUIRE_HUMAN_CONFIRMATION_FOR_MUTATION", "true").lower()
        return val in ("true", "1", "yes")
