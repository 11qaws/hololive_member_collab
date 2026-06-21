import asyncio
import time
from datetime import datetime, timedelta
from typing import Callable, Optional

from .config import load_config
from .detector import detect_mentions, detect_all_handles
from .fetcher import fetch_channel_videos_fast, extract_video_info
from .models import Member, Appearance, Branch, MemberStatus
from .storage import (
    load_members, find_member, add_appearance, load_appearances,
    save_scan_state, load_scan_state, add_unknown,
)


async def scan_for_target(
    target_handle: str,
    months: Optional[int] = None,
    count: Optional[int] = None,
    full: bool = False,
    branches: Optional[list[Branch]] = None,
    on_detected: Optional[Callable] = None,
    verbose: bool = True,
) -> tuple[list[Appearance], int]:
    """Scan for target member's appearances on other channels.

    Args:
        branches: If specified, only scan channels in these branches.
                  Defaults to all branches.

    Returns:
        (list of new appearances, total videos scanned)
    """
    target = find_member(target_handle)
    if not target:
        raise ValueError(f"Member '{target_handle}' not found in member list")

    members = load_members()
    other_members = [m for m in members if m.handle.lower() != target.handle.lower()]

    if branches:
        branch_set = set(branches)
        other_members = [m for m in other_members if m.branch in branch_set]

    # Sort by scan priority
    other_members.sort(key=lambda m: (m.branch.scan_priority, m.handle))

    cfg = load_config()
    if months is None and not full and count is None:
        months = cfg["default_scan_months"]

    all_new_appearances = []
    known_handles = {m.handle.lower() for m in members}
    total_members = len(other_members)
    grand_total_videos = 0

    # Group by yt_handle to avoid fetching same channel twice (e.g. FUWAMOCO)
    from collections import OrderedDict
    channel_groups = OrderedDict()
    for m in other_members:
        yh = m.yt_handle
        if yh not in channel_groups:
            channel_groups[yh] = []
        channel_groups[yh].append(m)
    channel_groups = list(channel_groups.items())
    total_channels = len(channel_groups)

    state_key = f"scan_{target.handle.lower()}"
    state = load_scan_state().get(state_key, {})

    for mi, (yt_handle, channel_members) in enumerate(channel_groups):
        ch_name = channel_members[0].handle
        ch_state = state.get(yt_handle, {"index": 0, "done": False})
        if ch_state.get("done"):
            if verbose:
                print(f"  [{mi+1}/{total_channels}] @{ch_name} — already done, skipping")
            continue

        # Determine limit
        per_channel_limit = None
        use_date_filter = False
        if count:
            per_channel_limit = count
        elif months and not full:
            per_channel_limit = None  # We'll fetch ALL and filter by date
            use_date_filter = True

        if verbose:
            limit_str = "ALL" if full else (
                f"last {per_channel_limit}" if per_channel_limit else f"recent {months}mo"
            )
            ch_display = "+".join(m.handle for m in channel_members) if len(channel_members) > 1 else ch_name
            print(f"  [{mi+1}/{total_channels}] @{ch_display} ({channel_members[0].branch.value}) [{limit_str}]...", end=" ")

        videos = await fetch_channel_videos_fast(yt_handle, limit=per_channel_limit)

        if use_date_filter and months:
            cutoff = datetime.now() - timedelta(days=months * 30)
            filtered = []
            for v in videos:
                upload_date = v.get("upload_date", "") or ""
                if len(upload_date) >= 8:
                    try:
                        vdate = datetime.strptime(upload_date[:8], "%Y%m%d")
                        if vdate >= cutoff:
                            filtered.append(v)
                    except ValueError:
                        filtered.append(v)
                else:
                    filtered.append(v)
            videos = filtered

        total_videos = len(videos)
        grand_total_videos += total_videos
        detected_count = 0

        resume_from = ch_state.get("index", 0)

        for vi, v in enumerate(videos):
            if vi < resume_from:
                continue

            info = extract_video_info(v, yt_handle)
            vid = info["video_id"]
            if not vid:
                continue

            title = info["title"]
            description = info["description"]

            # Check title and description for target mention
            method = detect_mentions(title, target)
            if not method:
                method = detect_mentions(description, target)

            if method:
                app = Appearance(
                    video_id=vid,
                    title=title,
                    channel_handle=ch_name,
                    channel_name=info["channel_name"],
                    published_at=info["published_at"],
                    detection_method=method,
                    url=info["url"],
                )
                is_new = add_appearance(target.handle, app)
                if is_new:
                    all_new_appearances.append(app)
                    detected_count += 1
                    msg = f"\n    → DETECTED: @{target.handle} in @{ch_name}'s \"{title[:60]}\""
                    if verbose:
                        print(msg)
                    if on_detected:
                        on_detected(app, is_new=True)

            # Discover unknown handles
            unknown_handles = detect_all_handles(description, known_handles)
            for uh in unknown_handles:
                add_unknown(uh, ch_name, title, info["url"])

            # Save progress every 20 videos
            if (vi + 1) % 20 == 0:
                state[yt_handle] = {"index": vi + 1, "done": False, "total": total_videos}
                save_scan_state({state_key: state})

        state[yt_handle] = {"index": total_videos, "done": True, "total": total_videos}
        save_scan_state({state_key: state})

        status = "✅" if detected_count > 0 else "—"
        if verbose:
            print(f" ({total_videos}v, {detected_count} found)")

    save_scan_state({state_key: state})
    return all_new_appearances, grand_total_videos


