import json
from pathlib import Path
from typing import Optional

from .config import get_data_dir
from .models import Member, Appearance, MemberStatus


def load_members() -> list[Member]:
    path = get_data_dir() / "channels.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [Member.from_dict(m) for m in data.get("members", [])]


def save_members(members: list[Member]):
    path = get_data_dir() / "channels.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "version": 2,
        "members": [m.to_dict() for m in members],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def find_member(handle: str) -> Optional[Member]:
    for m in load_members():
        if m.handle.lower() == handle.lower().lstrip("@"):
            return m
    return None


def load_appearances(target_handle: str) -> list[Appearance]:
    path = get_data_dir() / "appearances" / f"{target_handle.lower()}.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [Appearance.from_dict(a) for a in data.get("appearances", [])]


def save_appearances(target_handle: str, appearances: list[Appearance]):
    path = get_data_dir() / "appearances" / f"{target_handle.lower()}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "target": target_handle.lower(),
        "count": len(appearances),
        "appearances": [a.to_dict() for a in appearances],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_appearance(target_handle: str, app: Appearance):
    apps = load_appearances(target_handle)
    exists = any(a.video_id == app.video_id and a.detection_method == app.detection_method for a in apps)
    if not exists:
        apps.append(app)
        save_appearances(target_handle, apps)
    return not exists


def load_unknowns() -> list[dict]:
    path = get_data_dir() / "unknowns.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def add_unknown(handle: str, source_channel: str, video_title: str, video_url: str):
    unknowns = load_unknowns()
    exists = any(u["handle"].lower() == handle.lower() for u in unknowns)
    if not exists:
        unknowns.append({
            "handle": handle,
            "first_seen_in": source_channel,
            "video_title": video_title,
            "video_url": video_url,
        })
        path = get_data_dir() / "unknowns.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(unknowns, f, ensure_ascii=False, indent=2)
        return True
    return False


def load_scan_state() -> dict:
    path = get_data_dir() / "scan_state.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_scan_state(state: dict):
    path = get_data_dir() / "scan_state.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
