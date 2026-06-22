"""FastAPI web UI for HCAT."""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import jinja2
import uvicorn

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from hcat.timeline import load_timeline_entries, extract_partner_handles, top_collab_partners
from hcat.storage import load_members, load_appearances, load_unknowns, find_member
from hcat.models import Member, Branch, MemberStatus

app = FastAPI(title="HCAT - Hololive Collab Tracker")

TEMPLATES = Path(__file__).parent / "templates"
TEMPLATES.mkdir(exist_ok=True)

_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(TEMPLATES)),
)


def render(name: str, **kwargs):
    t = _env.get_template(name)
    return HTMLResponse(t.render(kwargs))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    members = load_members()
    by_branch = []
    for b in [Branch.EN, Branch.JP, Branch.ID, Branch.DEV_IS, Branch.OFFICIAL, Branch.HOLOSTARS, Branch.OTHER]:
        bm = [m for m in members if m.branch == b]
        if bm:
            by_branch.append((b.value, bm))
    return render("index.html", branches=by_branch)


@app.get("/member/{handle}", response_class=HTMLResponse)
async def member_detail(handle: str):
    member = find_member(handle)
    if not member:
        return HTMLResponse("Member not found", status_code=404)
    timeline = load_timeline_entries(handle)
    streams = len([e for e in timeline if e.entry_type == "stream"])
    collabs = len([e for e in timeline if e.entry_type == "collab"])
    partner_handles = extract_partner_handles(timeline)
    top_partners = top_collab_partners(timeline)
    return render("member.html",
        member=member, timeline=timeline,
        streams=streams, collabs=collabs, partner_handles=partner_handles,
        top_partners=top_partners)


@app.get("/unknowns", response_class=HTMLResponse)
async def unknowns_page():
    unknowns = load_unknowns()
    return render("unknowns.html", unknowns=unknowns)


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
    return render("stats.html",
        stats=stats, total_members=len(members), total_appearances=total_apps)


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
