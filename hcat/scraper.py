"""Scrape Hololive official website for talent member list.
The official site at /en/talents/ lists all members with their status (active/alum/affiliate/retirement).
Each talent's individual page has their YouTube channel link."""
import asyncio
import re
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .models import Member, MemberStatus, Branch
from .storage import save_members

TALENTS_URL = "https://hololive.hololivepro.com/en/talents/"
KNOWN_YOUTUBE_CHANNELS = {
    # Channel ID -> (yt_handle, branch)
    # Known mappings from channel IDs
}

# Slug to YouTube handle mapping (verified)
SLUG_TO_HANDLE = {
    # EN
    "mori-calliope": "moricalliope",
    "takanashi-kiara": "takanashikiara",
    "ninomae-inanis": "ninomaeinanis",
    "irys": "irys",
    "ouro-kronii": "ourokronii",
    "hakos-baelz": "hakosbaelz",
    "shiori-novella": "shiorinovella",
    "koseki-bijou": "kosekibijou",
    "nerissa-ravencroft": "nerissaravencroft",
    "fuwawa-abyssgard": "fuwawa_abyssgard",
    "mococo-abyssgard": "mococo_abyssgard",
    "elizabeth-rose-bloodflame": "holoen_erbloodflame",
    "gigi-murin": "holoen_gigimurin",
    "cecilia-immergreen": "holoen_ceciliaimmergreen",
    "raora-panthera": "holoen_raorapanthera",
    "gawr-gura": "gawrgura",
    "watson-amelia": "watsonamelia",
    "ceres-fauna": "ceresfauna",
    "nanashi-mumei": "nanashimumei",
    "tsukumo-sana": "tsukumosana",
    # JP
    "tokino-sora": "tokinosora",
    "roboco-san": "robocosan",
    "sakuramiko": "sakuramiko",
    "aki-rosenthal": "akirose",
    "akai-haato": "akaihaato",
    "shirakami-fubuki": "shirakamifubuki",
    "natsuiro-matsuri": "natsuiromatsuri",
    "nakiri-ayame": "nakiri_ayame",
    "yuzuki-choco": "yuzuki_choco",
    "oozora-subaru": "oozora_subaru",
    "azki": "azki",
    "ookami-mio": "ookamimio",
    "nekomata-okayu": "nekomataokayu",
    "inugami-korone": "inugamikorone",
    "hoshimachi-suisei": "hoshimachisuisei",
    "usada-pekora": "usadapekora",
    "shiranui-flare": "shiranuiflare",
    "shirogane-noel": "shiroganenoel",
    "houshou-marine": "houshoumarine",
    "tsunomaki-watame": "tsunomakiwatame",
    "tokoyami-towa": "tokoyamitowa",
    "himemori-luna": "himemoriluna",
    "yukihana-lamy": "yukihanalamy",
    "momosuzu-nene": "momosuzunene",
    "shishiro-botan": "shishirobotan",
    "omaru-polka": "omarupolka",
    "la-darknesss": "ladarknesss",
    "takane-lui": "takanelui",
    "hakui-koyori": "hakuikoyori",
    "sakamata-chloe": "sakamatachloe",
    "kazama-iroha": "kazamairoha",
    "minato-aqua": "minatoaqua",
    "murasaki-shion": "murasakishion",
    "amane-kanata": "amanekanata",
    "kiryu-coco": "kiryucoco",
    # ID
    "ayunda-risu": "ayunda_risu",
    "moona-hoshinova": "moona_hoshinova",
    "airani-iofifteen": "airaniiofifteen",
    "kureiji-ollie": "kureijiollie",
    "anya-melfissa": "aniamelfissa",
    "pavolia-reine": "pavoliareine",
    "vestia-zeta": "vestia_zeta",
    "kaela-kovalskia": "kaelakovalskia",
    "kobo-kanaeru": "kobokanaeru",
    # DEV_IS
    "otonose-kanade": "otonosekanade",
    "ichijou-ririka": "ichijouririka",
    "juufuutei-raden": "juufuuteiraden",
    "todoroki-hajime": "todorokihajime",
    "isaki-riona": "isakiriona",
    "koganei-niko": "koganei_niko",
    "mizumiya-su": "mizumiya_su",
    "rindo-chihaya": "rindo_chihaya",
    "kikirara-vivi": "kikirara_vivi",
    "izuki-michiru": "izuki_michiru",
    "hanazono-sayaka": "hanazono_sayaka",
    "kazeshiro-yuki": "kazeshiro_yuki",
    "hiodoshi-ao": "hiodoshi_ao",
    # retired
    "harusaki-nodoka": "harusaki_nodoka",
    "friend-a": "friend_a",
}


def _parse_status_from_text(name_text: str) -> MemberStatus:
    if "[Alum]" in name_text:
        return MemberStatus.GRADUATED
    if "[Retirement]" in name_text:
        return MemberStatus.GRADUATED
    if "[Affiliate]" in name_text:
        return MemberStatus.ACTIVE  # Affiliates still have active channels
    return MemberStatus.ACTIVE


