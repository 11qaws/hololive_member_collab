import asyncio
import time
from typing import Optional

import httpx

from .config import load_config

HOLODEX_BASE = "https://holodex.net/api/v2"
MAX_LIMIT = 50
MAX_CONCURRENT = 2
MAX_RETRIES = 5


class _TokenBucket:
    def __init__(self, rate: float, burst: int):
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.last = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last = now
            if self.tokens < 1:
                wait = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait)
                self.tokens = 0
            else:
                self.tokens -= 1


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
        self._bucket = _TokenBucket(rate=1.0, burst=2)
        self._sem = asyncio.Semaphore(MAX_CONCURRENT)

    async def close(self):
        await self._client.aclose()

    async def _get(self, path: str, params: dict | None = None) -> list:
        async with self._sem:
            await self._bucket.acquire()
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
        async def _fetch(cid: str) -> tuple[str, list[dict]]:
            return cid, await self.get_all_collabs(cid)

        tasks = [_fetch(cid) for cid in channel_ids]
        results = {}
        for coro in asyncio.as_completed(tasks):
            cid, videos = await coro
            results[cid] = videos
        return results
