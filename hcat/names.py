"""Nickname mapping for Hololive members."""
from .models import Branch, Member


NICKNAMES: dict[str, str] = {
    # EN — 이번 세션 지정
    "moricalliope": "Calli",
    "ninomaeinanis": "Ina",
    "holoen_raorapanthera": "Raora",
    "akirose": "Akirose",
    # EN — 기존 예외
    "irys": "IRyS",
    "holoen_erbloodflame": "ERB",
    "holoen_ceciliaimmergreen": "Cecilia",
    "holoen_gigimurin": "Gigi",
    "shiorinovella": "Shiori",
    "nerissaravencroft": "Nerissa",
    "fuwawa_abyssgard": "Fuwawa",
    "mococo_abyssgard": "Mococo",
    # ID
    "moona_hoshinova": "Moona",
    "airaniiofifteen": "Iofi",
    "aniamelfissa": "Anya",
    "kaelakovalskia": "Kaela",
    "kobokanaeru": "Kobo",
    # JP
    "robocosan": "Roboco",
    "ladarknesss": "La+",
    "azki": "AZKi",
}


def get_nickname(handle: str, member_name: str = "") -> str:
    """Return display nickname for a handle.

    Priority:
    1. NICKNAMES override
    2. Last word of english_name
    3. handle as fallback
    """
    if handle in NICKNAMES:
        return NICKNAMES[handle]
    if member_name:
        parts = member_name.strip().split()
        if len(parts) >= 2:
            return parts[-1]
        return member_name
    return handle


def build_nicknames_map(members: list[Member]) -> dict[str, str]:
    return {m.handle: get_nickname(m.handle, m.english_name) for m in members}
