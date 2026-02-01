"""Health metrics tools for Ultrahuman Ring - sleep, HR, HRV, steps, glucose."""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from .client import get_ultrahuman_client, DEFAULT_USER_EMAIL
from server.logging_config import logger


# Tool schemas for LLM
HEALTH_METRICS_TOOL_SCHEMAS = [
    {
        "name": "ultrahuman_get_health_metrics",
        "description": "Get all health metrics for the user on a specific date. Includes sleep, heart rate, HRV, steps, temperature, recovery score, and glucose data if available.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format (e.g., '2024-01-15'). Defaults to today.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "ultrahuman_get_sleep_data",
        "description": "Get detailed sleep data including sleep score, stages (deep, light, REM, awake), efficiency, total sleep time, and sleep insights.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format. Defaults to today.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "ultrahuman_get_heart_rate_data",
        "description": "Get heart rate data including current HR, resting HR, and HR values throughout the day.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format. Defaults to today.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "ultrahuman_get_hrv_data",
        "description": "Get Heart Rate Variability (HRV) data including average HRV, trend, and values throughout the day.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format. Defaults to today.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "ultrahuman_get_activity_data",
        "description": "Get activity data including steps, movement, and motion data for the day.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format. Defaults to today.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "ultrahuman_get_recovery_score",
        "description": "Get recovery score and recovery index for the user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format. Defaults to today.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "ultrahuman_get_glucose_data",
        "description": "Get glucose/metabolic data including glucose values, metabolic score, glucose variability, HbA1c, and time in target. Only available for users with CGM sensors.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format. Defaults to today.",
                },
            },
            "required": [],
        },
    },
]


async def _fetch_metrics(email: Optional[str] = None, date_str: Optional[str] = None) -> dict[str, Any]:
    """Fetch all metrics from the Partner API."""
    try:
        client = get_ultrahuman_client()
        target_date = date_str or date.today().isoformat()
        user_email = email or DEFAULT_USER_EMAIL

        response = await client.get(
            "/api/v1/metrics",
            params={"email": user_email, "date": target_date},
        )

        if response.get("status") == "error":
            return {"error": response.get("error", "Unknown error")}

        return response
    except Exception as e:
        logger.exception("Error fetching metrics")
        return {"error": str(e)}


def _extract_metric_by_type(metrics: list[dict], metric_type: str) -> Optional[dict]:
    """Extract a specific metric type from the metrics list."""
    for metric in metrics:
        if metric.get("type") == metric_type:
            return metric.get("object")
    return None


async def ultrahuman_get_health_metrics(email: Optional[str] = None, date: Optional[str] = None) -> dict[str, Any]:
    """
    Get all health metrics for a user on a specific date.

    Args:
        email: User's email address (defaults to hardcoded email)
        date: Date in YYYY-MM-DD format (defaults to today)

    Returns:
        dict with summary of all available metrics
    """
    response = await _fetch_metrics(email or DEFAULT_USER_EMAIL, date)
    if "error" in response:
        return response

    metrics = response.get("data", {}).get("metric_data", [])

    result = {
        "status": "success",
        "date": date or date.today().isoformat() if hasattr(date, 'today') else date,
        "email": email,
        "metrics_available": [],
    }

    # Extract key metrics
    sleep = _extract_metric_by_type(metrics, "sleep") or _extract_metric_by_type(metrics, "Sleep")
    if sleep:
        result["metrics_available"].append("sleep")
        result["sleep_score"] = sleep.get("score")
        details = sleep.get("details", {})
        quick = {m["type"]: m["value"] for m in details.get("quick_metrics", [])}
        result["total_sleep"] = quick.get("total_sleep")
        result["sleep_efficiency"] = quick.get("sleep_efic")

    hr = _extract_metric_by_type(metrics, "hr")
    if hr:
        result["metrics_available"].append("heart_rate")
        result["last_hr"] = hr.get("last_reading")

    hrv = _extract_metric_by_type(metrics, "hrv")
    if hrv:
        result["metrics_available"].append("hrv")
        result["avg_hrv"] = hrv.get("avg")
        result["hrv_trend"] = hrv.get("trend_direction")

    steps = _extract_metric_by_type(metrics, "steps")
    if steps:
        result["metrics_available"].append("steps")
        values = steps.get("values", [])
        result["total_steps"] = sum(v.get("value", 0) for v in values)

    recovery = _extract_metric_by_type(metrics, "recovery")
    if recovery:
        result["metrics_available"].append("recovery")
        result["recovery_score"] = recovery.get("score")

    glucose = _extract_metric_by_type(metrics, "glucose")
    if glucose:
        result["metrics_available"].append("glucose")

    metabolic = _extract_metric_by_type(metrics, "metabolic_score")
    if metabolic:
        result["metabolic_score"] = metabolic.get("value")

    return result


