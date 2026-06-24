"""Compute collab network graph data."""
from collections import defaultdict
from .storage import load_members, load_appearances
from .models import Branch


def _detect_clusters(pair_count, node_handles):
    """Detect communities using greedy modularity on weighted collab graph."""
    import networkx as nx
    from networkx.algorithms.community import greedy_modularity_communities

    G = nx.Graph()
    for h in node_handles:
        G.add_node(h)
    for (a, b), weight in pair_count.items():
        G.add_edge(a, b, weight=weight)

    communities = list(greedy_modularity_communities(G, weight="weight"))
    cluster_map = {}
    for i, comm in enumerate(communities):
        for node in comm:
            cluster_map[node] = i
    # Assign unconnected nodes to their own cluster
    next_id = len(communities)
    for h in node_handles:
        if h not in cluster_map:
            cluster_map[h] = next_id
            next_id += 1

    return cluster_map


def build_graph_data():
    members = [m for m in load_members() if m.branch != Branch.HOLOSTARS]
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

    # Detect communities
    all_handles = [m.handle for m in members]
    cluster_map = _detect_clusters(pair_count, all_handles)

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
                    "clusterId": cluster_map.get(h, 0),
                    "collabCount": node_total.get(h, 0),
                    "color": branch_color.get(br, "#94a3b8"),
                    "sortOrder": branch_order.index(br) if br in branch_order else 99,
                })
    # Add any unconnected members that never appear in pair_count
    for m in members:
        if m.handle not in node_set:
            br = handle_branch.get(m.handle, "OTHER")
            nodes.append({
                "id": m.handle,
                "group": br,
                "clusterId": cluster_map.get(m.handle, 0),
                "collabCount": 0,
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
