"""GitHub Pages static site generator."""
import json
import shutil
from pathlib import Path

import jinja2

from .config import get_data_dir
from .models import Branch, generation_sort_key
from .storage import load_members, load_appearances
from .timeline import load_timeline_entries, extract_partner_handles, top_collab_partners, group_partners_by_branch, fuwamoco_display


def _replace_placeholders(html: str, prefix: str) -> str:
    """Replace __ROOT__ and __STATIC__ placeholders.
    prefix: '' for root-level pages, '../' for member pages.
    """
    html = html.replace('__ROOT__/members/', prefix + 'members/')
    html = html.replace('href="__ROOT__/', 'href="' + prefix)
    html = html.replace('src="__ROOT__/', 'src="' + prefix)
    html = html.replace('__STATIC__/', prefix + 'static/')
    return html


def _fix_links(html: str) -> str:
    html = _replace_placeholders(html, '')
    html = html.replace('href="/member/', 'href="members/')
    html = html.replace('href="/stats"', 'href="stats.html"')
    html = html.replace('href="/unknowns"', 'href="unknowns.html"')
    html = html.replace('href="/"', 'href="index.html"')
    return html


def _fix_links_member(html: str, handle: str) -> str:
    html = _replace_placeholders(html, '../')
    html = html.replace('href="/member/', 'href="members/')
    html = html.replace('href="/stats"', 'href="../stats.html"')
    html = html.replace('href="/unknowns"', 'href="../unknowns.html"')
    html = html.replace('href="/"', 'href="../index.html"')
    return html


def build_site():
    data_dir = get_data_dir()
    site_dir = data_dir.parent  # repo root

    members_dir = site_dir / "members"
    static_dir = site_dir / "static"
    data_out_dir = site_dir / "data"
    for p in [site_dir / "index.html", site_dir / "stats.html", site_dir / "unknowns.html"]:
        if p.exists():
            p.unlink()
    if members_dir.exists():
        shutil.rmtree(members_dir)
    members_dir.mkdir(parents=True)
    data_out_dir.mkdir(parents=True, exist_ok=True)

    # Copy static files
    src_static = Path(__file__).parent.parent / "web" / "static"
    if src_static.exists():
        if static_dir.exists():
            shutil.rmtree(static_dir)
        shutil.copytree(src_static, static_dir)

    members = load_members()

    tmpl_dir = Path(__file__).parent.parent / "web" / "templates"
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(tmpl_dir)))
    env.globals["fuwamoco_display"] = fuwamoco_display

    member_photos = {m.handle: m.photo_url for m in members if m.photo_url}

    # ── Index page ──
    by_branch = []
    for b in [Branch.EN, Branch.JP, Branch.ID, Branch.OFFICIAL, Branch.DEV_IS, Branch.HOLOSTARS, Branch.OTHER]:
        bm = [m for m in members if m.branch == b]
        if bm:
            bm.sort(key=generation_sort_key)
            by_branch.append((b.value, bm))
    html = _fix_links(env.get_template("index.html").render(branches=by_branch, nav_active="members"))
    (site_dir / "index.html").write_text(html, encoding="utf-8")

    # ── Member pages ──
    for m in members:
        timeline = load_timeline_entries(m.handle)
        streams = len([e for e in timeline if e.entry_type == "stream"])
        collabs = sum(len(e.sub_entries) if e.sub_entries else 1 for e in timeline if e.entry_type == "collab")
        partner_handles = extract_partner_handles(timeline)
        partner_groups = group_partners_by_branch(partner_handles, members)
        top_partners = top_collab_partners(timeline)
        timeline_json = json.dumps([e.to_dict() for e in timeline], ensure_ascii=False)
        partner_groups_json = json.dumps([
            (b, [{"handle": p["handle"], "name": p["name"]} for p in ps])
            for b, ps in partner_groups
        ], ensure_ascii=False)
        member_photos_json = json.dumps(member_photos, ensure_ascii=False)
        html = _fix_links_member(
            env.get_template("member.html").render(
                member=m, timeline_json=timeline_json,
                streams=streams, collabs=collabs,
                partner_count=len(partner_handles),
                partner_groups_json=partner_groups_json,
                member_photos_json=member_photos_json,
                top_partners=top_partners, nav_active=""),
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
        stats=stats, total_members=len(members), total_appearances=total_apps,
        nav_active="stats"))
    (site_dir / "stats.html").write_text(html, encoding="utf-8")

    # ── Unknowns page ──
    unknowns = json.loads((data_dir / "unknowns.json").read_text(encoding="utf-8")) if (data_dir / "unknowns.json").exists() else []
    html = _fix_links(env.get_template("unknowns.html").render(
        unknowns=unknowns, nav_active="unknowns"))
    (site_dir / "unknowns.html").write_text(html, encoding="utf-8")

    print(f"Site built: {site_dir}")
    print(f"  {len(members)} member pages")
    print(f"  Static files copied to {static_dir}")
