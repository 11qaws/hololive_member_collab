import asyncio
import time
from typing import Optional

import httpx

from .config import load_config

HOLODEX_BASE = "https://holodex.net/api/v2"
MAX_LIMIT = 50
RATE_LIMIT = 0.75  # ~80 req/min → 0.75s between requests
MAX_CONCURRENT = 5


def _mkclient(api_key: str) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=HOLODEX_BASE,
        headers={"X-APIKEY": api_key},
        timeout=30,
    )


class HolodexClient:
    def __init__(self, api_key: str = ""):
        if not api_key:
            cfg = load_config()
            api_key = cfg.get("holodex_api_key", "")
        self.api_key = api_key
        self._client = _mkclient(api_key)
        self._rate_lock = asyncio.Lock()
        self._last_req = 0.0
        self._sem = asyncio.Semaphore(MAX_CONCURRENT)

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
        async with self._sem:
            resp = await self._client.get(path, params=params)
            resp.raise_for_status()
            return resp.json()

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
        async def _fetch(cid: str) -> tuple[str, list[dict]]:
            return cid, await self.get_all_collabs(cid)

        tasks = [_fetch(cid) for cid in channel_ids]
        results = {}
        for coro in asyncio.as_completed(tasks):
            cid, videos = await coro
            results[cid] = videos
        return results
