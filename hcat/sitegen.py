"""GitHub Pages static site generator."""
import json
import shutil
from datetime import datetime
from pathlib import Path

import jinja2

from .config import get_data_dir
from .models import Member, Branch, MemberStatus, Appearance, generation_sort_key
from .storage import load_members, load_appearances
from .timeline import load_timeline_entries, extract_partner_handles, top_collab_partners, group_partners_by_branch, fuwamoco_display


def _fix_links(html: str) -> str:
    html = html.replace('href="/member/', 'href="members/')
    html = html.replace('href="/stats"', 'href="stats.html"')
    html = html.replace('href="/unknowns"', 'href="unknowns.html"')
    html = html.replace('href="/"', 'href="index.html"')
    return html


def _fix_links_member(html: str, handle: str) -> str:
    html = html.replace('href="/member/', 'href="members/')
    html = html.replace('href="/stats"', 'href="../stats.html"')
    html = html.replace('href="/unknowns"', 'href="../unknowns.html"')
    html = html.replace('href="/"', 'href="../index.html"')
    html = html.replace(
        'await fetch(`/api/appearance/',
        '/* static */ console.log(')
    return html


def build_site():
    data_dir = get_data_dir()
    site_dir = data_dir.parent  # repo root

    members_dir = site_dir / "members"
    for p in [site_dir / "index.html", site_dir / "stats.html", site_dir / "unknowns.html"]:
        if p.exists():
            p.unlink()
    if members_dir.exists():
        shutil.rmtree(members_dir)
    members_dir.mkdir(parents=True)

    members = load_members()

    tmpl_dir = Path(__file__).parent.parent / "web" / "templates"
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(tmpl_dir)))
    env.globals["fuwamoco_display"] = fuwamoco_display

    # ── Index page ──
    by_branch = []
    for b in [Branch.EN, Branch.JP, Branch.ID, Branch.OFFICIAL, Branch.DEV_IS, Branch.HOLOSTARS, Branch.OTHER]:
        bm = [m for m in members if m.branch == b]
        if bm:
            bm.sort(key=generation_sort_key)
            by_branch.append((b.value, bm))
    html = _fix_links(env.get_template("index.html").render(branches=by_branch))
    (site_dir / "index.html").write_text(html, encoding="utf-8")

    # ── Member pages ──
    for m in members:
        timeline = load_timeline_entries(m.handle)
        streams = len([e for e in timeline if e.entry_type == "stream"])
        collabs = sum(len(e.sub_entries) if e.sub_entries else 1 for e in timeline if e.entry_type == "collab")
        partner_handles = extract_partner_handles(timeline)
        top_partners = top_collab_partners(timeline)
        partner_groups = group_partners_by_branch(partner_handles, members)
        member_photos = {m2.handle: m2.photo_url for m2 in members if m2.photo_url}
        html = _fix_links_member(
            env.get_template("member.html").render(
                member=m, timeline=timeline,
                streams=streams, collabs=collabs, partner_handles=partner_handles,
                partner_groups=partner_groups, top_partners=top_partners,
                member_photos=member_photos),
            m.handle,
        )
        (members_dir / f"{m.handle}.html").write_text(html, encoding="utf-8")

    # ── Stats page ──
    stats = []
    total_apps = 0
    for b in Branch:
        bm = [m for m in members if m.branch == b]
        if not bm:
            continue
        branch_total = 0
        for m_ in bm:
            apps = load_appearances(m_.handle)
            branch_total += len(apps)
            total_apps += len(apps)
        stats.append((b.value, {"count": len(bm), "appearances": branch_total}))
    html = _fix_links(env.get_template("stats.html").render(
        stats=stats, total_members=len(members), total_appearances=total_apps))
    (site_dir / "stats.html").write_text(html, encoding="utf-8")

    # ── Unknowns page ──
    unknowns = json.loads((data_dir / "unknowns.json").read_text(encoding="utf-8")) if (data_dir / "unknowns.json").exists() else []
    html = _fix_links(env.get_template("unknowns.html").render(unknowns=unknowns))
    (site_dir / "unknowns.html").write_text(html, encoding="utf-8")

    print(f"Site built: {site_dir}")