async def scan_all_unknowns(
    branches: Optional[list[Branch]] = None,
    videos_per_channel: int = 50,
    verbose: bool = True,
) -> list[dict]:
    """Scan channels to discover unknown @handles."""
    members = load_members()
    known_handles = {m.handle.lower() for m in members}
    if branches:
        branch_set = set(branches)
        members = [m for m in members if m.branch in branch_set]

    found_unknowns = []

    for mi, member in enumerate(members):
        ch = member.handle
        if verbose:
            print(f"  [{mi+1}/{len(members)}] @{ch}...", end=" ")
        videos = await fetch_channel_videos_fast(ch, limit=videos_per_channel)
        local_found = 0
        for v in videos:
            desc = v.get("description", "") or ""
            uhs = detect_all_handles(desc, known_handles)
            for uh in uhs:
                added = add_unknown(uh, ch, v.get("title", ""), f"https://youtu.be/{v.get('id', '')}")
                if added:
                    found_unknowns.append({"handle": uh, "source": ch})
                    local_found += 1
        if verbose:
            print(f" {local_found} new unknowns")

    return found_unknowns


def _build_uploader_map(members: list[Member]) -> dict[str, Member]:
    mapping = {}
    for m in members:
        if m.channel_id:
            cid = m.channel_id.strip()
            if cid:
                mapping[cid] = m
    return mapping


