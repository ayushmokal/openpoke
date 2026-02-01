"""Ring status API endpoint for live battery and device stats."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..agents.execution_agent.tools.ultrahuman import get_ultrahuman_client
from ..logging_config import logger

router = APIRouter(prefix="/ring", tags=["ring"])


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

    except Exception as e:
        logger.exception("Error fetching ring status")
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


__all__ = ["router"]
