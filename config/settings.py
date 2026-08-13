"""
Centralized Configuration Manager for Autonomous Workspace Agent.
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Config:
    """Type-safe configuration settings retrieval."""

    @staticmethod
    def _get_val(key: str, default: str = "") -> str:
        """Helper to retrieve key from st.secrets or os.getenv."""
        try:
            import streamlit as st
            if hasattr(st, "secrets") and key in st.secrets:
                val = st.secrets[key]
                if val is not None:
                    return str(val).strip()
        except Exception:
            pass

        val = os.getenv(key, default)
        return str(val).strip() if val is not None else default

    @classmethod
    def get_app_access_key(cls) -> str:
        """Returns application access key."""
        return cls._get_val("APP_ACCESS_KEY", "admin123")

    @classmethod
    def get_ai_provider(cls) -> str:
        """Returns default AI provider selection (openai, gemini)."""
        return cls._get_val("AI_PROVIDER", "openai")

    @classmethod
    def get_openai_api_key(cls) -> str:
        """Returns OpenAI API key."""
        return cls._get_val("OPENAI_API_KEY", "")

    @classmethod
    def get_openai_chat_model(cls) -> str:
        """Returns OpenAI chat model name."""
        return cls._get_val("OPENAI_CHAT_MODEL", "gpt-4o-mini")

    @classmethod
    def get_gemini_api_key(cls) -> str:
        """Returns Google Gemini API key."""
        return cls._get_val("GEMINI_API_KEY", "")

    @classmethod
    def get_gemini_chat_model(cls) -> str:
        """Returns Gemini chat model name."""
        return cls._get_val("GEMINI_CHAT_MODEL", "gemini-2.5-flash")

    @classmethod
    def get_workspace_dir(cls) -> Path:
        """Returns resolved Path object for workspace sandbox root."""
        raw_path = cls._get_val("WORKSPACE_DIR", "workspace")
        base_dir = Path(__file__).resolve().parent.parent
        resolved = (base_dir / raw_path).resolve()
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved

    @classmethod
    def get_python_timeout(cls) -> int:
        """Returns maximum Python process execution timeout in seconds."""
        val = cls._get_val("MAX_PYTHON_TIMEOUT_SECONDS", "10")
        try:
            return max(1, int(val))
        except ValueError:
            return 10

    @classmethod
    def require_human_confirmation(cls) -> bool:
        """Returns True if human confirmation is enabled for mutations."""
        val = cls._get_val("REQUIRE_HUMAN_CONFIRMATION_FOR_MUTATION", "true").lower()
        return val in ("true", "1", "yes")
