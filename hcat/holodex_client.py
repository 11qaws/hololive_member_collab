import asyncio
import time
from typing import Optional

import httpx

from .config import load_config

HOLODEX_BASE = "https://holodex.net/api/v2"
MAX_LIMIT = 50
RATE_LIMIT = 1.5
MAX_RETRIES = 5


class HolodexClient:
    def __init__(self, api_key: str = ""):
        if not api_key:
            cfg = load_config()
            api_key = cfg.get("holodex_api_key", "")
        self.api_key = api_key
        self._client = httpx.AsyncClient(
            base_url=HOLODEX_BASE,
            headers={"X-APIKEY": api_key},
            timeout=30,
        )
        self._rate_lock = asyncio.Lock()
        self._last_req = 0.0

    async def close(self):
        await self._client.aclose()

    async def _rate_limit(self):
        async with self._rate_lock:
            now = time.time()
            since = now - self._last_req
            if since < RATE_LIMIT:
                await asyncio.sleep(RATE_LIMIT - since)
            self._last_req = time.time()

    async def _get(self, path: str, params: dict | None = None) -> list:
        await self._rate_limit()
        for attempt in range(MAX_RETRIES):
            resp = await self._client.get(path, params=params)
            if resp.status_code == 429:
                wait = min(2 ** attempt * 5, 60)
                print(f"    429 rate limited, retrying in {wait}s...")
                await asyncio.sleep(wait)
                continue
            if resp.status_code == 200:
                return resp.json()
            body = resp.text[:200]
            if resp.status_code == 403 or "Illegal Access" in body:
                raise Exception(
                    "Holodex API rejected the request (Illegal Access). "
                    "Your API key may be missing, invalid, or revoked. "
                    "Run: python cli.py config --get | grep holodex_api_key"
                )
            resp.raise_for_status()
        raise Exception("Holodex API max retries exceeded")

    async def get_collabs(
        self, channel_id: str, limit: int = MAX_LIMIT, offset: int = 0
    ) -> list[dict]:
        return await self._get(
            f"/channels/{channel_id}/collabs",
            params={"limit": min(limit, MAX_LIMIT), "offset": offset},
        )

    async def get_all_collabs(self, channel_id: str) -> list[dict]:
        all_videos = []
        offset = 0
        while True:
            videos = await self.get_collabs(channel_id, offset=offset)
            if not videos:
                break
            all_videos.extend(videos)
            offset += len(videos)
            if len(videos) < MAX_LIMIT:
                break
        return all_videos

    async def batch_get_all_collabs(
        self, channel_ids: list[str]
    ) -> dict[str, list[dict]]:
        results = {}
        for cid in channel_ids:
            results[cid] = await self.get_all_collabs(cid)
        return results
