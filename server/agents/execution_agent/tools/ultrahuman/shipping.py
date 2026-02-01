"""Shipping and order-related tools for Ultrahuman Ring replacements and orders."""

from __future__ import annotations

from typing import Any, Optional

from .client import get_ultrahuman_client
from server.logging_config import logger


# Tool schemas for LLM
SHIPPING_TOOL_SCHEMAS = [
    {
        "name": "ultrahuman_create_replacement_request",
        "description": "Create a replacement request for the user's Ultrahuman ring. Use this when the user needs a ring replacement due to battery issues, heating, or other defects.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Replacement category. Options: 'battery_dissipation', 'battery_issue_ring_heating', 'physical_damage', 'sensor_malfunction', 'connectivity_issues', 'other'",
                    "enum": [
                        "battery_dissipation",
                        "battery_issue_ring_heating",
                        "physical_damage",
                        "sensor_malfunction",
                        "connectivity_issues",
                        "other",
                    ],
                },
                "state": {
                    "type": "string",
                    "description": "Acceptance state. Defaults to 'auto_accepted'. Use 'auto_accepted_wabi_sabi' for Wabi Sabi replacements.",
                    "enum": ["auto_accepted", "auto_accepted_wabi_sabi"],
                    "default": "auto_accepted",
                },
            },
            "required": ["category"],
        },
    },
    {
        "name": "ultrahuman_update_shipping_address",
        "description": "Update the shipping address on the user's latest ring order. Use this when the user needs to change their delivery address.",
        "input_schema": {
            "type": "object",
            "properties": {
                "address1": {
                    "type": "string",
                    "description": "Street address line 1",
                },
                "address2": {
                    "type": "string",
                    "description": "Street address line 2 (optional)",
                },
                "city": {
                    "type": "string",
                    "description": "City",
                },
                "province": {
                    "type": "string",
                    "description": "State/Province name",
                },
                "province_code": {
                    "type": "string",
                    "description": "State/Province code (e.g., 'CA', 'NY')",
                },
                "zip": {
                    "type": "string",
                    "description": "Postal/ZIP code",
                },
                "country": {
                    "type": "string",
                    "description": "Country name",
                },
                "country_code": {
                    "type": "string",
                    "description": "Country code (e.g., 'US', 'IN')",
                },
                "phone": {
                    "type": "string",
                    "description": "Phone number",
                },
                "first_name": {
                    "type": "string",
                    "description": "First name",
                },
                "last_name": {
                    "type": "string",
                    "description": "Last name",
                },
            },
            "required": ["address1", "city", "country", "zip"],
        },
    },
    {
        "name": "ultrahuman_enable_data_sharing",
        "description": "Enable data sharing consent for the user. This allows coaches and support to access user data for troubleshooting.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "ultrahuman_get_order_status",
        "description": "Get the status of the user's latest order including order ID, status, tracking URL, and shipping address.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "ultrahuman_get_warranty_info",
        "description": "Get warranty and replacement policy information for the user's ring.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


async def ultrahuman_create_replacement_request(
    category: str,
    state: str = "auto_accepted",
) -> dict[str, Any]:
    """
    Create a replacement request for the user's ring.

    Args:
        category: Replacement category (battery_dissipation, battery_issue_ring_heating, etc.)
        state: Acceptance state (auto_accepted or auto_accepted_wabi_sabi)

    Returns:
        dict with replacement request ID or error
    """
    try:
        client = get_ultrahuman_client()
        response = await client.post(
            "/api/v4/yellow/create_replacement_request",
            data={"category": category, "state": state},
        )

        if response.get("status") == "error":
            error = response.get("error", {})
            return {
                "error": error.get("message", "Unknown error"),
                "code": error.get("code"),
            }

        data = response.get("data", {})
        return {
            "status": "success",
            "replacement_request_id": data.get("replacement_request_id"),
            "message": f"Replacement request created successfully with ID: {data.get('replacement_request_id')}",
        }
    except Exception as e:
        logger.exception("Error creating replacement request")
        return {"error": str(e)}


async def ultrahuman_update_shipping_address(
    address1: str,
    city: str,
    country: str,
    zip: str,
    address2: Optional[str] = None,
    province: Optional[str] = None,
    province_code: Optional[str] = None,
    country_code: Optional[str] = None,
    phone: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Update shipping address on the user's latest order.

    Args:
        address1: Street address line 1
        city: City
        country: Country name
        zip: Postal code
        address2: Street address line 2 (optional)
        province: State/Province name (optional)
        province_code: State/Province code (optional)
        country_code: Country code (optional)
        phone: Phone number (optional)
        first_name: First name (optional)
        last_name: Last name (optional)

    Returns:
        dict with updated order ID and address or error
    """
    try:
        shipping_address = {
            "address1": address1,
            "city": city,
            "country": country,
            "zip": zip,
        }

        # Add optional fields if provided
        if address2:
            shipping_address["address2"] = address2
        if province:
            shipping_address["province"] = province
        if province_code:
            shipping_address["province_code"] = province_code
        if country_code:
            shipping_address["country_code"] = country_code
        if phone:
            shipping_address["phone"] = phone
        if first_name:
            shipping_address["first_name"] = first_name
        if last_name:
            shipping_address["last_name"] = last_name

        client = get_ultrahuman_client()
        response = await client.post(
            "/api/v4/yellow/update_shipping_address",
            data={"shipping_address": shipping_address},
        )

        if response.get("status") == "error":
            error = response.get("error", {})
            return {
                "error": error.get("message", "Unknown error"),
                "code": error.get("code"),
            }

        data = response.get("data", {})
        return {
            "status": "success",
            "order_id": data.get("order_id"),
            "shipping_address": data.get("shipping_address"),
            "message": f"Shipping address updated successfully for order {data.get('order_id')}",
        }
    except Exception as e:
        logger.exception("Error updating shipping address")
        return {"error": str(e)}


async def ultrahuman_enable_data_sharing() -> dict[str, Any]:
    """
    Enable data sharing consent for the user.

    Returns:
        dict with success message or error
    """
    try:
        client = get_ultrahuman_client()
        response = await client.post("/api/v4/yellow/user_data_sharing_consent")

        if response.get("status") == "error":
            return {"error": response.get("error", {}).get("message", "Unknown error")}

        return {
            "status": "success",
            "message": response.get("data", {}).get("message", "Data sharing consent updated"),
        }
    except Exception as e:
        logger.exception("Error enabling data sharing")
        return {"error": str(e)}


async def ultrahuman_get_order_status() -> dict[str, Any]:
    """
    Get the status of the user's latest order.

    Returns:
        dict with order information
    """
    try:
        client = get_ultrahuman_client()
        response = await client.get("/api/v4/yellow/ring_battery_info")

        if response.get("status") == "error":
            return {"error": response.get("error", {}).get("message", "Unknown error")}

        data = response.get("data", {})

        order_id = data.get("latestOrderIdStr")
        if not order_id:
            return {
                "status": "success",
                "message": "No orders found for this user",
            }

        return {
            "status": "success",
            "order_id": order_id,
            "order_status": data.get("latestOrderStatusStr"),
            "order_date": data.get("orderDateStr"),
            "order_source": data.get("orderSourceStr"),
            "tracking_url": data.get("trackingUrlStr"),
            "shipping_address": data.get("shippingAddressStr"),
            "shipping_country": data.get("shippingCountryStr"),
        }
    except Exception as e:
        logger.exception("Error getting order status")
        return {"error": str(e)}


async def ultrahuman_get_warranty_info() -> dict[str, Any]:
    """
    Get warranty and replacement policy information.

    Returns:
        dict with warranty information
    """
    try:
        client = get_ultrahuman_client()
        response = await client.get("/api/v4/yellow/ring_battery_info")

        if response.get("status") == "error":
            return {"error": response.get("error", {}).get("message", "Unknown error")}

        data = response.get("data", {})
        return {
            "status": "success",
            "policy_status": data.get("policyStatusStr"),
            "warranty_expiry_date": data.get("warrantyExpiryDateStr"),
            "days_until_warranty_expiry": data.get("daysUntilWarrantyExpiryStr"),
            "replacement_eligible": data.get("replacementEligibleStr"),
            "replacement_count": data.get("replacementCountStr"),
            "max_replacements": data.get("maxReplacementsStr"),
            "wabi_sabi_replacement_count": data.get("wabiSabiReplacementCountStr"),
        }
    except Exception as e:
        logger.exception("Error getting warranty info")
        return {"error": str(e)}


# Map tool names to functions
SHIPPING_TOOL_FUNCTIONS = {
    "ultrahuman_create_replacement_request": ultrahuman_create_replacement_request,
    "ultrahuman_update_shipping_address": ultrahuman_update_shipping_address,
    "ultrahuman_enable_data_sharing": ultrahuman_enable_data_sharing,
    "ultrahuman_get_order_status": ultrahuman_get_order_status,
    "ultrahuman_get_warranty_info": ultrahuman_get_warranty_info,
}
