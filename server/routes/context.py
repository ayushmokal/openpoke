"""API routes for user context management."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from server.agents.execution_agent.tools.ultrahuman import (
    clear_user_context,
    get_user_context,
    has_context,
    set_user_context,
)
from server.logging_config import logger

router = APIRouter(prefix="/context", tags=["context"])


@router.post("/set")
async def set_context(payload: dict[str, Any]) -> dict[str, Any]:
    """Set user context from Yellow AI payload data.

    The payload can contain user data at:
    - payload.data.payload (from Yellow AI response)
    - payload.session.payload (from Yellow AI response)
    - Or directly the payload fields
    """
    try:
        logger.info(f"Received context payload with {len(payload)} keys: {list(payload.keys())[:10]}")
        set_user_context(payload)
        has_ctx = has_context()
        ctx = get_user_context()
        logger.info(f"Context set successfully. has_context={has_ctx}, keys={list(ctx.keys())[:10]}")
        return {
            "status": "success",
            "message": "User context set successfully",
            "has_context": has_ctx,
            "context_keys": list(ctx.keys())[:10],
        }
    except Exception as e:
        logger.exception("Error setting user context")
        return {
            "status": "error",
            "message": str(e),
        }


@router.get("/get")
async def get_context() -> dict[str, Any]:
    """Get the current user context."""
    return {
        "status": "success",
        "has_context": has_context(),
        "context": get_user_context(),
    }


@router.post("/clear")
async def clear_context() -> dict[str, Any]:
    """Clear the user context."""
    clear_user_context()
    return {
        "status": "success",
        "message": "User context cleared",
    }
