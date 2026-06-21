import asyncio
import json
from typing import AsyncIterator, Optional

from .config import load_config


async def _run_ytdlp(args: list[str], timeout: int = 120) -> Optional[bytes]:
    """Run yt-dlp and return stdout bytes."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        if stdout:
            return stdout
        if stderr:
            err_text = stderr.decode("utf-8", errors="replace")[:200]
            if "ERROR" in err_text or "Warning" in err_text:
                pass  # non-fatal, just return None
        return None
    except asyncio.TimeoutError:
        return None
    except Exception:
        return None


async def fetch_channel_videos_fast(
    channel_handle: str,
    limit: Optional[int] = None,
    months: Optional[int] = None,
) -> list[dict]:
    """Fetch video metadata (including descriptions) for a channel using a single yt-dlp command.
    
    This is MUCH faster than fetching videos individually because yt-dlp processes
    the channel playlist internally in a single process.
    """
    cfg = load_config()
    url = f"https://www.youtube.com/@{channel_handle}/videos"

    cmd = [
        "--dump-json",
        "--no-warnings",
        "--ignore-errors",
        "--skip-download",
        "--sleep-interval", str(cfg["sleep_between_videos"]),
        "--max-sleep-interval", "1.0",
        "--extractor-args", "youtubetab:approximate_date=0",
        url,
    ]

    if limit:
        cmd = ["--playlist-end", str(limit)] + cmd
    else:
        cmd = [""] + cmd  # dummy to make the logic work

    if limit:
        full_cmd = ["--playlist-end", str(limit), *cmd[1:]]
    else:
        full_cmd = cmd[1:]

    stdout = await _run_ytdlp(full_cmd, timeout=cfg["ytdlp_timeout"] * 3)
    if not stdout:
        return []

    videos = []
    text = stdout.decode("utf-8", errors="replace")
    for line in text.strip().split("\n"):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            # Only include videos that have a description
            if data.get("description") is not None:
                videos.append(data)
        except json.JSONDecodeError:
            continue

    return videos


def extract_video_info(data: dict, channel_handle: str) -> dict:
    """Extract relevant fields from raw yt-dlp output."""
    return {
        "video_id": data.get("id", ""),
        "title": data.get("title", "") or "",
        "description": data.get("description", "") or "",
        "channel_handle": channel_handle,
        "channel_name": data.get("channel", data.get("uploader", "")),
        "published_at": data.get("upload_date", "") or "",
        "url": f"https://youtu.be/{data.get('id', '')}",
    }


async def fetch_channel_info(channel_handle: str) -> Optional[dict]:
    """Fetch basic channel info (handle, name, etc.) from yt-dlp."""
    args = [
        "--dump-json",
        "--no-warnings",
        "--ignore-errors",
        "--skip-download",
        "--playlist-end", "1",
        f"https://www.youtube.com/@{channel_handle}",
    ]
    stdout = await _run_ytdlp(args, timeout=30)
    if not stdout:
        return None
    try:
        data = json.loads(stdout.decode("utf-8", errors="replace").strip().split("\n")[0])
        return {
            "channel": data.get("channel", data.get("uploader", "")),
            "uploader_id": data.get("uploader_id", ""),
            "channel_url": data.get("channel_url", ""),
            "channel_id": data.get("channel_id", ""),
        }
    except (json.JSONDecodeError, IndexError):
        return None


async def fetch_channel_info_by_id(channel_id: str) -> Optional[dict]:
    """Fetch channel info by channel ID."""
    args = [
        "--dump-json",
        "--no-warnings",
        "--ignore-errors",
        "--skip-download",
        "--playlist-end", "1",
        f"https://www.youtube.com/channel/{channel_id}",
    ]
    stdout = await _run_ytdlp(args, timeout=30)
    if not stdout:
        return None
    try:
        data = json.loads(stdout.decode("utf-8", errors="replace").strip().split("\n")[0])
        return {
            "channel": data.get("channel", data.get("uploader", "")),
            "uploader_id": data.get("uploader_id", "").lstrip("@"),
            "channel_url": data.get("channel_url", ""),
            "channel_id": data.get("channel_id", ""),
        }
    except (json.JSONDecodeError, IndexError):
        return None
