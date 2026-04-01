"""Async GHL API v2 client for read-only dashboard intel."""

import asyncio
import logging
from typing import Any

import aiohttp

logger = logging.getLogger("ghl_dashboard_client")


class GHLDashboardClient:
    """Read-only async client for GHL API v2 (Services endpoint)."""

    BASE_URL = "https://services.leadconnectorhq.com"
    API_VERSION = "2021-07-28"
    RATE_LIMIT_DELAY = 0.1  # 100ms between requests = max 10 req/s

    def __init__(self, private_token: str, location_id: str):
        """Initialize with GHL credentials.

        Args:
            private_token: GHL Private Integration Token (v2 API)
            location_id: GHL Location ID
        """
        self.private_token = private_token
        self.location_id = location_id

    def _headers(self) -> dict:
        """Build standard request headers."""
        return {
            "Authorization": f"Bearer {self.private_token}",
            "Version": self.API_VERSION,
            "Content-Type": "application/json",
        }

    async def _get(self, endpoint: str, params: dict | None = None) -> dict | list:
        """Make authenticated GET request with rate limiting.

        Returns raw dict/list on success, [] on any error.
        """
        url = f"{self.BASE_URL}{endpoint}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._headers(), params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        logger.warning(f"GHL API {endpoint} returned {resp.status}")
                        return [] if isinstance([], list) else {}
        except Exception as exc:
            logger.error(f"GHL API {endpoint} failed: {exc}")
            return [] if endpoint.endswith("s") else {}
        finally:
            await asyncio.sleep(self.RATE_LIMIT_DELAY)

    async def get_contacts(self, limit: int = 100, page: int = 1) -> list[dict]:
        """Fetch contacts for location.

        Args:
            limit: Results per page (max 100)
            page: 1-indexed page number

        Returns:
            List of contact dicts, or [] on error
        """
        endpoint = f"/contacts/"
        params = {
            "locationId": self.location_id,
            "limit": min(limit, 100),
            "offset": (page - 1) * limit,
        }
        result = await self._get(endpoint, params)
        return result.get("contacts", []) if isinstance(result, dict) else []

    async def get_pipelines(self) -> list[dict]:
        """Fetch all pipelines for location.

        Returns:
            List of pipeline dicts, or [] on error
        """
        endpoint = f"/pipelines/"
        params = {"locationId": self.location_id}
        result = await self._get(endpoint, params)
        return result.get("pipelines", []) if isinstance(result, dict) else []

    async def get_opportunities(self, pipeline_id: str, limit: int = 100, page: int = 1) -> list[dict]:
        """Fetch opportunities for a pipeline.

        Args:
            pipeline_id: Pipeline ID from get_pipelines
            limit: Results per page (max 100)
            page: 1-indexed page number

        Returns:
            List of opportunity dicts, or [] on error
        """
        endpoint = f"/opportunities/"
        params = {
            "locationId": self.location_id,
            "pipelineId": pipeline_id,
            "limit": min(limit, 100),
            "offset": (page - 1) * limit,
        }
        result = await self._get(endpoint, params)
        return result.get("opportunities", []) if isinstance(result, dict) else []

    async def get_conversations(self, limit: int = 100, page: int = 1) -> list[dict]:
        """Fetch recent conversations for location.

        Args:
            limit: Results per page (max 100)
            page: 1-indexed page number

        Returns:
            List of conversation dicts, or [] on error
        """
        endpoint = f"/conversations/"
        params = {
            "locationId": self.location_id,
            "limit": min(limit, 100),
            "offset": (page - 1) * limit,
        }
        result = await self._get(endpoint, params)
        return result.get("conversations", []) if isinstance(result, dict) else []
