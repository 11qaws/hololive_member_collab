"""GitHub Pages static site generator."""
import json
import shutil
from pathlib import Path

import jinja2

from .config import get_data_dir
from .models import Branch, generation_sort_key
from .storage import load_members, load_appearances
from collections import defaultdict
from datetime import datetime
from .timeline import load_timeline_entries, extract_partner_handles, top_collab_partners, group_partners_by_branch, fuwamoco_display
from .network import build_graph_data
from .names import get_nickname, build_nicknames_map


def _replace_placeholders(html: str, prefix: str) -> str:
    """Replace __ROOT__ and __STATIC__ placeholders.
    prefix: '' for root-level pages, '../' for member pages.
    """
    # Do __ROOT__/ first so members/ still works
    html = html.replace('__ROOT__/', prefix)
    html = html.replace('__STATIC__/', prefix + 'static/')
    # If prefix is empty, // cleanup
    html = html.replace('"" + ', '').replace('" + "', '')
    return html


def _fix_links(html: str) -> str:
    html = _replace_placeholders(html, '')
    html = html.replace('href="/member/', 'href="members/')
    html = html.replace('href="/stats"', 'href="stats.html"')
    html = html.replace('href="/unknowns"', 'href="unknowns.html"')
    html = html.replace('href="/graph"', 'href="graph.html"')
    html = html.replace('href="/compare"', 'href="compare.html"')
    html = html.replace('href="/search"', 'href="search.html"')
    html = html.replace('href="/dashboard"', 'href="dashboard.html"')
    html = html.replace('href="/"', 'href="index.html"')
    return html


