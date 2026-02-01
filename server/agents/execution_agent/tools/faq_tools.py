"""FAQ tool schemas and actions for the execution agent.

This module provides tools for searching the Ultrahuman CX Bible knowledge base.
"""

from __future__ import annotations

import inspect
from typing import Any, Callable, Dict, List

from server.services.execution import get_execution_agent_logs

from .faq_search import (
    FAQ_TOOL_FUNCTIONS,
    FAQ_TOOL_SCHEMAS,
)

_LOG_STORE = get_execution_agent_logs()


def _convert_to_openai_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Convert our tool schema format to OpenAI/OpenRouter compatible format."""
    return {
        "type": "function",
        "function": {
            "name": schema["name"],
            "description": schema["description"],
            "parameters": schema["input_schema"],
        },
    }


_SCHEMAS: List[Dict[str, Any]] = [
    _convert_to_openai_schema(schema) for schema in FAQ_TOOL_SCHEMAS
]


def get_schemas() -> List[Dict[str, Any]]:
    """Return FAQ tool schemas in OpenAI/OpenRouter format."""
    return _SCHEMAS


def _wrap_tool_with_logging(
    tool_name: str,
    tool_fn: Callable[..., Any],
    agent_name: str,
) -> Callable[..., Any]:
    """Wrap a tool function with logging."""

    async def wrapper(**kwargs: Any) -> Dict[str, Any]:
        try:
            # Call the async tool function
            if inspect.iscoroutinefunction(tool_fn):
                result = await tool_fn(**kwargs)
            else:
                result = tool_fn(**kwargs)

            # Log success
            _LOG_STORE.record_action(
                agent_name,
                description=f"{tool_name} succeeded | args={kwargs}",
            )
            return result
        except Exception as exc:
            # Log failure
            _LOG_STORE.record_action(
                agent_name,
                description=f"{tool_name} failed | args={kwargs} | error={exc}",
            )
            return {"error": str(exc)}

    return wrapper


def build_registry(agent_name: str) -> Dict[str, Callable[..., Any]]:
    """Return FAQ tool callables bound to a specific agent."""
    registry: Dict[str, Callable[..., Any]] = {}

    for tool_name, tool_fn in FAQ_TOOL_FUNCTIONS.items():
        # Wrap with logging
        wrapped = _wrap_tool_with_logging(tool_name, tool_fn, agent_name)
        registry[tool_name] = wrapped

    return registry


__all__ = [
    "build_registry",
    "get_schemas",
]
