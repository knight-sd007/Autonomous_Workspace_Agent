"""
Google Gemini Provider Implementation.
"""

from typing import Dict, Any, List, Optional
import httpx
from app.providers.base import BaseLLMProvider, ProviderResponse, ToolCallRequest
from app.security.sanitizer import sanitize_error_message


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API Provider."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        super().__init__(provider_name="gemini", model_name=model_name)
        self.api_key = api_key

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 1024,
        temperature: float = 0.2
    ) -> ProviderResponse:
        if not self.api_key:
            raise ValueError("Google Gemini API key is missing.")

        # Convert messages to Gemini format
        contents = []
        system_instruction = None
        for m in messages:
            role = m.get("role")
            text = m.get("content", "")
            if role == "system":
                system_instruction = {"parts": [{"text": text}]}
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": text}]})
            elif role == "assistant" or role == "agent":
                contents.append({"role": "model", "parts": [{"text": text}]})

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

                candidates = data.get("candidates", [])
                if not candidates:
                    return ProviderResponse(content="No response generated.", tool_calls=[], finish_reason="stop")

                candidate = candidates[0]
                content_parts = candidate.get("content", {}).get("parts", [])
                text_out = "".join(p.get("text", "") for p in content_parts if "text" in p)

                return ProviderResponse(
                    content=text_out,
                    tool_calls=[],
                    raw_response=data,
                    finish_reason=candidate.get("finishReason", "stop")
                )
            except Exception as e:
                clean_err = sanitize_error_message(e)
                raise RuntimeError(f"Gemini Provider Error: {clean_err}") from None