async def ultrahuman_get_sleep_data(email: Optional[str] = None, date: Optional[str] = None) -> dict[str, Any]:
    """
    Get detailed sleep data.

    Args:
        email: User's email address (defaults to hardcoded email)
        date: Date in YYYY-MM-DD format

    Returns:
        dict with detailed sleep information
    """
    response = await _fetch_metrics(email or DEFAULT_USER_EMAIL, date)
    if "error" in response:
        return response

    metrics = response.get("data", {}).get("metric_data", [])
    sleep = _extract_metric_by_type(metrics, "sleep") or _extract_metric_by_type(metrics, "Sleep")

    if not sleep:
        return {"status": "success", "message": "No sleep data available for this date"}

    details = sleep.get("details", {})
    quick_metrics = {m["type"]: m for m in details.get("quick_metrics", [])}
    sleep_stages = {s["type"]: s["percentage"] for s in details.get("sleep_stages", [])}
    summary = {s["title"]: {"score": s["score"], "state": s["state"]} for s in details.get("summary", [])}

    return {
        "status": "success",
        "sleep_score": sleep.get("score"),
        "bedtime_start": details.get("bedtime_start"),
        "bedtime_end": details.get("bedtime_end"),
        "total_sleep": quick_metrics.get("total_sleep", {}).get("display_text"),
        "total_sleep_seconds": quick_metrics.get("total_sleep", {}).get("value"),
        "sleep_efficiency": quick_metrics.get("sleep_efic", {}).get("display_text"),
        "avg_heart_rate": quick_metrics.get("avg_hr", {}).get("value"),
        "avg_hrv": quick_metrics.get("avg_hrv", {}).get("value"),
        "sleep_stages": {
            "deep_sleep_pct": sleep_stages.get("deep_sleep"),
            "light_sleep_pct": sleep_stages.get("light_sleep"),
            "rem_sleep_pct": sleep_stages.get("rem_sleep"),
            "awake_pct": sleep_stages.get("awake"),
        },
        "summary": summary,
        "insights": [i.get("title") for i in details.get("insights", [])],
    }


async def ultrahuman_get_heart_rate_data(email: Optional[str] = None, date: Optional[str] = None) -> dict[str, Any]:
    """
    Get heart rate data.

    Args:
        email: User's email address (defaults to hardcoded email)
        date: Date in YYYY-MM-DD format

    Returns:
        dict with heart rate information
    """
    response = await _fetch_metrics(email or DEFAULT_USER_EMAIL, date)
    if "error" in response:
        return response

    metrics = response.get("data", {}).get("metric_data", [])
    hr = _extract_metric_by_type(metrics, "hr")
    rhr = _extract_metric_by_type(metrics, "night_rhr")

    if not hr:
        return {"status": "success", "message": "No heart rate data available for this date"}

    values = hr.get("values", [])
    hr_values = [v["value"] for v in values if v.get("value") is not None]

    return {
        "status": "success",
        "last_reading": hr.get("last_reading"),
        "unit": hr.get("unit", "BPM"),
        "min_hr": min(hr_values) if hr_values else None,
        "max_hr": max(hr_values) if hr_values else None,
        "avg_hr": round(sum(hr_values) / len(hr_values), 1) if hr_values else None,
        "reading_count": len(hr_values),
        "resting_hr": rhr.get("avg") if rhr else None,
    }


async def ultrahuman_get_hrv_data(email: Optional[str] = None, date: Optional[str] = None) -> dict[str, Any]:
    """
    Get HRV data.

    Args:
        email: User's email address (defaults to hardcoded email)
        date: Date in YYYY-MM-DD format

    Returns:
        dict with HRV information
    """
    response = await _fetch_metrics(email or DEFAULT_USER_EMAIL, date)
    if "error" in response:
        return response

    metrics = response.get("data", {}).get("metric_data", [])
    hrv = _extract_metric_by_type(metrics, "hrv")

    if not hrv:
        return {"status": "success", "message": "No HRV data available for this date"}

    values = hrv.get("values", [])
    hrv_values = [v["value"] for v in values if v.get("value") is not None]

    return {
        "status": "success",
        "avg_hrv": hrv.get("avg"),
        "trend_title": hrv.get("trend_title"),
        "trend_direction": hrv.get("trend_direction"),
        "min_hrv": min(hrv_values) if hrv_values else None,
        "max_hrv": max(hrv_values) if hrv_values else None,
        "reading_count": len(hrv_values),
    }


