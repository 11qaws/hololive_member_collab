#!/usr/bin/env python3
"""Regenerate timelines for all non-EN members using already-scanned data."""
import subprocess
import sys

sys.path.insert(0, ".")
from hcat.storage import load_members
from hcat.models import Branch

members = [
    m for m in load_members()
    if m.channel_id and m.branch not in (Branch.EN, Branch.HOLOSTARS)
]
total = len(members)

for i, m in enumerate(members):
    print(f"\n{'='*60}")
    print(f"[{i+1}/{total}] Timeline @{m.handle}...")
    print(f"{'='*60}", flush=True)
    r = subprocess.run(
        ["python3", "cli.py", "timeline", m.handle, "--full"],
        capture_output=True, text=True,
    )
    if r.stdout:
        print(r.stdout.rstrip())
    if r.returncode != 0:
        print(f"  ERROR: {r.stderr.strip()[:500]}")

print(f"\nAll {total} timelines complete!", flush=True)
