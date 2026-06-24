#!/usr/bin/env python3
"""Local full scan: all members sequentially (no 60s delay)."""
import subprocess
import sys

sys.path.insert(0, ".")
from hcat.storage import load_members
from hcat.models import Branch

start = 0
if len(sys.argv) > 1:
    start = int(sys.argv[1]) - 1

members = [
    m for m in load_members()
    if m.branch != Branch.HOLOSTARS and m.channel_id
]
total = len(members)

for idx, m in enumerate(members):
    i = idx + 1
    if i <= start:
        continue
    print(f"\n{'='*60}")
    print(f"[{i}/{total}] Scanning @{m.handle} ({m.channel_id})...")
    print(f"{'='*60}", flush=True)
    r = subprocess.run(
        ["python3", "cli.py", "scan", m.handle, "--source", "holodex", "--full"],
        capture_output=True, text=True,
    )
    if r.stdout:
        print(r.stdout.rstrip())
    if r.returncode != 0:
        print(f"  ERROR: {r.stderr.strip()[:500]}")

    print(f"  -> Refreshing timeline for @{m.handle}...", flush=True)
    r2 = subprocess.run(
        ["python3", "cli.py", "timeline", m.handle, "--full"],
        capture_output=True, text=True,
    )
    if r2.stdout:
        print(r2.stdout.rstrip())
    if r2.returncode != 0:
        print(f"  TIMELINE ERROR: {r2.stderr.strip()[:500]}")

print(f"\nAll {total} scans complete!", flush=True)