async def ultrahuman_get_activity_data(email: Optional[str] = None, date: Optional[str] = None) -> dict[str, Any]:
    """
    Get activity data (steps, movement).

    Args:
        email: User's email address (defaults to hardcoded email)
        date: Date in YYYY-MM-DD format

    Returns:
        dict with activity information
    """
    response = await _fetch_metrics(email or DEFAULT_USER_EMAIL, date)
    if "error" in response:
        return response

    metrics = response.get("data", {}).get("metric_data", [])
    steps = _extract_metric_by_type(metrics, "steps")
    motion = _extract_metric_by_type(metrics, "motion")
    movement_index = _extract_metric_by_type(metrics, "movement_index")

    result = {"status": "success"}

    if steps:
        values = steps.get("values", [])
        step_values = [v["value"] for v in values if v.get("value") is not None]
        result["total_steps"] = int(sum(step_values)) if step_values else 0
        result["avg_steps_per_interval"] = steps.get("avg")
        result["steps_trend_title"] = steps.get("trend_title")
        result["steps_trend_direction"] = steps.get("trend_direction")

    if motion:
        result["avg_motion"] = motion.get("avg")
        result["motion_trend_title"] = motion.get("trend_title")
        result["motion_trend_direction"] = motion.get("trend_direction")

    if movement_index:
        result["movement_index"] = movement_index.get("value")

    if not steps and not motion:
        result["message"] = "No activity data available for this date"

    return result


async def ultrahuman_get_recovery_score(email: Optional[str] = None, date: Optional[str] = None) -> dict[str, Any]:
    """
    Get recovery score.

    Args:
        email: User's email address (defaults to hardcoded email)
        date: Date in YYYY-MM-DD format

    Returns:
        dict with recovery information
    """
    response = await _fetch_metrics(email or DEFAULT_USER_EMAIL, date)
    if "error" in response:
        return response

    metrics = response.get("data", {}).get("metric_data", [])
    recovery = _extract_metric_by_type(metrics, "recovery")
    recovery_index = _extract_metric_by_type(metrics, "recovery_index")
    vo2_max = _extract_metric_by_type(metrics, "vo2_max")

    result = {"status": "success"}

    if recovery:
        result["recovery_score"] = recovery.get("score")

    if recovery_index:
        result["recovery_index"] = recovery_index.get("value")

    if vo2_max:
        result["vo2_max"] = vo2_max.get("value")

    if not recovery and not recovery_index:
        result["message"] = "No recovery data available for this date"

    return result


async def ultrahuman_get_glucose_data(email: Optional[str] = None, date: Optional[str] = None) -> dict[str, Any]:
    """
    Get glucose/metabolic data.

    Args:
        email: User's email address (defaults to hardcoded email)
        date: Date in YYYY-MM-DD format

    Returns:
        dict with glucose and metabolic information
    """
    response = await _fetch_metrics(email or DEFAULT_USER_EMAIL, date)
    if "error" in response:
        return response

    metrics = response.get("data", {}).get("metric_data", [])

    glucose = _extract_metric_by_type(metrics, "glucose")
    metabolic = _extract_metric_by_type(metrics, "metabolic_score")
    variability = _extract_metric_by_type(metrics, "glucose_variability")
    avg_glucose = _extract_metric_by_type(metrics, "average_glucose")
    hba1c = _extract_metric_by_type(metrics, "hba1c")
    time_target = _extract_metric_by_type(metrics, "time_in_target")

    result = {"status": "success"}

    if glucose:
        values = glucose.get("values", [])
        glucose_values = [v["value"] for v in values if v.get("value") is not None]
        result["glucose_readings_count"] = len(glucose_values)
        if glucose_values:
            result["min_glucose"] = min(glucose_values)
            result["max_glucose"] = max(glucose_values)
            result["latest_glucose"] = glucose_values[-1] if glucose_values else None

    if metabolic:
        result["metabolic_score"] = metabolic.get("value")

    if variability:
        result["glucose_variability_pct"] = variability.get("value")

    if avg_glucose:
        result["average_glucose"] = avg_glucose.get("value")

    if hba1c:
        result["hba1c"] = hba1c.get("value")

    if time_target:
        result["time_in_target_pct"] = time_target.get("value")

    if not any([glucose, metabolic, variability, avg_glucose, hba1c, time_target]):
        result["message"] = "No glucose/metabolic data available. This requires a CGM sensor."

    return result


# Map tool names to functions
HEALTH_METRICS_TOOL_FUNCTIONS = {
    "ultrahuman_get_health_metrics": ultrahuman_get_health_metrics,
    "ultrahuman_get_sleep_data": ultrahuman_get_sleep_data,
    "ultrahuman_get_heart_rate_data": ultrahuman_get_heart_rate_data,
    "ultrahuman_get_hrv_data": ultrahuman_get_hrv_data,
    "ultrahuman_get_activity_data": ultrahuman_get_activity_data,
    "ultrahuman_get_recovery_score": ultrahuman_get_recovery_score,
    "ultrahuman_get_glucose_data": ultrahuman_get_glucose_data,
}
