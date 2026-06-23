"""FastAPI web UI for HCAT."""
import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import jinja2
import uvicorn

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from collections import defaultdict
from hcat.timeline import load_timeline_entries, extract_partner_handles, top_collab_partners, group_partners_by_branch, fuwamoco_display
from hcat.storage import load_members, load_appearances, load_unknowns, find_member
from hcat.models import Member, Branch, MemberStatus
from hcat.network import build_graph_data
from hcat.names import get_nickname, build_nicknames_map

app = FastAPI(title="HCAT - Hololive Collab Tracker")

STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")

TEMPLATES = Path(__file__).parent / "templates"
TEMPLATES.mkdir(exist_ok=True)

_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(TEMPLATES)),
)
_env.globals["fuwamoco_display"] = fuwamoco_display
_env.globals["get_nickname"] = get_nickname


def _render(template_name: str, **kwargs):
    """Render template with __ROOT__ → '' and __STATIC__ → '/static' for FastAPI."""
    kwargs.setdefault("nav_active", "")
    html = _env.get_template(template_name).render(**kwargs)
    html = html.replace('__ROOT__/members/', '/member/')
    html = html.replace('href="__ROOT__/', 'href="/')
    html = html.replace('src="__ROOT__/', 'src="/')
    html = html.replace('__STATIC__/', '/static/')
    return HTMLResponse(html)


def _load_members_filtered():
    return [m for m in load_members() if m.branch != Branch.HOLOSTARS]

def _build_member_stats(members: list):
    stats = []
    for m in members:
        timeline = load_timeline_entries(m.handle)
        streams = len([e for e in timeline if e.entry_type == "stream"])
        collabs = sum(len(e.sub_entries) if e.sub_entries else 1 for e in timeline if e.entry_type == "collab")
        partners = extract_partner_handles(timeline)
        top5 = top_collab_partners(timeline)[:5]
        monthly_map: dict[str, int] = defaultdict(int)
        for e in timeline:
            try:
                monthly_map[e.published_at[:7]] += 1
            except Exception:
                pass
        monthly = sorted([{"month": k, "count": v} for k, v in monthly_map.items()], key=lambda x: x["month"])
        stats.append({
            "handle": m.handle, "name": m.name, "branch": m.branch.value,
            "photo": m.photo_url or "", "streams": streams, "collabs": collabs,
            "partners": len(partners),
            "topPartners": [{"handle": p[0], "count": p[1]} for p in top5],
            "monthly": monthly,
        })
    return stats


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    members = _load_members_filtered()
    by_branch = []
    for b in [Branch.EN, Branch.JP, Branch.ID, Branch.DEV_IS, Branch.OFFICIAL, Branch.OTHER]:
        bm = [m for m in members if m.branch == b]
        if bm:
            by_branch.append((b.value, bm))
    return _render("index.html", branches=by_branch, nav_active="members")


@app.get("/member/{handle}", response_class=HTMLResponse)
async def member_detail(handle: str):
    member = find_member(handle)
    if not member:
        return HTMLResponse("Member not found", status_code=404)
    timeline = load_timeline_entries(handle)
    streams = len([e for e in timeline if e.entry_type == "stream"])
    collabs = sum(len(e.sub_entries) if e.sub_entries else 1 for e in timeline if e.entry_type == "collab")
    partner_handles = extract_partner_handles(timeline)
    top_partners = top_collab_partners(timeline)
    members = _load_members_filtered()
    partner_groups = group_partners_by_branch(partner_handles, members)
    member_photos = {m.handle: m.photo_url for m in members if m.photo_url}
    nicknames = build_nicknames_map(members)
    timeline_json = json.dumps([e.to_dict() for e in timeline], ensure_ascii=False)
    partner_groups_json = json.dumps([
        (b, [{"handle": p["handle"], "name": p["name"]} for p in ps])
        for b, ps in partner_groups
    ], ensure_ascii=False)
    member_photos_json = json.dumps(member_photos, ensure_ascii=False)
    nicknames_json = json.dumps(nicknames, ensure_ascii=False)
    return _render("member.html",
        member=member, timeline_json=timeline_json,
        streams=streams, collabs=collabs,
        partner_count=len(partner_handles),
        partner_groups_json=partner_groups_json,
        member_photos_json=member_photos_json,
        nicknames_json=nicknames_json,
        top_partners=top_partners)


