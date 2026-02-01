"""Context store for Yellow AI payload data.

This module stores user context data from Yellow AI payload that can be used
by tools instead of making API calls (useful when APIs return 401 or for testing).
"""

from __future__ import annotations

from typing import Any, Optional
from server.logging_config import logger

# Global context store
_user_context: dict[str, Any] = {}


def set_user_context(payload: dict[str, Any]) -> None:
    """Set user context from Yellow AI payload data.

    The payload should contain user data at:
    - payload.data.payload (from Yellow AI response)
    - payload.session.payload (from Yellow AI response)
    - Or directly the payload fields
    """
    global _user_context

    # Try to extract from nested structure
    if isinstance(payload, dict):
        if "data" in payload and isinstance(payload["data"], dict):
            if "payload" in payload["data"]:
                _user_context = payload["data"]["payload"]
                logger.info("User context set from data.payload")
                return
        if "session" in payload and isinstance(payload["session"], dict):
            if "payload" in payload["session"]:
                _user_context = payload["session"]["payload"]
                logger.info("User context set from session.payload")
                return
        # Assume it's already the payload fields
        _user_context = payload
        logger.info("User context set directly")
    else:
        logger.warning("Invalid payload format for user context")


def get_user_context() -> dict[str, Any]:
    """Get the current user context."""
    return _user_context.copy()


def clear_user_context() -> None:
    """Clear the user context."""
    global _user_context
    _user_context = {}
    logger.info("User context cleared")


def get_context_value(key: str, default: Any = None) -> Any:
    """Get a specific value from user context."""
    return _user_context.get(key, default)


def has_context() -> bool:
    """Check if user context is available."""
    return bool(_user_context)


# Helper functions to get specific data from context
def get_battery_context() -> dict[str, Any]:
    """Get battery-related data from context."""
    ctx = _user_context
    return {
        "battery_health_score": ctx.get("batteryHealthScoreStr"),
        "battery_ts_sessions": ctx.get("batteryTsSessionsStr"),
        "current_battery_level": ctx.get("currentBatteryLevelStr"),
        "avg_wear_time": ctx.get("avgWearTimeStr"),
        "last_100_charged": ctx.get("last100ChargedStr"),
        "bdr_triggered": ctx.get("bdrTriggeredStr"),
        "bdr_completed": ctx.get("bdrCompletedStr"),
        "bdr_value": ctx.get("bdrValueStr"),
        "days_since_bdr": ctx.get("daysSinceBdrStr"),
        "bdr_time_left": ctx.get("bdrTimeLeftStr"),
    }


def get_device_context() -> dict[str, Any]:
    """Get device-related data from context."""
    ctx = _user_context
    return {
        "ring_serial_number": ctx.get("ringSerialNumberStr"),
        "ring_description": ctx.get("ringDescriptionStr"),
        "ring_firmware_version": ctx.get("ringFirmwareVersionStr"),
        "latest_firmware_available": ctx.get("latestFirmwareAvailableForUserStr"),
        "ring_connected_last_24hrs": ctx.get("ringConnectedLast24HrsStr"),
        "days_since_activation": ctx.get("noOfDaysSinceRingActivationStr"),
        "last_ring_states_timestamp": ctx.get("lastRingStatesTimestampStr"),
        "device_model": ctx.get("deviceModelStr"),
        "device_os": ctx.get("deviceOsStr"),
        "app_version": ctx.get("appVersionStr"),
        "latest_app_version": ctx.get("latestAvailableAppVersionStr"),
        "platform": ctx.get("Platform"),
    }


def get_warranty_context() -> dict[str, Any]:
    """Get warranty and replacement data from context."""
    ctx = _user_context
    return {
        "policy_status": ctx.get("policyStatusStr"),
        "warranty_expiry_date": ctx.get("warrantyExpiryDateStr"),
        "days_until_warranty_expiry": ctx.get("daysUntilWarrantyExpiryStr"),
        "replacement_eligible": ctx.get("replacementEligibleStr"),
        "replacement_count": ctx.get("replacementCountStr"),
        "max_replacements": ctx.get("maxReplacementsStr"),
        "wabi_sabi_replacement_count": ctx.get("wabiSabiReplacementCountStr"),
    }


def get_user_info_context() -> dict[str, Any]:
    """Get user info from context."""
    ctx = _user_context
    return {
        "name": ctx.get("nameStr"),
        "email": ctx.get("emailIdStr") or ctx.get("userEmail"),
        "uhx_user": ctx.get("uhXUserStr"),
        "vip_user": ctx.get("vipUserStr"),
        "uhx_plan_name": ctx.get("uhxPlanNameStr"),
        "uhx_expiry": ctx.get("uhxExpiryStr"),
        "data_sharing": ctx.get("dataSharingStr"),
    }


def get_reset_context() -> dict[str, Any]:
    """Get reset-related data from context."""
    ctx = _user_context
    soft_reset_str = ctx.get("softResetStr")
    factory_reset_str = ctx.get("factoryResetStr")

    # Parse reset status from strings
    soft_reset_done = soft_reset_str and soft_reset_str.lower() not in ["never", "none", "n/a", ""]
    hard_reset_done = factory_reset_str and factory_reset_str.lower() not in ["never", "none", "n/a", ""]

    return {
        "soft_reset_done": soft_reset_done,
        "hard_reset_done": hard_reset_done,
        "soft_reset_date": soft_reset_str if soft_reset_done else None,
        "hard_reset_date": factory_reset_str if hard_reset_done else None,
    }


def get_order_context() -> dict[str, Any]:
    """Get order-related data from context."""
    ctx = _user_context
    return {
        "latest_order_id": ctx.get("latestOrderIdStr"),
        "latest_order_status": ctx.get("latestOrderStatusStr"),
        "tracking_url": ctx.get("trackingUrlStr"),
        "order_source": ctx.get("orderSourceStr"),
        "order_date": ctx.get("orderDateStr"),
        "shipping_address": ctx.get("shippingAddressStr"),
        "shipping_country": ctx.get("shippingCountryStr"),
    }


__all__ = [
    "set_user_context",
    "get_user_context",
    "clear_user_context",
    "get_context_value",
    "has_context",
    "get_battery_context",
    "get_device_context",
    "get_warranty_context",
    "get_user_info_context",
    "get_reset_context",
    "get_order_context",
]
