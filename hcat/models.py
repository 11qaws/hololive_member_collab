from dataclasses import dataclass, field, asdict, fields
from typing import Optional
from enum import Enum


class MemberStatus(str, Enum):
    ACTIVE = "active"
    GRADUATED = "graduated"
    TERMINATED = "terminated"


class Branch(str, Enum):
    JP = "JP"
    EN = "EN"
    ID = "ID"
    DEV_IS = "DEV_IS"
    OFFICIAL = "Official"
    HOLOSTARS = "Holostars"
    OTHER = "Other"

    @property
    def scan_priority(self) -> int:
        order = [Branch.EN, Branch.OFFICIAL, Branch.ID, Branch.JP, Branch.DEV_IS, Branch.HOLOSTARS, Branch.OTHER]
        return order.index(self)


@dataclass
class Member:
    handle: str
    name: str
    channel_id: Optional[str] = None
    channel_handle: Optional[str] = None  # actual YouTube @handle (if different from `handle`)
    branch: Branch = Branch.OTHER
    status: MemberStatus = MemberStatus.ACTIVE
    graduated_at: Optional[str] = None
    photo_url: Optional[str] = None

    def to_dict(self):
        d = {}
        for k, v in asdict(self).items():
            if isinstance(v, Enum):
                d[k] = v.value
            else:
                d[k] = v
        return d

    @classmethod
    def from_dict(cls, d):
        d = dict(d)
        if "branch" in d and isinstance(d["branch"], str):
            d["branch"] = Branch(d["branch"])
        if "status" in d and isinstance(d["status"], str):
            d["status"] = MemberStatus(d["status"])
        valid = {f.name for f in fields(cls)}
        d = {k: v for k, v in d.items() if k in valid}
        return cls(**d)

    @property
    def yt_handle(self) -> str:
        """Return the YouTube handle to match in descriptions."""
        return (self.channel_handle or self.handle).lower()

    @property
    def match_handles(self) -> list[str]:
        """Return all handles that might mention this member in descriptions."""
        base = self.yt_handle
        handles = [base]
        # Also match with common variations
        if "_" in base:
            handles.append(base.replace("_", ""))
        if base != self.handle.lower():
            handles.append(self.handle.lower())
        return list(set(handles))


@dataclass
class Appearance:
    video_id: str
    title: str
    channel_handle: str
    channel_name: str
    published_at: str
    detection_method: str
    url: str
    status: str = "unreviewed"
    note: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        valid = {f.name for f in fields(cls)}
        d = {k: v for k, v in d.items() if k in valid}
        return cls(**d)


@dataclass
class TimelineEntry:
    video_id: str
    title: str
    published_at: str  # YYYYMMDD
    url: str
    entry_type: str  # "stream" or "collab"
    thumbnail: str = ""
    partner_handle: str = ""  # primary partner handle
    partner_name: str = ""  # primary partner name
    sub_entries: list[dict] = field(default_factory=list)  # grouped collab: [{...}, ...]
    paired_self: Optional[dict] = None  # set at load time: {video_id, title, url, thumbnail}
    _content_key: str = ""  # runtime: normalized content key for pairing

    def to_dict(self):
        d = asdict(self)
        d.pop("paired_self", None)
        d.pop("_content_key", None)
        return d

    @classmethod
    def from_dict(cls, d):
        valid = {f.name for f in fields(cls) if not f.name.startswith("_")}
        d = {k: v for k, v in d.items() if k in valid}
        if d.get("entry_type") == "self":
            d["entry_type"] = "stream"
        return cls(**d)


SCAN_GROUP_ORDER = [
    Branch.EN,
    Branch.OFFICIAL,
    Branch.ID,
    Branch.JP,
    Branch.DEV_IS,
    Branch.HOLOSTARS,
    Branch.OTHER,
]
