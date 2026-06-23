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

from hcat.timeline import load_timeline_entries, extract_partner_handles, top_collab_partners, group_partners_by_branch, fuwamoco_display
from hcat.storage import load_members, load_appearances, load_unknowns, find_member
from hcat.models import Member, Branch, MemberStatus

app = FastAPI(title="HCAT - Hololive Collab Tracker")

STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

TEMPLATES = Path(__file__).parent / "templates"
TEMPLATES.mkdir(exist_ok=True)

_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(TEMPLATES)),
)
_env.globals["fuwamoco_display"] = fuwamoco_display


def _render(template_name: str, **kwargs):
    """Render template with __ROOT__ → '' and __STATIC__ → '/static' for FastAPI."""
    kwargs.setdefault("nav_active", "")
    html = _env.get_template(template_name).render(**kwargs)
    html = html.replace('__ROOT__/members/', '/member/')
    html = html.replace('href="__ROOT__/', 'href="/')
    html = html.replace('src="__ROOT__/', 'src="/')
    html = html.replace('__STATIC__/', '/static/')
    return HTMLResponse(html)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    members = load_members()
    by_branch = []
    for b in [Branch.EN, Branch.JP, Branch.ID, Branch.DEV_IS, Branch.OFFICIAL, Branch.HOLOSTARS, Branch.OTHER]:
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
    members = load_members()
    partner_groups = group_partners_by_branch(partner_handles, members)
    member_photos = {m.handle: m.photo_url for m in members if m.photo_url}
    timeline_json = json.dumps([e.to_dict() for e in timeline], ensure_ascii=False)
    partner_groups_json = json.dumps([
        (b, [{"handle": p["handle"], "name": p["name"]} for p in ps])
        for b, ps in partner_groups
    ], ensure_ascii=False)
    member_photos_json = json.dumps(member_photos, ensure_ascii=False)
    return _render("member.html",
        member=member, timeline_json=timeline_json,
        streams=streams, collabs=collabs,
        partner_count=len(partner_handles),
        partner_groups_json=partner_groups_json,
        member_photos_json=member_photos_json,
        top_partners=top_partners)


@app.get("/unknowns", response_class=HTMLResponse)
async def unknowns_page():
    unknowns = load_unknowns()
    return _render("unknowns.html", unknowns=unknowns, nav_active="unknowns")


@app.get("/stats", response_class=HTMLResponse)
async def stats_page():
    members = load_members()
    stats = []
    total_apps = 0
    for b in Branch:
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