def _parse_holodex_date(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        from datetime import datetime
        import re
        m = re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", date_str)
        if m:
            dt = datetime.strptime(m.group(), "%Y-%m-%dT%H:%M:%S")
            return dt.strftime("%Y%m%d")
        if len(date_str) >= 10 and date_str[4] == "-":
            dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
            return dt.strftime("%Y%m%d")
    except Exception:
        pass
    return ""


def _filter_collabs_by_date(
    collabs: list[dict],
    months: int | None,
    full: bool,
) -> list[dict]:
    if full or months is None:
        return collabs
    cutoff = datetime.now() - timedelta(days=months * 30)
    filtered = []
    for v in collabs:
        ts = v.get("published_at") or v.get("available_at") or ""
        date_str = _parse_holodex_date(ts)
        if date_str:
            try:
                vdate = datetime.strptime(date_str, "%Y%m%d")
                if vdate >= cutoff:
                    filtered.append(v)
            except ValueError:
                filtered.append(v)
        else:
            filtered.append(v)
    return filtered


async def scan_for_target_via_holodex(
    target_handle: str,
    months: int | None = None,
    full: bool = False,
    branches: list[Branch] | None = None,
    on_detected: Callable | None = None,
    verbose: bool = True,
) -> tuple[list[Appearance], int]:
    from .holodex_client import HolodexClient

    target = find_member(target_handle)
    if not target:
        raise ValueError(f"Member '{target_handle}' not found")
    if not target.channel_id:
        print(f"  ⚠ @{target.handle} has no channel_id, skipping")
        return [], 0

    members = load_members()
    uploader_map = _build_uploader_map(members)

    if branches:
        branch_set = set(branches)

    cfg = load_config()
    if months is None and not full:
        months = cfg["default_scan_months"]

    client = HolodexClient()
    if verbose:
        print(f"  Fetching collabs for @{target.handle} ({target.channel_id})...", end=" ")

    raw_collabs = await client.get_all_collabs(target.channel_id, max_pages=100 if full else 0)
    collabs = _filter_collabs_by_date(raw_collabs, months, full)

    if verbose:
        print(f"{len(raw_collabs)} total, {len(collabs)} after date filter")

    all_new = []
    total = len(collabs)
    seen_video_ids = set()

    for vi, v in enumerate(collabs):
        vid = v.get("id", "")
        if not vid or vid in seen_video_ids:
            continue
        seen_video_ids.add(vid)

        uploader_cid = v.get("channel", {}).get("id", "")
        uploader = uploader_map.get(uploader_cid)

        if not uploader:
            continue

        if branches and uploader.branch not in branch_set:
            continue

        if uploader.handle.lower() == target.handle.lower():
            continue

        title = v.get("title", "") or ""
        ts = v.get("published_at") or v.get("available_at") or ""
        date_str = _parse_holodex_date(ts)

        app = Appearance(
            video_id=vid,
            title=title,
            channel_handle=uploader.handle,
            channel_name=v.get("channel", {}).get("name", ""),
            published_at=date_str,
            detection_method="holodex_collab",
            url=f"https://youtu.be/{vid}",
        )
        is_new = add_appearance(target.handle, app)
        if is_new:
            all_new.append(app)
            if verbose:
                print(f"    → DETECTED: @{target.handle} in @{uploader.handle}'s \"{title[:60]}\"")
            if on_detected:
                on_detected(app, is_new=True)

    await client.close()
    return all_new, total


async def scan_all_via_holodex(
    months: int | None = None,
    full: bool = False,
    branches: list[Branch] | None = None,
    on_detected: Callable | None = None,
    verbose: bool = True,
) -> tuple[list[Appearance], int]:
    from .holodex_client import HolodexClient

    members = load_members()
    if branches:
        branch_set = set(branches)
        scan_members = [m for m in members if m.branch in branch_set]
    else:
        scan_members = members

    uploader_map = _build_uploader_map(members)

    members_with_id = [m for m in scan_members if m.channel_id]
    if verbose:
        print(f"Fetching collabs for {len(members_with_id)}/{len(scan_members)} members via Holodex...")

    cfg = load_config()
    if months is None and not full:
        months = cfg["default_scan_months"]

    client = HolodexClient()

    # Phase 1: batch-collect all collabs concurrently
    channel_ids = [m.channel_id for m in members_with_id]
    if verbose:
        print(f"Fetching collabs for {len(channel_ids)} members (adaptive rate)...")

    raw_by_cid = await client.batch_get_all_collabs(channel_ids, max_pages=100 if full else 0)

    video_index: dict[str, dict] = {}
    total_fetched = 0
    cid_to_member = {m.channel_id: m for m in members_with_id}

    for cid, collabs in raw_by_cid.items():
        m = cid_to_member.get(cid)
        if not m:
            continue
        filtered = _filter_collabs_by_date(collabs, months, full)
        total_fetched += len(filtered)

        for v in filtered:
            vid = v.get("id", "")
            if not vid:
                continue
            if vid not in video_index:
                video_index[vid] = {
                    "video": v,
                    "targets": set(),
                }
            video_index[vid]["targets"].add(m.handle.lower())

        if verbose:
            print(f"  @{m.handle}: {len(collabs)} total, {len(filtered)} after filter")

    await client.close()

    # Phase 2: process unique videos, record appearances
    all_new = []
    processed = 0

    for vid, entry in video_index.items():
        v = entry["video"]
        targets = entry["targets"]

        uploader_cid = v.get("channel", {}).get("id", "")
        uploader = uploader_map.get(uploader_cid)
        if not uploader:
            continue

        for target_handle in targets:
            if target_handle == uploader.handle.lower():
                continue

            title = v.get("title", "") or ""
            ts = v.get("published_at") or v.get("available_at") or ""
            date_str = _parse_holodex_date(ts)

            app = Appearance(
                video_id=vid,
                title=title,
                channel_handle=uploader.handle,
                channel_name=v.get("channel", {}).get("name", ""),
                published_at=date_str,
                detection_method="holodex_collab",
                url=f"https://youtu.be/{vid}",
            )
            is_new = add_appearance(target_handle, app)
            if is_new:
                all_new.append(app)
                if verbose:
                    print(f"  → @{target_handle} appeared in @{uploader.handle}'s \"{title[:60]}\"")
                if on_detected:
                    on_detected(app, is_new=True)

        processed += 1

    if verbose:
        print(f"\nProcessed {processed} unique videos, {len(all_new)} new appearances")

    return all_new, total_fetched
