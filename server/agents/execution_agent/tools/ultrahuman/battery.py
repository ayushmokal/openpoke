"""Battery and device-related tools for Ultrahuman Ring."""

from __future__ import annotations

from typing import Any
from datetime import datetime, timedelta

from .client import get_ultrahuman_client
from .context import (
    has_context,
    get_battery_context,
    get_device_context,
    get_reset_context,
    get_warranty_context,
    get_context_value,
    get_user_context,
)
from server.logging_config import logger


# Tool schemas for LLM
BATTERY_TOOL_SCHEMAS = [
    {
        "name": "ultrahuman_check_charger_status",
        "description": """Check charger LED status to diagnose if the issue is with the charger or the ring.
Ask the user what they see when placing the ring on the charger:
- Green or Red LED = Charger working, proceed with ring troubleshooting
- No LED at all = Likely charger issue, offer charger replacement
- Purple LED stuck = Charger malfunction, offer charger replacement

Use this FIRST when user reports charging issues like 'not charging', 'won't charge', or 'charger not working'.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "led_status": {
                    "type": "string",
                    "enum": ["green", "red", "none", "purple_stuck"],
                    "description": "What the user sees on the charger LED"
                }
            },
            "required": ["led_status"],
        },
    },
    {
        "name": "ultrahuman_check_troubleshooting_history",
        "description": """Check what troubleshooting steps the user has already tried within relevant time windows.
Returns:
- 'soft_reset_done_within_7_days' → Skip to factory reset
- 'factory_reset_done_within_7_days' → Skip to chill mode check
- 'no_recent_attempts' → Start normal troubleshooting flow

Use this to AVOID suggesting steps the user has already tried recently.""",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "ultrahuman_confirm_wear_status",
        "description": """When system shows insufficient wear data, ask user if they actually wear the ring consistently.
If user confirms YES (8+ hours/day), BYPASS the insufficient wear block and proceed with troubleshooting.
This fixes the issue where 15% of users get stuck despite wearing the ring consistently.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_confirms_consistent_wear": {
                    "type": "boolean",
                    "description": "True if user confirms they wear ring 8+ hours/day"
                }
            },
            "required": ["user_confirms_consistent_wear"],
        },
    },
    {
        "name": "ultrahuman_get_reset_status",
        "description": "Check if a soft reset or hard reset has been performed on the user's Ultrahuman ring. Returns reset status and dates.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "ultrahuman_trigger_soft_reset",
        "description": "Queue a soft reset command for the user's Ultrahuman ring. Use this when troubleshooting battery or connectivity issues.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "ultrahuman_get_ring_battery_info",
        "description": "Get detailed battery information for the user's ring including battery life at current BDR, chill mode status, and CDT events count.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "ultrahuman_get_device_info",
        "description": "Get device and ring information including serial number, firmware version, app version, warranty status, and replacement eligibility.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "ultrahuman_battery_troubleshoot",
        "description": """Run the battery troubleshooting flow for the user's ring. This follows the standard battery troubleshooting decision tree:
1. Check if user is on latest app version
2. Check BDR status (Battery Drain Rate): ≤1.4 is normal, >1.4 is high, or calibrating/not available
3. Check if user is on latest firmware version
4. Check CDT (Workout/Breathwork) usage in last 3 days
5. Check if Chill Mode is active
6. Check if soft/hard reset has been done
7. Recommend appropriate action based on findings

Returns a structured analysis with recommended next steps. NO EMAIL NEEDED - uses cached user context.""",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


def _get_ctx_value(key: str, default: Any = None) -> Any:
    """Get value from context, trying both with and without 'Str' suffix."""
    ctx = get_user_context()
    # Try with Str suffix first
    value = ctx.get(f"{key}Str")
    if value is not None:
        return value
    # Try without suffix
    value = ctx.get(key)
    if value is not None:
        return value
    # Try camelCase variations
    camel_key = key[0].lower() + key[1:] if key else key
    value = ctx.get(camel_key)
    if value is not None:
        return value
    return default


async def ultrahuman_check_charger_status(led_status: str) -> dict[str, Any]:
    """
    Diagnose charger vs ring issues based on LED status.

    Args:
        led_status: What user sees on charger ('green', 'red', 'none', 'purple_stuck')

    Returns:
        Diagnosis and recommended action
    """
    diagnoses = {
        "green": {
            "status": "success",
            "diagnosis": "ring_issue",
            "charger_working": True,
            "message": "Green LED indicates charger is working and ring is charging normally. Proceed with ring troubleshooting.",
            "next_action": "continue_ring_troubleshooting"
        },
        "red": {
            "status": "success",
            "diagnosis": "ring_issue",
            "charger_working": True,
            "message": "Red LED indicates charger is working, ring battery is low and charging. Proceed with ring troubleshooting.",
            "next_action": "continue_ring_troubleshooting"
        },
        "none": {
            "status": "success",
            "diagnosis": "charger_issue",
            "charger_working": False,
            "message": "No LED indicates a potential charger issue. Try: 1) Different USB port/adapter, 2) Clean charger contacts. If issue persists, recommend charger replacement.",
            "next_action": "charger_troubleshooting",
            "troubleshooting_steps": [
                "Try a different USB port or power adapter",
                "Clean the charger contacts with a dry cloth",
                "Ensure the ring is properly seated on the charger"
            ]
        },
        "purple_stuck": {
            "status": "success",
            "diagnosis": "charger_issue",
            "charger_working": False,
            "message": "Stuck purple LED indicates a charger malfunction. Recommend charger replacement.",
            "next_action": "charger_replacement"
        }
    }

    result = diagnoses.get(led_status, {
        "status": "error",
        "message": f"Unknown LED status: {led_status}. Valid options: green, red, none, purple_stuck"
    })

    logger.info(f"Charger diagnosis: {led_status} -> {result.get('diagnosis', 'unknown')}")
    return result


async def ultrahuman_check_troubleshooting_history() -> dict[str, Any]:
    """
    Check troubleshooting history to detect what user has already tried.

    This helps avoid suggesting redundant troubleshooting steps.
    Returns status indicating what was done within relevant time windows.
    """
    if not has_context():
        return {"status": "no_context", "message": "No context data available"}

    soft_reset_date = _get_ctx_value("softReset")
    factory_reset_date = _get_ctx_value("factoryReset")

    # Parse dates and check time windows
    soft_parsed = _parse_reset_date(soft_reset_date)
    factory_parsed = _parse_reset_date(factory_reset_date)

    now = datetime.now()
    seven_days_ago = now - timedelta(days=7)

    result = {
        "status": "success",
        "soft_reset_date": soft_reset_date,
        "factory_reset_date": factory_reset_date,
        "history_status": "no_recent_attempts",
        "skip_to": None,
        "message": "No recent troubleshooting attempts found. Start normal flow."
    }

    # Check factory reset first (more significant)
    if factory_parsed and factory_parsed > seven_days_ago:
        result["history_status"] = "factory_reset_done_within_7_days"
        result["skip_to"] = "chill_mode_check"
        result["message"] = f"Factory reset done on {factory_reset_date} (within 7 days). Skip to chill mode verification."
        logger.info(f"Troubleshooting history: factory reset within 7 days")
        return result

    # Check soft reset
    if soft_parsed and soft_parsed > seven_days_ago:
        result["history_status"] = "soft_reset_done_within_7_days"
        result["skip_to"] = "factory_reset"
        result["message"] = f"Soft reset done on {soft_reset_date} (within 7 days). Skip to factory reset."
        logger.info(f"Troubleshooting history: soft reset within 7 days")
        return result

    logger.info("Troubleshooting history: no recent attempts")
    return result


async def ultrahuman_confirm_wear_status(user_confirms_consistent_wear: bool) -> dict[str, Any]:
    """
    Handle user confirmation of wear status to bypass insufficient wear blocks.

    When system shows insufficient wear data but user confirms they wear the ring
    consistently (8+ hours/day), we should bypass and proceed with troubleshooting.

    Args:
        user_confirms_consistent_wear: True if user confirms consistent wear

    Returns:
        Whether to proceed with troubleshooting
    """
    if user_confirms_consistent_wear:
        return {
            "status": "success",
            "proceed_with_troubleshooting": True,
            "message": "User confirms consistent wear. Proceeding with battery troubleshooting despite low system data.",
            "reason": "System wear data may be incomplete or delayed. User confirmation takes precedence."
        }
    else:
        return {
            "status": "success",
            "proceed_with_troubleshooting": False,
            "message": "User indicates inconsistent wear. Recommend wearing ring 8+ hours daily for 7 days before reassessing battery.",
            "recommendation": "wear_more",
            "guidance": "For accurate battery assessment, please wear your ring for at least 8 hours daily for the next 7 days. If the issue persists after consistent wear, please reach out again."
        }


async def ultrahuman_get_reset_status() -> dict[str, Any]:
    """Check if soft/hard reset has been performed on the user's ring."""
    if has_context():
        reset_ctx = get_reset_context()
        logger.info("Using context data for reset status")
        return {
            "status": "success",
            "source": "context",
            "soft_reset_done": reset_ctx["soft_reset_done"],
            "hard_reset_done": reset_ctx["hard_reset_done"],
            "soft_reset_date": reset_ctx["soft_reset_date"],
            "hard_reset_date": reset_ctx["hard_reset_date"],
        }

    return {"status": "error", "message": "No context data available"}


async def ultrahuman_trigger_soft_reset() -> dict[str, Any]:
    """Queue a soft reset command for the user's ring."""
    try:
        client = get_ultrahuman_client()
        response = await client.post("/api/v4/yellow/trigger_soft_reset")
        if response.get("status") == "error":
            return {"error": response.get("error", {}).get("message", "Unknown error")}
        return {
            "status": "success",
            "message": response.get("data", {}).get("message", "Soft reset command queued successfully"),
        }
    except Exception as e:
        logger.exception("Error triggering soft reset")
        return {"error": str(e)}


async def ultrahuman_get_ring_battery_info() -> dict[str, Any]:
    """Get battery information for the user's ring."""
    if has_context():
        logger.info("Using context data for battery info")
        return {
            "status": "success",
            "source": "context",
            "battery_health_score": _get_ctx_value("batteryHealthScore"),
            "current_battery_level": _get_ctx_value("currentBatteryLevel"),
            "bdr_value": _get_ctx_value("bdrValue"),
            "bdr_triggered": _get_ctx_value("bdrTriggered"),
            "bdr_completed": _get_ctx_value("bdrCompleted"),
            "days_since_bdr": _get_ctx_value("daysSinceBdr"),
            "bdr_time_left": _get_ctx_value("bdrTimeLeft"),
            "avg_wear_time": _get_ctx_value("avgWearTime"),
            "chill_mode_active": _get_ctx_value("chill_mode_active"),
            "cdt_events_count_last_3_days": _get_ctx_value("cdt_events_count_last_3_days"),
        }
    return {"status": "error", "message": "No context data available"}


async def ultrahuman_get_device_info() -> dict[str, Any]:
    """Get device and ring information."""
    if has_context():
        logger.info("Using context data for device info")
        return {
            "status": "success",
            "source": "context",
            "ring_serial_number": _get_ctx_value("ringSerialNumber"),
            "ring_firmware_version": _get_ctx_value("ringFirmwareVersion"),
            "latest_firmware_available": _get_ctx_value("latestFirmwareAvailableForUser"),
            "device_model": _get_ctx_value("deviceModel"),
            "device_os": _get_ctx_value("deviceOs"),
            "app_version": _get_ctx_value("appVersion"),
            "latest_app_version": _get_ctx_value("latestAvailableAppVersion"),
            "policy_status": _get_ctx_value("policyStatus"),
            "warranty_expiry_date": _get_ctx_value("warrantyExpiryDate"),
            "replacement_eligible": _get_ctx_value("replacementEligible"),
            "avg_wear_time": _get_ctx_value("avgWearTime"),
        }
    return {"status": "error", "message": "No context data available"}


def _parse_bdr_value(bdr_str: str | None) -> tuple[str, float | None]:
    """Parse BDR string to determine status.

    Returns: (status, numeric_value)
    - status: "normal" (≤1.4), "high" (>1.4), "calibrating", "not_available"
    """
    if not bdr_str or bdr_str.lower() in ["no data", "n/a", "none", "", "null"]:
        return "not_available", None

    if "calibrating" in bdr_str.lower():
        return "calibrating", None

    try:
        numeric = float(bdr_str.replace("days", "").replace("%", "").strip())
        if numeric <= 1.4:
            return "normal", numeric
        else:
            return "high", numeric
    except ValueError:
        return "not_available", None


def _is_version_outdated(current: str | None, latest: str | None) -> bool:
    """Check if current version is outdated compared to latest."""
    if not current or not latest:
        return False
    if latest.lower() in ["n/a", "none", ""]:
        return False  # No update available
    current_clean = current.lower().replace("ios", "").replace("android", "").strip()
    latest_clean = latest.lower().replace("ios", "").replace("android", "").strip()
    return current_clean != latest_clean


def _parse_reset_date(date_str: str | None) -> datetime | None:
    """Parse reset date string to datetime."""
    if not date_str or date_str.lower() in ["n/a", "none", "never", ""]:
        return None
    try:
        # Try common formats
        for fmt in ["%B %d, %Y %I:%M %p", "%B %d, %Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
    except Exception:
        return None


def _is_within_24_hours(date_str: str | None) -> bool:
    """Check if a date is within the last 24 hours."""
    parsed = _parse_reset_date(date_str)
    if not parsed:
        return False
    return datetime.now() - parsed < timedelta(hours=24)


async def ultrahuman_battery_troubleshoot() -> dict[str, Any]:
    """
    Run the battery troubleshooting flow following the exact decision tree.

    Flow:
    1. Check app version → recommend update if outdated
    2. Check BDR status:
       - ≤1.4: Battery normal, show tips
       - >1.4: Continue troubleshooting
       - Calibrating/Not available: Fallback logic
    3. Check firmware → recommend update if outdated
    4. Check CDT usage (Workout/Breathwork)
    5. Check Chill Mode → recommend enabling if inactive
    6. Check soft reset → recommend if not done
    7. Check factory reset → recommend if soft done but not factory
    8. If all done and issue persists → recommend replacement
    """
    logger.info("Starting battery troubleshooting flow")

    if not has_context():
        return {
            "status": "no_context",
            "message": "I have your ring data loaded. Let me analyze your battery status.",
            "recommendation": "Context data not found - please ensure payload is loaded in dashboard.",
        }

    # Get all context data
    ctx = get_user_context()
    logger.info(f"Battery troubleshoot context keys: {list(ctx.keys())[:10]}...")

    # Extract values (try both with and without Str suffix)
    app_version = _get_ctx_value("appVersion")
    latest_app = _get_ctx_value("latestAvailableAppVersion")
    firmware_version = _get_ctx_value("ringFirmwareVersion")
    latest_firmware = _get_ctx_value("latestFirmwareAvailableForUser")
    bdr_value = _get_ctx_value("bdrValue")
    battery_health = _get_ctx_value("batteryHealthScore")
    current_battery = _get_ctx_value("currentBatteryLevel")
    soft_reset_date = _get_ctx_value("softReset")
    factory_reset_date = _get_ctx_value("factoryReset")
    chill_mode_active = _get_ctx_value("chill_mode_active")
    cdt_events = _get_ctx_value("cdt_events_count_last_3_days")
    avg_wear_time = _get_ctx_value("avgWearTime")
    replacement_eligible = _get_ctx_value("replacementEligible")
    policy_status = _get_ctx_value("policyStatus")

    # Parse reset status
    soft_reset_done = soft_reset_date and soft_reset_date.lower() not in ["n/a", "none", "never", ""]
    factory_reset_done = factory_reset_date and factory_reset_date.lower() not in ["n/a", "none", "never", ""]

    # Build response
    result = {
        "status": "success",
        "current_status": {
            "battery_health": battery_health or "Unknown",
            "current_level": current_battery or "N/A",
            "avg_wear_time": avg_wear_time or "N/A",
            "app_version": app_version or "Unknown",
            "firmware_version": firmware_version or "Unknown",
        },
        "checks": [],
        "issues": [],
        "recommendation": None,
        "next_action": None,
        "message": "",
    }

    # STEP 1: Check App Version
    app_outdated = _is_version_outdated(app_version, latest_app)
    result["checks"].append({
        "step": "App Version",
        "current": app_version,
        "latest": latest_app,
        "status": "outdated" if app_outdated else "up_to_date"
    })

    if app_outdated:
        result["issues"].append("App version is outdated")
        result["recommendation"] = "update_app"
        result["next_action"] = {
            "type": "update_app",
            "cta": "Get the latest app"
        }
        result["message"] = f"Checking your app version.. You're on {app_version}. We recommend updating to the latest app ({latest_app}), which includes improvements for battery performance."
        return result

    result["message"] = f"You're on the latest app ({app_version}). "

    # STEP 2: Check BDR Status
    bdr_status, bdr_numeric = _parse_bdr_value(bdr_value)
    result["checks"].append({
        "step": "BDR Status",
        "value": bdr_value,
        "status": bdr_status,
        "numeric": bdr_numeric
    })

    if bdr_status == "normal":
        # Battery is within expected range - provide tips and exit
        result["message"] += f"Your battery usage is within the expected range. "
        if bdr_numeric:
            result["message"] += f"At your current usage rate, battery life is approximately {bdr_numeric} days. "
        result["message"] += "Your ring's battery life can be affected by several factors: how often you use active modes like Workout and Breath Work, your daily wear patterns, ring size, environmental temperature, location settings, charging habits, and firmware version."
        result["recommendation"] = "battery_normal"
        result["next_action"] = {
            "type": "exit",
            "cta": "Exit troubleshooting"
        }
        return result

    if bdr_status == "high":
        result["issues"].append(f"High battery drain rate (BDR: {bdr_value})")
        result["message"] += f"Your current battery drain is higher than expected (BDR: {bdr_value}). "
    elif bdr_status in ["calibrating", "not_available"]:
        result["message"] += f"BDR data is {bdr_status}. Continuing with other checks. "

    # STEP 3: Check Firmware Version
    firmware_outdated = _is_version_outdated(firmware_version, latest_firmware)
    result["checks"].append({
        "step": "Firmware Version",
        "current": firmware_version,
        "latest": latest_firmware,
        "status": "outdated" if firmware_outdated else "up_to_date"
    })

    if firmware_outdated:
        result["issues"].append("Firmware version is outdated")
        result["recommendation"] = "update_firmware"
        result["next_action"] = {
            "type": "update_firmware",
            "cta": "Update firmware"
        }
        result["message"] += f"We recommend updating to the latest firmware ({latest_firmware}), which includes improvements to battery performance. After updating, please charge your ring to 100%."
        return result

    result["message"] += f"Your ring is running the latest firmware ({firmware_version}). "

    # STEP 4: Check CDT Usage
    cdt_count = 0
    if cdt_events:
        try:
            cdt_count = int(cdt_events)
        except ValueError:
            pass

    result["checks"].append({
        "step": "CDT Usage",
        "events_last_3_days": cdt_count,
        "status": "high" if cdt_count >= 5 else "normal"
    })

    if cdt_count >= 5:
        result["message"] += f"Active modes like Workout and Breath Work are using more battery power than usual ({cdt_count} events in last 3 days). "

    # STEP 5: Check Chill Mode
    is_chill_active = chill_mode_active in [True, "true", "True", "active", "yes"]
    result["checks"].append({
        "step": "Chill Mode",
        "status": "active" if is_chill_active else "inactive"
    })

    if not is_chill_active and bdr_status == "high":
        result["recommendation"] = "enable_chill_mode"
        result["next_action"] = {
            "type": "enable_chill_mode",
            "cta": "Enable Chill Mode"
        }
        result["message"] += "We recommend switching to Chill Mode in which active daytime heart rate tracking is intelligently reduced to extend battery life by up to 35%. Daytime heart rate signals tend to be noisier due to movement and variability, so Chill Mode prioritizes clean, low-power sampling during extended rest periods, preserving accuracy without impacting efficiency."
        return result

    # STEP 6: Check Soft Reset
    result["checks"].append({
        "step": "Soft Reset",
        "done": soft_reset_done,
        "date": soft_reset_date if soft_reset_done else None
    })

    if not soft_reset_done:
        result["recommendation"] = "soft_reset"
        result["next_action"] = {
            "type": "soft_reset",
            "cta": "Initiate soft reset"
        }
        result["message"] += "Let's try a soft reset to refresh your ring's software. This can help improve performance by reinitializing sensors and updating readings."
        return result

    # Check if soft reset was recent (within 24 hours)
    if _is_within_24_hours(soft_reset_date):
        result["message"] += f"Soft reset was completed recently ({soft_reset_date}). Let's monitor your battery performance for at least 24 hours and evaluate any changes."
        result["recommendation"] = "monitor"
        result["next_action"] = {
            "type": "exit",
            "cta": "Exit troubleshooting"
        }
        return result

    result["message"] += f"Soft reset completed on {soft_reset_date}. "

    # STEP 7: Check Factory Reset
    result["checks"].append({
        "step": "Factory Reset",
        "done": factory_reset_done,
        "date": factory_reset_date if factory_reset_done else None
    })

    if not factory_reset_done:
        result["recommendation"] = "factory_reset"
        result["next_action"] = {
            "type": "factory_reset",
            "cta": "Initiate factory reset"
        }
        result["message"] += "Let's try a factory reset to refresh your ring's systems. You'll need your ring charger for this process, which typically takes about 10 minutes. This reset can help resolve battery performance by restarting all sensors and recalibrating power management."
        return result

    # Check if factory reset was recent (within 24 hours)
    if _is_within_24_hours(factory_reset_date):
        result["message"] += f"Factory reset was completed recently ({factory_reset_date}). Let's monitor your battery performance for at least 24 hours and evaluate any changes."
        result["recommendation"] = "monitor"
        result["next_action"] = {
            "type": "exit",
            "cta": "Exit troubleshooting"
        }
        return result

    # STEP 8: All troubleshooting exhausted - Recommend Replacement
    is_eligible = replacement_eligible in [True, "true", "True", "yes", "Yes"]
    within_policy = policy_status and "within" in policy_status.lower()

    if is_eligible or within_policy:
        result["recommendation"] = "replacement"
        result["next_action"] = {
            "type": "replacement",
            "cta": "Request replacement"
        }
        result["message"] = "Since the battery issue persists after trying the resets, we recommend requesting a replacement ring to ensure you can continue tracking your health without interruption. We may need to collect your current ring for further investigation. Thank you for your patience as we work to make this right for you."
    else:
        result["recommendation"] = "wabi_sabi_replacement"
        result["next_action"] = {
            "type": "wabi_sabi_replacement",
            "cta": "Proceed with instant replacement"
        }
        result["message"] = "Since the battery issue persists after trying the resets, we recommend requesting a replacement ring to ensure you can continue tracking your health without interruption. We can offer you an Ultrahuman Certified Renewed Ring—identical in performance to new, with subtle aesthetic variations."

    return result


# Map tool names to functions
BATTERY_TOOL_FUNCTIONS = {
    "ultrahuman_check_charger_status": ultrahuman_check_charger_status,
    "ultrahuman_check_troubleshooting_history": ultrahuman_check_troubleshooting_history,
    "ultrahuman_confirm_wear_status": ultrahuman_confirm_wear_status,
    "ultrahuman_get_reset_status": ultrahuman_get_reset_status,
    "ultrahuman_trigger_soft_reset": ultrahuman_trigger_soft_reset,
    "ultrahuman_get_ring_battery_info": ultrahuman_get_ring_battery_info,
    "ultrahuman_get_device_info": ultrahuman_get_device_info,
    "ultrahuman_battery_troubleshoot": ultrahuman_battery_troubleshoot,
}
