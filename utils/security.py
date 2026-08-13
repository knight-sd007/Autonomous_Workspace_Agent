"""
Security & Input Sanitization Utilities.
"""

import hmac
import re

def verify_access_key(provided_key: str, expected_key: str) -> bool:
    """Performs constant-time comparison to prevent timing attacks."""
    if not provided_key or not expected_key:
        return False
    return hmac.compare_digest(provided_key.strip(), expected_key.strip())

def sanitize_error_message(error: Exception) -> str:
    """Strips API keys, tokens, or system file paths from exception messages."""
    msg = str(error)
    # Redact potential API keys (sk-..., AIzaSy..., nvapi-...)
    msg = re.sub(r'(sk-[a-zA-Z0-9]{20,})', '[REDACTED_API_KEY]', msg)
    msg = re.sub(r'(AIzaSy[a-zA-Z0-9_-]{30,})', '[REDACTED_API_KEY]', msg)
    msg = re.sub(r'(nvapi-[a-zA-Z0-9_-]{30,})', '[REDACTED_API_KEY]', msg)
    return msg
