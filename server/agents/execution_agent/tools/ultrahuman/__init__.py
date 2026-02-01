"""Ultrahuman API tools for battery, health metrics, and shipping."""

from .battery import (
    BATTERY_TOOL_FUNCTIONS,
    BATTERY_TOOL_SCHEMAS,
    ultrahuman_battery_troubleshoot,
    ultrahuman_get_device_info,
    ultrahuman_get_reset_status,
    ultrahuman_get_ring_battery_info,
    ultrahuman_trigger_soft_reset,
)
from .context import (
    clear_user_context,
    get_battery_context,
    get_context_value,
    get_device_context,
    get_order_context,
    get_reset_context,
    get_user_context,
    get_user_info_context,
    get_warranty_context,
    has_context,
    set_user_context,
)
from .client import UltrahumanAPIClient, get_ultrahuman_client
from .health_metrics import (
    HEALTH_METRICS_TOOL_FUNCTIONS,
    HEALTH_METRICS_TOOL_SCHEMAS,
    ultrahuman_get_activity_data,
    ultrahuman_get_glucose_data,
    ultrahuman_get_health_metrics,
    ultrahuman_get_heart_rate_data,
    ultrahuman_get_hrv_data,
    ultrahuman_get_recovery_score,
    ultrahuman_get_sleep_data,
)
from .shipping import (
    SHIPPING_TOOL_FUNCTIONS,
    SHIPPING_TOOL_SCHEMAS,
    ultrahuman_create_replacement_request,
    ultrahuman_enable_data_sharing,
    ultrahuman_get_order_status,
    ultrahuman_get_warranty_info,
    ultrahuman_update_shipping_address,
)

# Combined tool schemas for all Ultrahuman tools
ULTRAHUMAN_TOOL_SCHEMAS = (
    BATTERY_TOOL_SCHEMAS + HEALTH_METRICS_TOOL_SCHEMAS + SHIPPING_TOOL_SCHEMAS
)

# Combined tool functions mapping
ULTRAHUMAN_TOOL_FUNCTIONS = {
    **BATTERY_TOOL_FUNCTIONS,
    **HEALTH_METRICS_TOOL_FUNCTIONS,
    **SHIPPING_TOOL_FUNCTIONS,
}

__all__ = [
    # Client
    "UltrahumanAPIClient",
    "get_ultrahuman_client",
    # Context
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
    # Combined exports
    "ULTRAHUMAN_TOOL_SCHEMAS",
    "ULTRAHUMAN_TOOL_FUNCTIONS",
    # Battery
    "BATTERY_TOOL_SCHEMAS",
    "BATTERY_TOOL_FUNCTIONS",
    "ultrahuman_get_reset_status",
    "ultrahuman_trigger_soft_reset",
    "ultrahuman_get_ring_battery_info",
    "ultrahuman_get_device_info",
    "ultrahuman_battery_troubleshoot",
    # Health Metrics
    "HEALTH_METRICS_TOOL_SCHEMAS",
    "HEALTH_METRICS_TOOL_FUNCTIONS",
    "ultrahuman_get_health_metrics",
    "ultrahuman_get_sleep_data",
    "ultrahuman_get_heart_rate_data",
    "ultrahuman_get_hrv_data",
    "ultrahuman_get_activity_data",
    "ultrahuman_get_recovery_score",
    "ultrahuman_get_glucose_data",
    # Shipping
    "SHIPPING_TOOL_SCHEMAS",
    "SHIPPING_TOOL_FUNCTIONS",
    "ultrahuman_create_replacement_request",
    "ultrahuman_update_shipping_address",
    "ultrahuman_enable_data_sharing",
    "ultrahuman_get_order_status",
    "ultrahuman_get_warranty_info",
]
