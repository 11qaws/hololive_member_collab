import re
from typing import Optional

from .models import Member


def detect_mentions(text: str, target: Member) -> Optional[str]:
    """Check if text (title or description) mentions the target member.
    Returns the detection method string or None.
    """
    if not text:
        return None

    text_lower = text.lower()
    match_handles = target.match_handles
    name_lower = target.name.lower()

    # Pattern 1: @handle mentions
    for handle in match_handles:
        patterns = [
            rf'(?:^|\s|[#@✨🌸])@{re.escape(handle)}\b',
            rf'(?:^|\s|[#@✨🌸]){re.escape(handle)}\b',
            rf'youtube\.com/@{re.escape(handle)}\b',
        ]
        for pat in patterns:
            if re.search(pat, text_lower):
                return "mention"

    # Pattern 2: channel URL with channel ID
    if target.channel_id:
        ch_pat = rf'youtube\.com/channel/{re.escape(target.channel_id)}'
        if re.search(ch_pat, text_lower):
            return "channel_id"

    # Pattern 3: Display name match (lower confidence)
    # Skip common short names to avoid false positives
    if len(name_lower) > 4:
        if name_lower in text_lower:
            return "name_match"

    return None


def detect_all_handles(text: str, known_handles: set[str]) -> list[str]:
    """Extract all @handle mentions from text, returning unknown ones."""
    if not text:
        return []

    found = set()
    matches = re.findall(r'@(\w[\w.-]*)', text)
    for m in matches:
        m = m.lower().lstrip("@")
        # Check if this handle or any known member's match_handles contain it
        if m not in known_handles:
            found.add(m)
    return list(found)


def is_collab_title(title: str) -> bool:
    """Check if the video title suggests a collaboration."""
    if not title:
        return False
    keywords = [
        "collab", "コラボ", "合作", "一緒", "with", "×", "⚔", "vs",
        "feat.", "feat", "guest", "ゲスト",
    ]
    t = title.lower()
    return any(k in t for k in keywords)
