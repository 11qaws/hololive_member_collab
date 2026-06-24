#!/usr/bin/env python3
"""GHA wrapper: scan all members one per minute via Holodex."""
import subprocess
import sys
import time

sys.path.insert(0, ".")
from hcat.storage import load_members
from hcat.models import Branch

members = [
    m for m in load_members()
    if m.branch != Branch.HOLOSTARS and m.channel_id
]
total = len(members)

for i, m in enumerate(members):
    print(f"[{i+1}/{total}] Scanning @{m.handle} ({m.channel_id})...", flush=True)
    r = subprocess.run(
        ["python3", "cli.py", "scan", m.handle, "--source", "holodex", "--full"],
        capture_output=True,
        text=True,
    )
    if r.stdout:
        print(r.stdout.rstrip())
    if r.returncode != 0:
        print(f"  ERROR: {r.stderr.strip()[:300]}", flush=True)
    if i < total - 1:
        print("  sleep 60s...", flush=True)
        time.sleep(60)

print("All scans complete.", flush=True)
