import asyncio
import time
from typing import Optional

import httpx

from .config import load_config

HOLODEX_BASE = "https://holodex.net/api/v2"
MAX_LIMIT = 50
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

    async def _request(self, path: str, params: dict | None = None) -> httpx.Response:
        while True:
            await self._wait()
            try:
                resp = await self._client.get(path, params=params)
            except httpx.HTTPError as e:
                print(f"  ⚠ HTTP error: {e}, retrying in 60s...")
                await asyncio.sleep(60)
                continue

            status = resp.status_code

            if status == 200:
                return resp

            if status == 429:
                try:
                    retry = int(resp.headers.get("retry-after", 60))
                except (ValueError, TypeError):
                    retry = 60
                retry = max(retry, 30)
                self._min_interval = min(self._min_interval * 2, 60)
                print(f"    429 — waiting {retry}s (rate: 1/{self._min_interval:.0f}s)")
                await asyncio.sleep(retry)
                continue

            body = resp.text[:200]
            if status == 403 or "Illegal Access" in body:
                raise Exception(
                    "Holodex API rejected the request (Illegal Access). "
                    "Your API key may be missing, invalid, or revoked. "
                    "Run: python cli.py config --get | grep holodex_api_key"
                )

            print(f"  ⚠ HTTP {status}: {body}")
            try:
                resp.raise_for_status()
            except httpx.HTTPError as e:
                print(f"    → retrying in 60s...")
                await asyncio.sleep(60)
                continue

    async def get_collabs(
        self, channel_id: str, limit: int = MAX_LIMIT, offset: int = 0
    ) -> list:
        resp = await self._request(
            f"/channels/{channel_id}/collabs",
            params={"limit": min(limit, MAX_LIMIT), "offset": offset},
        )
        return resp.json()

    async def get_channel(self, channel_id: str) -> dict:
        resp = await self._request(f"/channels/{channel_id}")
        return resp.json()

    async def get_channel_videos(self, channel_id: str, limit: int = MAX_LIMIT, offset: int = 0) -> list:
        resp = await self._request(
            f"/channels/{channel_id}/videos",
            params={"limit": min(limit, MAX_LIMIT), "offset": offset},
        )
        return resp.json()

    async def get_all_videos(self, channel_id: str, max_pages: int = 5) -> list:
        all_videos = []
        offset = 0
        pages = 0
        while pages < max_pages:
            videos = await self.get_channel_videos(channel_id, offset=offset)
            if not videos:
                break
            all_videos.extend(videos)
            offset += len(videos)
            pages += 1
            if len(videos) < MAX_LIMIT:
                break
        return all_videos

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
