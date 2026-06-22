"""Timeline: merge self videos + collab appearances per member."""
import asyncio
import re
from collections import defaultdict

from .config import load_config
from .models import TimelineEntry
from .storage import load_members, load_appearances, load_timeline, save_timeline


def _parse_yymmdd(s: str) -> str:
    s = (s or "").strip()
    if len(s) >= 10 and s[4] == "-":
        return s[:10].replace("-", "")
    if len(s) >= 8 and s.isdigit():
        return s[:8]
    return s[:8].replace("-", "")


def _normalize_series(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r'[:：]\s*(chapter|season|ep|episode|part|vol|volume)\s*\d+.*$', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\s+#\d+.*$', '', s)
    s = re.sub(r'\s+\d+\s*$', '', s)
    s = re.sub(r'\s*[#]\s*$', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def _extract_series(title: str) -> str | None:
    m = re.search(r'[【≪\[\(](.+?)[】≫\]\)]', title.strip())
    return m.group(1) if m else None


_ENRECO_KEYWORDS = ["enreco", "enigmatic"]


def _has_enreco_tag(title: str) -> bool:
    low = title.lower()
    return any(kw in low for kw in _ENRECO_KEYWORDS)


def _content_group_key(title: str) -> str:
    if _has_enreco_tag(title):
        return "enigmatic recollection"
    series = _extract_series(title)
    if series:
        return _normalize_series(series)
    return title[:30].rstrip()


def _representative_title(title: str) -> str:
    raw = _extract_series(title)
    if not raw:
        return title[:50].rstrip()
    clean = re.sub(r'[:：]\s*(Chapter|Season|Ep|Episode|Part|Vol|Volume)\s*\d+.*$', '', raw).strip()
    clean = re.sub(r'\s+#\d+.*$', '', clean).strip()
    clean = re.sub(r'\s+\d+\s*$', '', clean).strip()
    return clean or raw


def _collab_entries(handle: str) -> list[TimelineEntry]:
    apps = load_appearances(handle)
    out = []
    for a in apps:
        if a.detection_method != "holodex_collab":
            continue
        out.append(TimelineEntry(
            video_id=a.video_id,
            title=a.title,
            published_at=_parse_yymmdd(a.published_at),
            url=a.url,
            entry_type="collab",
            thumbnail=f"https://img.youtube.com/vi/{a.video_id}/mqdefault.jpg",
            partner_handle=a.channel_handle,
            partner_name=a.channel_name,
        ))
    return out


async def fetch_self_videos(client, channel_id: str, months: int = 3, max_pages: int = 10) -> list[TimelineEntry]:
    from datetime import datetime, timedelta
    from .holodex_client import HolodexClient

    raw = await client.get_all_videos(channel_id, max_pages=max_pages)
    cutoff = (datetime.utcnow() - timedelta(days=months * 30)).strftime("%Y%m%d")
    out = []
    for v in raw:
        pid = _parse_yymmdd(v.get("published_at", ""))
        if pid < cutoff:
            continue
        out.append(TimelineEntry(
            video_id=v.get("id", ""),
            title=v.get("title", ""),
            published_at=pid,
            url=f"https://youtu.be/{v.get('id', '')}",
            entry_type="self",
            thumbnail=v.get("thumbnail", "") or f"https://img.youtube.com/vi/{v.get('id', '')}/mqdefault.jpg",
        ))
    return out


async def refresh_timeline(handle: str, months: int = 3, full: bool = False) -> list[TimelineEntry]:
    from .holodex_client import HolodexClient
    from .storage import find_member

    member = find_member(handle)
    if not member or not member.channel_id:
        print(f"  ⚠ @{handle} has no channel_id")
        return []

    client = HolodexClient()
    max_pages = 100 if full else 10
    self_vids = await fetch_self_videos(client, member.channel_id, months=months, max_pages=max_pages)
    await client.close()

    collabs = _collab_entries(handle)

    flat_count = len(collabs)
    merged = sorted(self_vids + collabs, key=lambda e: e.published_at, reverse=True)
    save_timeline(handle, merged)
    print(f"  @{handle}: {len(self_vids)} self + {flat_count} collab = {len(merged)} timeline entries")
    return merged


async def refresh_all_timelines(months: int = 3, full: bool = False):
    members = load_members()
    with_id = [m for m in members if m.channel_id]
    for i, m in enumerate(with_id):
        print(f"[{i + 1}/{len(with_id)}] ", end="")
        try:
            await refresh_timeline(m.handle, months=months, full=full)
        except Exception as e:
            print(f"  @{m.handle}: ERROR {e}")


def load_timeline_entries(handle: str) -> list[TimelineEntry]:
    entries = load_timeline(handle)
    selfs = [e for e in entries if e.entry_type == "self"]
    collabs = [e for e in entries if e.entry_type == "collab"]

    for e in entries:
        e._content_key = _content_group_key(e.title)

    groups: dict[tuple[str, str], list[TimelineEntry]] = {}
    for e in collabs:
        key = (e.published_at, e._content_key)
        groups.setdefault(key, []).append(e)

    grouped_collabs: list[TimelineEntry] = []
    for (date, ck), group_entries in groups.items():
        if len(group_entries) == 1:
            grouped_collabs.append(group_entries[0])
        else:
            primary = group_entries[0]
            primary.sub_entries = [
                {
                    "video_id": e.video_id,
                    "title": e.title,
                    "url": e.url,
                    "partner_handle": e.partner_handle,
                    "partner_name": e.partner_name,
                    "thumbnail": e.thumbnail,
                }
                for e in group_entries
            ]
            primary.title = _representative_title(primary.title)
            grouped_collabs.append(primary)

    # Index self entries by (date, content_key)
    self_by_ck: dict[tuple[str, str], TimelineEntry] = {}
    for s in selfs:
        key = (s.published_at, s._content_key)
        if key not in self_by_ck:
            self_by_ck[key] = s

    used_self: set[int] = set()
    for c in grouped_collabs:
        key = (c.published_at, c._content_key)
        if key in self_by_ck:
            s = self_by_ck[key]
            if id(s) not in used_self:
                c.paired_self = {
                    "video_id": s.video_id,
                    "title": s.title,
                    "url": s.url,
                    "thumbnail": s.thumbnail,
                    "published_at": s.published_at,
                }
                used_self.add(id(s))

    result = [s for s in selfs if id(s) not in used_self]
    result += grouped_collabs
    result.sort(key=lambda e: e.published_at, reverse=True)
    return result
