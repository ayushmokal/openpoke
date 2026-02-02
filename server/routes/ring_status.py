"""Ring status API endpoint for live battery and device stats."""

import time
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from httpx import HTTPStatusError

from ..agents.execution_agent.tools.ultrahuman import get_ultrahuman_client
from ..logging_config import logger

router = APIRouter(prefix="/ring", tags=["ring"])

# Circuit breaker state to avoid spamming logs
_last_auth_error_time: float = 0
_auth_error_logged: bool = False


@router.get("/status", response_class=JSONResponse)
async def get_ring_status() -> JSONResponse:
    """Get live ring status including battery, device info, and reset status."""
    try:
        client = get_ultrahuman_client()

        # Fetch ring battery info (contains most of the data we need)
        response = await client.get("/api/v4/yellow/ring_battery_info")

        if response.get("status") == "error":
            return JSONResponse(
                status_code=500,
                content={"error": response.get("error", {}).get("message", "Unknown error")}
            )

        data = response.get("data", {})

        # Extract the specific fields requested
        status = {
            "connected": True,
            "lastUpdated": data.get("lastRingStatesTimestampStr", "Unknown"),

            # Battery Info
            "batteryTsSessions": data.get("batteryTsSessionsStr", "Not available"),
            "batteryHealthScore": data.get("batteryHealthScoreStr", "Unknown"),
            "currentBatteryLevel": data.get("currentBatteryLevelStr", "Unknown"),
            "batteryLifeAtCurrentBdr": data.get("battery_life_at_current_bdr", "Unknown"),

            # Reset Info
            "softReset": data.get("softResetStr", "Never"),
            "factoryReset": data.get("factoryResetStr", "Never"),

            # Ring Info
            "ringSerialNumber": data.get("ringSerialNumberStr", "Unknown"),
            "ringDescription": data.get("ringDescriptionStr", "Ultrahuman Ring"),
            "ringFirmwareVersion": data.get("ringFirmwareVersionStr", "Unknown"),
            "latestFirmwareAvailable": data.get("latestFirmwareAvailableForUserStr", "Unknown"),

            # Connection Info
            "ringConnectedLast24hrs": data.get("ringConnectedLast24HrsStr", "Unknown"),
            "daysSinceActivation": data.get("noOfDaysSinceRingActivationStr", "Unknown"),

            # Device Info
            "deviceModel": data.get("deviceModelStr", "Unknown"),
            "deviceOs": data.get("deviceOsStr", "Unknown"),
            "appVersion": data.get("appVersionStr", "Unknown"),
            "latestAppVersion": data.get("latestAvailableAppVersionStr", "Unknown"),

            # BDR Info
            "bdrTriggered": data.get("bdrTriggeredStr", "No"),
            "bdrCompleted": data.get("bdrCompletedStr", "No"),
            "bdrValue": data.get("bdrValueStr", "N/A"),
            "daysSinceBdr": data.get("daysSinceBdrStr", "N/A"),
            "bdrTimeLeft": data.get("bdrTimeLeftStr", "N/A"),

            # Warranty & Policy
            "policyStatus": data.get("policyStatusStr", "Unknown"),
            "warrantyExpiryDate": data.get("warrantyExpiryDateStr", "Unknown"),
            "daysUntilWarrantyExpiry": data.get("daysUntilWarrantyExpiryStr", "Unknown"),
            "replacementEligible": data.get("replacementEligibleStr", "Unknown"),
            "replacementCount": data.get("replacementCountStr", "0"),
            "maxReplacements": data.get("maxReplacementsStr", "Unknown"),

            # Other
            "chillModeActive": data.get("chill_mode_active", False),
            "dataSharingEnabled": data.get("dataSharingStr", "Unknown"),
            "faultyHr": data.get("faultyHrStr", "No"),
        }

        return JSONResponse(content={"ok": True, "data": status})

    except HTTPStatusError as e:
        global _last_auth_error_time, _auth_error_logged

        if e.response.status_code == 401:
            # Only log auth errors once per minute to avoid spam
            now = time.time()
            if not _auth_error_logged or (now - _last_auth_error_time) > 60:
                logger.warning("Ring status: 401 Unauthorized - check ULTRAHUMAN_PARTNER_API_KEY")
                _last_auth_error_time = now
                _auth_error_logged = True
            return JSONResponse(
                status_code=401,
                content={"ok": False, "error": "Unauthorized - API key may be invalid or expired"}
            )

        logger.error(f"Ring status HTTP error: {e.response.status_code}")
        return JSONResponse(
            status_code=e.response.status_code,
            content={"ok": False, "error": str(e)}
        )
    except Exception as e:
        logger.exception("Error fetching ring status")
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


__all__ = ["router"]