@app.get("/unknowns", response_class=HTMLResponse)
async def unknowns_page():
    unknowns = load_unknowns()
    return _render("unknowns.html", unknowns=unknowns, nav_active="unknowns")


@app.get("/dashboard", response_class=HTMLResponse)
@app.get("/dashboard.html", response_class=HTMLResponse)
async def dashboard_page():
    members = _load_members_filtered()
    nicknames = build_nicknames_map(members)
    member_stats = _build_member_stats(members)
    stats_json = json.dumps(member_stats, ensure_ascii=False)
    nicknames_json = json.dumps(nicknames, ensure_ascii=False)
    return _render("dashboard.html", stats_json=stats_json, nicknames_json=nicknames_json, nav_active="dashboard")


@app.get("/search", response_class=HTMLResponse)
@app.get("/search.html", response_class=HTMLResponse)
async def search_page():
    members = _load_members_filtered()
    nicknames = build_nicknames_map(members)
    nicknames_json = json.dumps(nicknames, ensure_ascii=False)
    return _render("search.html", search_index_size=0, search_index_mb=0, nicknames_json=nicknames_json, nav_active="search")

@app.get("/compare", response_class=HTMLResponse)
@app.get("/compare.html", response_class=HTMLResponse)
async def compare_page():
    members = _load_members_filtered()
    nicknames = build_nicknames_map(members)
    member_stats = _build_member_stats(members)
    stats_json = json.dumps(member_stats, ensure_ascii=False)
    nicknames_json = json.dumps(nicknames, ensure_ascii=False)
    return _render("compare.html", stats_json=stats_json, nicknames_json=nicknames_json, nav_active="compare")


@app.get("/graph", response_class=HTMLResponse)
@app.get("/graph.html", response_class=HTMLResponse)
async def graph_page():
    members = _load_members_filtered()
    branch_order = [Branch.EN, Branch.JP, Branch.ID, Branch.DEV_IS, Branch.HOLOAN, Branch.OFFICIAL, Branch.OTHER]
    branch_colors_map = {
        Branch.EN: "#06b6d4", Branch.JP: "#ec4899", Branch.ID: "#22c55e",
        Branch.DEV_IS: "#a855f7", Branch.HOLOAN: "#f59e0b",
        Branch.OFFICIAL: "#6b7280", Branch.OTHER: "#94a3b8",
    }
    branch_colors = [
        (b.value, branch_colors_map[b])
        for b in branch_order if b in branch_colors_map and any(m.branch == b for m in members)
    ]
    nicknames = build_nicknames_map(members)
    nicknames_json = json.dumps(nicknames, ensure_ascii=False)
    graph_data = build_graph_data()
    graph_json = json.dumps(graph_data, ensure_ascii=False)
    return _render("graph.html", graph_json=graph_json, branch_colors=branch_colors, nicknames_json=nicknames_json, nav_active="graph")


@app.get("/stats", response_class=HTMLResponse)
async def stats_page():
    members = _load_members_filtered()
    stats = []
    total_apps = 0
    for b in Branch:
        if b == Branch.HOLOSTARS:
            continue
        bm = [m for m in members if m.branch == b]
        if not bm:
            continue
        branch_total = 0
        for m in bm:
            apps = load_appearances(m.handle)
            branch_total += len(apps)
            total_apps += len(apps)
        stats.append((b.value, {"count": len(bm), "appearances": branch_total}))
    return _render("stats.html",
        stats=stats, total_members=len(members), total_appearances=total_apps,
        nav_active="stats")


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
