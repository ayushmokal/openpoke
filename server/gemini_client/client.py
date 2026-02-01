"""Gemini API client for chat completions."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx

from ..config import get_settings

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiError(RuntimeError):
    """Raised when the Gemini API returns an error response."""


def _convert_messages_to_gemini(
    messages: List[Dict[str, str]], system: Optional[str] = None
) -> tuple[List[Dict[str, Any]], Optional[str]]:
    """Convert OpenAI-style messages to Gemini format."""
    contents = []
    system_instruction = system

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role == "system":
            # Gemini handles system as separate instruction
            system_instruction = content
            continue

        # Map roles: user -> user, assistant -> model
        gemini_role = "model" if role == "assistant" else "user"

        contents.append({
            "role": gemini_role,
            "parts": [{"text": content}]
        })

    return contents, system_instruction


def _clean_parameters_for_gemini(params: Dict[str, Any]) -> Dict[str, Any]:
    """Remove fields not supported by Gemini from parameter definitions."""
    if not isinstance(params, dict):
        return params

    # Fields not supported by Gemini
    unsupported_fields = {"additionalProperties", "$schema", "default"}

    cleaned = {}
    for key, value in params.items():
        if key in unsupported_fields:
            continue
        if key == "properties" and isinstance(value, dict):
            # Recursively clean property definitions
            cleaned[key] = {
                prop_name: _clean_parameters_for_gemini(prop_value)
                for prop_name, prop_value in value.items()
            }
        elif isinstance(value, dict):
            cleaned[key] = _clean_parameters_for_gemini(value)
        else:
            cleaned[key] = value

    return cleaned


def _convert_tools_to_gemini(tools: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
    """Convert OpenAI-style tools to Gemini function declarations."""
    if not tools:
        return None

    function_declarations = []
    for tool in tools:
        if tool.get("type") == "function":
            func = tool.get("function", {})
            params = func.get("parameters", {"type": "object", "properties": {}})
            cleaned_params = _clean_parameters_for_gemini(params)
            function_declarations.append({
                "name": func.get("name"),
                "description": func.get("description", ""),
                "parameters": cleaned_params
            })

    if not function_declarations:
        return None

    return [{"functionDeclarations": function_declarations}]


def _convert_gemini_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Gemini response to OpenAI-compatible format."""
    candidates = response.get("candidates", [])
    if not candidates:
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "No response generated."
                }
            }]
        }

    candidate = candidates[0]
    content = candidate.get("content", {})
    parts = content.get("parts", [])

    # Check for function calls
    tool_calls = []
    text_content = ""

    for part in parts:
        if "text" in part:
            text_content += part["text"]
        elif "functionCall" in part:
            func_call = part["functionCall"]
            tool_calls.append({
                "id": f"call_{func_call.get('name', 'unknown')}",
                "type": "function",
                "function": {
                    "name": func_call.get("name"),
                    "arguments": json.dumps(func_call.get("args", {}))
                }
            })

    message: Dict[str, Any] = {
        "role": "assistant",
        "content": text_content
    }

    if tool_calls:
        message["tool_calls"] = tool_calls

    return {
        "choices": [{
            "message": message,
            "finish_reason": candidate.get("finishReason", "stop")
        }],
        "usage": response.get("usageMetadata", {})
    }


async def request_chat_completion(
    *,
    model: str,
    messages: List[Dict[str, str]],
    system: Optional[str] = None,
    api_key: Optional[str] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    base_url: str = GEMINI_BASE_URL,
) -> Dict[str, Any]:
    """Request a chat completion from Gemini and return OpenAI-compatible format."""

    settings = get_settings()
    key = (api_key or settings.gemini_api_key or "").strip()
    if not key:
        raise GeminiError("Missing Gemini API key")

    # Convert messages to Gemini format
    contents, system_instruction = _convert_messages_to_gemini(messages, system)

    # Build payload
    payload: Dict[str, Any] = {
        "contents": contents
    }

    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }

    # Convert and add tools if present
    gemini_tools = _convert_tools_to_gemini(tools)
    if gemini_tools:
        payload["tools"] = gemini_tools

    # Build URL with API key
    url = f"{base_url.rstrip('/')}/models/{model}:generateContent?key={key}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=60.0,
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                detail: str
                try:
                    error_payload = exc.response.json()
                    detail = error_payload.get("error", {}).get("message", str(error_payload))
                except Exception:
                    detail = exc.response.text
                raise GeminiError(f"Gemini request failed ({exc.response.status_code}): {detail}") from exc

            gemini_response = response.json()
            return _convert_gemini_response(gemini_response)

        except httpx.HTTPError as exc:
            raise GeminiError(f"Gemini request failed: {exc}") from exc

    raise GeminiError("Gemini request failed: unknown error")


__all__ = ["GeminiError", "request_chat_completion", "GEMINI_BASE_URL"]
