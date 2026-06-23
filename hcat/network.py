"""Compute collab network graph data."""
from collections import defaultdict
from .storage import load_members, load_appearances
from .models import Branch


def build_graph_data():
    members = load_members()
    handle_map = {m.handle: m for m in members}
    handle_branch = {m.handle: m.branch.value for m in members}

    # Count collabs per pair
    pair_count: dict[tuple[str, str], int] = defaultdict(int)
    node_total: dict[str, int] = defaultdict(int)

    for m in members:
        apps = load_appearances(m.handle)
        seen_videos: dict[str, set[str]] = defaultdict(set)
        for a in apps:
            if a.detection_method != "holodex_collab":
                continue
            if a.channel_handle not in handle_map:
                continue
            # Avoid duplicate pairs from same video
            video_key = a.video_id
            other = a.channel_handle
            if other in seen_videos[video_key]:
                continue
            seen_videos[video_key].add(other)
            pair = tuple(sorted([m.handle, other]))
            pair_count[pair] += 1
            node_total[m.handle] += 1
            node_total[other] += 1

    # Build nodes
    branch_order = [
        Branch.EN.value, Branch.ID.value, Branch.JP.value,
        Branch.DEV_IS.value, Branch.HOLOAN.value, Branch.OFFICIAL.value,
        Branch.HOLOSTARS.value, Branch.OTHER.value,
    ]
    branch_color = {
        Branch.EN.value: "#06b6d4",
        Branch.ID.value: "#22c55e",
        Branch.JP.value: "#ec4899",
        Branch.DEV_IS.value: "#a855f7",
        Branch.HOLOAN.value: "#f59e0b",
        Branch.OFFICIAL.value: "#6b7280",
        Branch.HOLOSTARS.value: "#f97316",
        Branch.OTHER.value: "#94a3b8",
    }

    nodes = []
    node_set = set()
    for (a, b), weight in sorted(pair_count.items(), key=lambda x: -x[1]):
        for h in (a, b):
            if h not in node_set:
                node_set.add(h)
                br = handle_branch.get(h, "OTHER")
                nodes.append({
                    "id": h,
                    "group": br,
                    "collabCount": node_total.get(h, 0),
                    "color": branch_color.get(br, "#94a3b8"),
                    "sortOrder": branch_order.index(br) if br in branch_order else 99,
                })

    edges = []
    for (a, b), weight in pair_count.items():
        edges.append({
            "source": a,
            "target": b,
            "weight": weight,
        })

    nodes.sort(key=lambda n: (n["sortOrder"], -n["collabCount"], n["id"]))

    return {"nodes": nodes, "edges": edges}