def _slug_to_branch(slug: str, status: MemberStatus) -> Branch:
    """Determine branch based on slug patterns and official site categories."""
    en_slugs = {
        "mori-calliope","takanashi-kiara","ninomae-inanis","irys","ouro-kronii",
        "hakos-baelz","shiori-novella","koseki-bijou","nerissa-ravencroft",
        "fuwawa-abyssgard","mococo-abyssgard","elizabeth-rose-bloodflame",
        "gigi-murin","cecilia-immergreen","raora-panthera",
        "gawr-gura","watson-amelia","ceres-fauna","nanashi-mumei","tsukumo-sana",
    }
    id_slugs = {
        "ayunda-risu","moona-hoshinova","airani-iofifteen","kureiji-ollie",
        "anya-melfissa","pavolia-reine","vestia-zeta","kaela-kovalskia","kobo-kanaeru",
    }
    devis_slugs = {
        "otonose-kanade","ichijou-ririka","juufuutei-raden","todoroki-hajime",
        "isaki-riona","koganei-niko","mizumiya-su","rindo-chihaya","kikirara-vivi",
        "izuki-michiru","hanazono-sayaka","kazeshiro-yuki","hiodoshi-ao",
    }
    if slug in en_slugs:
        return Branch.EN
    if slug in id_slugs:
        return Branch.ID
    if slug in devis_slugs:
        return Branch.DEV_IS
    return Branch.JP


def scrape_talent_list() -> list[dict]:
    """Scrape the talent listing page for all members with their slugs and statuses."""
    resp = requests.get(TALENTS_URL, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    talents = []
    seen_slugs = set()

    for card in soup.find_all("a", href=True):
        href = card["href"]
        if "/en/talents/" not in href:
            continue
        slug = href.rstrip("/").split("/")[-1]
        if slug in seen_slugs or not slug or slug == "talents":
            continue
        seen_slugs.add(slug)

        full_text = card.get_text(" ", strip=True)
        status = _parse_status_from_text(full_text)
        # Clean status prefix from name
        name = full_text
        for prefix in ["[Alum] ", "[Affiliate] ", "[Retirement] "]:
            name = name.replace(prefix, "")

        talents.append({
            "slug": slug,
            "name": name,
            "status": status,
        })

    return talents


async def _resolve_yt_handle(slug: str, channel_id: str) -> str:
    """Resolve a channel ID to a YouTube @handle using yt-dlp."""
    if slug in SLUG_TO_HANDLE:
        return SLUG_TO_HANDLE[slug]
    try:
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", "--dump-json", "--no-warnings",
            f"https://www.youtube.com/channel/{channel_id}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
        if stdout:
            import json
            data = json.loads(stdout.decode("utf-8", errors="replace"))
            uploader_id = data.get("uploader_id", "")
            if uploader_id:
                return uploader_id.lstrip("@")
    except Exception:
        pass
    return slug.replace("-", "").replace("_", "").lower()


def _scrape_channel_id(slug: str) -> Optional[str]:
    """Scrape a talent's individual page for their YouTube channel ID."""
    url = f"https://hololive.hololivepro.com/en/talents/{slug}/"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "youtube.com/channel/" in href:
                match = re.search(r"youtube\.com/channel/(UC[\w-]+)", href)
                if match:
                    cid = match.group(1)
                    # Skip the hololive official channel (used as a global link)
                    if cid != "UCJFZiqLMntJufDCHc6bQixg" and cid not in seen:
                        seen.add(cid)
        # Return the first unique channel ID found (skip official)
        for cid in seen:
            return cid
    except Exception:
        pass
    return None


async def update_member_list():
    """Full pipeline: scrape official site → resolve handles → save."""
    talents = scrape_talent_list()
    print(f"Found {len(talents)} talents on official site")

    members = []
    SHARED_CHANNELS = {
        "fuwawa-abyssgard": "fuwamococh",
        "mococo-abyssgard": "fuwamococh",
    }
    for t in talents:
        slug = t["slug"]
        name = t["name"]
        status = t["status"]
        branch = _slug_to_branch(slug, status)

        channel_id = _scrape_channel_id(slug)
        handle = SLUG_TO_HANDLE.get(slug, slug.replace("-", "").lower())

        if not channel_id:
            channel_id = ""

        # Handle shared channels (e.g. FUWAMOCO)
        channel_handle = SHARED_CHANNELS.get(slug, None)

        members.append(Member(
            handle=handle,
            name=name.split("[")[0].strip(),
            channel_id=channel_id or "",
            channel_handle=channel_handle,
            branch=branch,
            status=status,
        ))

        time.sleep(0.3)  # Rate limiting

    # Add official channels (they're on YouTube but not in the talent listing)
    official_channels = [
        Member("hololive", "ホロライブ公式", branch=Branch.OFFICIAL, channel_id="UCJFZiqLMntJufDCHc6bQixg"),
        Member("hololiveenglish", "hololive English", branch=Branch.OFFICIAL),
        Member("hololiveindonesia", "hololive Indonesia", branch=Branch.OFFICIAL),
    ]
    members.extend(official_channels)

    save_members(members)
    print(f"Saved {len(members)} members to channels.json")

    from .storage import get_data_dir
    import json
    path = get_data_dir() / "channels.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["_source"] = "official_hololivepro_site"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Print summary
    for b in Branch:
        bm = [m for m in members if m.branch == b]
        if bm:
            active = [m for m in bm if m.status == MemberStatus.ACTIVE]
            graduated = [m for m in bm if m.status != MemberStatus.ACTIVE]
            parts = [f"  {b.value}: {len(bm)}"]
            if active:
                parts[-1] += f" ({len(active)} active"
                if graduated:
                    parts[-1] += f", {len(graduated)} graduated"
                parts[-1] += ")"
            print(parts[-1])

    return members
