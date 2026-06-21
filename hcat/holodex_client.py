import asyncio
import time
from typing import Optional

import httpx

from .config import load_config

HOLODEX_BASE = "https://holodex.net/api/v2"
MAX_LIMIT = 50
MAX_RETRIES = 5
MAX_PAGES = 5


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
        self._lock = asyncio.Lock()
        self._min_interval = 2.0
        self._last_req = 0.0

    async def close(self):
        await self._client.aclose()

    async def _wait(self):
        async with self._lock:
            now = time.monotonic()
            since = now - self._last_req
            if since < self._min_interval:
                await asyncio.sleep(self._min_interval - since)
            self._last_req = time.monotonic()

    async def _get(self, path: str, params: dict | None = None) -> list:
        await self._wait()
        for attempt in range(MAX_RETRIES):
            resp = await self._client.get(path, params=params)

            if resp.status_code == 200:
                return resp.json()

            if resp.status_code == 429:
                retry = int(resp.headers.get("retry-after", min(2 ** attempt * 10, 120)))
                self._min_interval = min(self._min_interval * 2, 30)
                print(f"    429 — slowing to 1/{self._min_interval:.0f}s, retry in {retry}s")
                await asyncio.sleep(retry)
                continue

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
    ) -> list:
        return await self._get(
            f"/channels/{channel_id}/collabs",
            params={"limit": min(limit, MAX_LIMIT), "offset": offset},
        )

    async def get_all_collabs(self, channel_id: str, max_pages: int = 0) -> list:
        all_videos = []
        offset = 0
        pages = 0
        page_limit = max_pages if max_pages > 0 else MAX_PAGES
        while pages < page_limit:
            videos = await self.get_collabs(channel_id, offset=offset)
            if not videos:
                break
            all_videos.extend(videos)
            offset += len(videos)
            pages += 1
            if len(videos) < MAX_LIMIT:
                break
        return all_videos

    async def batch_get_all_collabs(self, channel_ids: list[str], max_pages: int = 0) -> dict[str, list]:
        results = {}
        for cid in channel_ids:
            results[cid] = await self.get_all_collabs(cid, max_pages=max_pages)
        return results