def _fix_links_member(html: str, handle: str) -> str:
    html = _replace_placeholders(html, '../')
    html = html.replace('href="/member/', 'href="members/')
    html = html.replace('href="/stats"', 'href="../stats.html"')
    html = html.replace('href="/unknowns"', 'href="../unknowns.html"')
    html = html.replace('href="/graph"', 'href="../graph.html"')
    html = html.replace('href="/compare"', 'href="../compare.html"')
    html = html.replace('href="/search"', 'href="../search.html"')
    html = html.replace('href="/dashboard"', 'href="../dashboard.html"')
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

    members = [m for m in load_members() if m.branch != Branch.HOLOSTARS]

    tmpl_dir = Path(__file__).parent.parent / "web" / "templates"
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(tmpl_dir)))
    env.globals["fuwamoco_display"] = fuwamoco_display
    env.globals["get_nickname"] = get_nickname

    member_photos = {m.handle: m.photo_url for m in members if m.photo_url}
    nicknames = build_nicknames_map(members)
    nicknames_json = json.dumps(nicknames, ensure_ascii=False)

    # ── Index page ──
    by_branch = []
    for b in [Branch.EN, Branch.JP, Branch.ID, Branch.OFFICIAL, Branch.DEV_IS, Branch.OTHER]:
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
                nicknames_json=nicknames_json,
                top_partners=top_partners, nav_active=""),
            m.handle,
        )
        (members_dir / f"{m.handle}.html").write_text(html, encoding="utf-8")

    # ── Stats page ──
    stats = []
    total_apps = 0
    for b in Branch:
        if b == Branch.HOLOSTARS:
            continue
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

    # ── Member stats data (for compare page) ──
    member_stats = []
    for m in members:
        timeline = load_timeline_entries(m.handle)
        streams = len([e for e in timeline if e.entry_type == "stream"])
        collabs = sum(len(e.sub_entries) if e.sub_entries else 1 for e in timeline if e.entry_type == "collab")
        partners = extract_partner_handles(timeline)
        top5 = top_collab_partners(timeline)[:5]
        monthly_map: dict[str, int] = defaultdict(int)
        for e in timeline:
            try:
                month = e.published_at[:7]
                monthly_map[month] += 1
            except Exception:
                pass
        monthly = sorted([{"month": k, "count": v} for k, v in monthly_map.items()], key=lambda x: x["month"])
        member_stats.append({
            "handle": m.handle,
            "name": m.name,
            "branch": m.branch.value,
            "photo": m.photo_url or "",
            "streams": streams,
            "collabs": collabs,
            "partners": len(partners),
            "topPartners": [{"handle": p[0], "count": p[1]} for p in top5],
            "monthly": monthly,
        })
    (data_out_dir / "member_stats.json").write_text(
        json.dumps(member_stats, ensure_ascii=False), encoding="utf-8")

    # ── Search index (compact, all entries) ──
    search_index = []
    for m in members:
        timeline = load_timeline_entries(m.handle)
        for e in timeline:
            partners = []
            if e.sub_entries:
                for se in e.sub_entries:
                    ph = se.get("partner_handle") if isinstance(se, dict) else getattr(se, "partner_handle", None)
                    if ph and ph not in partners:
                        partners.append(ph)
            elif e.partner_handle and e.partner_handle not in partners:
                partners.append(e.partner_handle)
            p_str = ", ".join(partners)
            if m.handle == "ladarknesss":
                p_str = ("La+, " + p_str) if p_str else "La+"
            search_index.append({
                "h": m.handle,
                "n": m.name,
                "d": e.published_at or "",
                "t": e.title or "",
                "ty": e.entry_type,
                "v": e.video_id or "",
                "p": p_str,
            })
    search_idx_path = data_out_dir / "search_index.json"
    search_idx_path.write_text(json.dumps(search_index, ensure_ascii=False), encoding="utf-8")
    search_size_mb = search_idx_path.stat().st_size / 1024 / 1024

    # ── Dashboard page ──
    html = _fix_links(env.get_template("dashboard.html").render(
        stats_json=json.dumps(member_stats, ensure_ascii=False),
        nicknames_json=nicknames_json, nav_active="dashboard"))
    (site_dir / "dashboard.html").write_text(html, encoding="utf-8")

    # ── Search page ──
    html = _fix_links(env.get_template("search.html").render(
        search_index_size=len(search_index), search_index_mb=round(search_size_mb, 1),
        nicknames_json=nicknames_json, nav_active="search"))
    (site_dir / "search.html").write_text(html, encoding="utf-8")

    # ── Compare page ──
    stats_json = json.dumps(member_stats, ensure_ascii=False)
    html = _fix_links(env.get_template("compare.html").render(
        stats_json=stats_json, nicknames_json=nicknames_json, nav_active="compare"))
    (site_dir / "compare.html").write_text(html, encoding="utf-8")

    # ── Network Graph page ──
    branch_order = [Branch.EN, Branch.JP, Branch.ID, Branch.DEV_IS, Branch.HOLOAN, Branch.OFFICIAL, Branch.OTHER]
    branch_colors = {
        Branch.EN: "#06b6d4", Branch.JP: "#ec4899", Branch.ID: "#22c55e",
        Branch.DEV_IS: "#a855f7", Branch.HOLOAN: "#f59e0b",
        Branch.OFFICIAL: "#6b7280", Branch.HOLOSTARS: "#f97316", Branch.OTHER: "#94a3b8",
    }
    branch_colors_list = [
        (b.value, branch_colors[b])
        for b in branch_order if b in branch_colors and any(m.branch == b for m in members)
    ]
    graph_data = build_graph_data()
    graph_json = json.dumps(graph_data, ensure_ascii=False)
    member_photos = {m.handle: m.photo_url for m in members if m.photo_url}
    member_photos_json = json.dumps(member_photos, ensure_ascii=False)
    html = _fix_links(env.get_template("graph.html").render(
        graph_json=graph_json, branch_colors=branch_colors_list,
        nicknames_json=nicknames_json, member_photos_json=member_photos_json,
        nav_active="graph"))
    (site_dir / "graph.html").write_text(html, encoding="utf-8")

    print(f"Site built: {site_dir}")
    print(f"  {len(members)} member pages")
    print(f"  Static files copied to {static_dir}")
