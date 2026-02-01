"""Ultrahuman API client for Partner and Yellow APIs."""

from __future__ import annotations

import os
from typing import Any, Optional

import httpx

from server.logging_config import logger

# Hardcoded user email for testing
DEFAULT_USER_EMAIL = "ayush.mokal@ultrahuman.com"


class UltrahumanAPIClient:
    """Client for interacting with Ultrahuman APIs."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("ULTRAHUMAN_PARTNER_API_KEY")
        self.base_url = (base_url or os.getenv("ULTRAHUMAN_PARTNER_API_URL", "https://partner.ultrahuman.com")).rstrip("/")

        if not self.api_key:
            raise ValueError("ULTRAHUMAN_PARTNER_API_KEY is required")

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authorization."""
        # Ultrahuman Partner API uses the JWT token directly in Authorization header
        return {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def get(self, endpoint: str, params: Optional[dict[str, Any]] = None, email: Optional[str] = None) -> dict[str, Any]:
        """Make a GET request to the API."""
        url = f"{self.base_url}{endpoint}"

        # Add email to params for Yellow API endpoints
        if params is None:
            params = {}
        if email or "yellow" in endpoint:
            params["email"] = email or DEFAULT_USER_EMAIL

        logger.debug(f"Ultrahuman API GET: {url}", extra={"params": params})

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            return response.json()

    async def post(self, endpoint: str, data: Optional[dict[str, Any]] = None, email: Optional[str] = None) -> dict[str, Any]:
        """Make a POST request to the API."""
        url = f"{self.base_url}{endpoint}"

        # Add email to data for Yellow API endpoints
        if data is None:
            data = {}
        if email or "yellow" in endpoint:
            data["email"] = email or DEFAULT_USER_EMAIL

        logger.debug(f"Ultrahuman API POST: {url}", extra={"data": data})

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=self._get_headers(), json=data)
            response.raise_for_status()
            return response.json()


# Singleton instance
_client: Optional[UltrahumanAPIClient] = None


def get_ultrahuman_client() -> UltrahumanAPIClient:
    """Get or create the Ultrahuman API client singleton."""
    global _client
    if _client is None:
        _client = UltrahumanAPIClient()
    return _client
