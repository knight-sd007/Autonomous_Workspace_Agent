"""
OpenAI Provider Implementation.
"""

import json
from typing import Dict, Any, List, Optional
import httpx
from app.providers.base import BaseLLMProvider, ProviderResponse, ToolCallRequest
from app.security.sanitizer import sanitize_error_message


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API Provider."""

    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini", base_url: str = "https://api.openai.com/v1"):
        super().__init__(provider_name="openai", model_name=model_name)
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 1024,
        temperature: float = 0.2
    ) -> ProviderResponse:
        if not self.api_key:
            raise ValueError("OpenAI API key is missing.")

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

                choice = data["choices"][0]
                message = choice["message"]
                content = message.get("content")
                tool_calls_raw = message.get("tool_calls", [])

                parsed_tool_calls = []
                for tc in tool_calls_raw:
                    fn = tc.get("function", {})
                    args = json.loads(fn.get("arguments", "{}"))
                    parsed_tool_calls.append(
                        ToolCallRequest(
                            id=tc.get("id", "call_1"),
                            tool_name=fn.get("name", ""),
                            arguments=args
                        )
                    )

                return ProviderResponse(
                    content=content,
                    tool_calls=parsed_tool_calls,
                    raw_response=data,
                    finish_reason=choice.get("finish_reason", "stop")
                )
            except Exception as e:
                clean_err = sanitize_error_message(e)
                raise RuntimeError(f"OpenAI Provider Error: {clean_err}") from None
