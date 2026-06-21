#!/usr/bin/env python3
import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hcat.config import load_config, save_config, get_data_dir
from hcat.models import Member, Branch, MemberStatus
from hcat.storage import (
    load_members, save_members, load_appearances, load_unknowns,
    load_scan_state, save_scan_state,
)
from hcat.models import Branch
from hcat.scanner import scan_for_target, scan_all_unknowns, scan_for_target_via_holodex, scan_all_via_holodex
from hcat.sitegen import build_site


def cmd_scan_members(args):
    members = load_members()
    print(f"Member list: {len(members)} members")
    for b in Branch:
        branch_members = [m for m in members if m.branch == b]
        if branch_members:
            active = [m for m in branch_members if m.status == MemberStatus.ACTIVE]
            graduated = [m for m in branch_members if m.status != MemberStatus.ACTIVE]
            parts = [f"  {b.value}: {len(branch_members)} total"]
            if active:
                parts[-1] += f" ({len(active)} active"
                if graduated:
                    parts[-1] += f", {len(graduated)} graduated"
                parts[-1] += ")"
            print(parts[-1])
            for m in branch_members:
                status_tag = " [GRADUATED]" if m.status != MemberStatus.ACTIVE else ""
                print(f"    @{m.handle} — {m.name}{status_tag}")


def cmd_scan_videos(args):
    async def run():
        if args.all_members:
            branches = None
            if args.en_only:
                branches = [Branch.EN, Branch.OFFICIAL]

            kwargs = {
                "months": args.months,
                "full": args.full,
                "branches": branches,
                "verbose": True,
            }

            if args.source == "holodex":
                scope = "EN+Official" if args.en_only else "ALL members"
                mode = "FULL" if args.full else f"recent {args.months or 3}mo"
                print(f"Starting Holodex scan for ALL members [{scope}] [{mode}]")
                print()
                appearances, total_v = await scan_all_via_holodex(**kwargs)
            elif args.source == "both":
                print("--source=both not yet implemented for --all; use holodex or ytdlp")
                appearances, total_v = [], 0
            else:
                scope = "EN+Official" if args.en_only else "ALL members"
                mode = "FULL" if args.full else f"recent {args.months or 3}mo"
                print(f"Starting yt-dlp scan for ALL members [{scope}] [{mode}]")
                print("yt-dlp --all not supported; use --source holodex for all-member scans")
                appearances, total_v = [], 0

            print()
            print(f"Scan complete. {total_v} collab entries checked, {len(appearances)} new appearances.")
            return

        branches = None
        if args.en_only:
            branches = [Branch.EN, Branch.OFFICIAL]

        scope = "EN+Official" if args.en_only else "ALL channels"
        mode = "FULL" if args.full else f"recent {args.months or args.count or 3}mo"
        source_label = {"ytdlp": "yt-dlp", "holodex": "Holodex API", "both": "yt-dlp + Holodex"}.get(args.source, args.source)
        print(f"Starting scan for @{args.handle} [{scope}] [{mode}] [source: {source_label}]")
        print()

        if args.source == "holodex":
            kwargs = {
                "target_handle": args.handle,
                "months": args.months,
                "full": args.full,
                "branches": branches,
                "verbose": True,
            }
            appearances, total_v = await scan_for_target_via_holodex(**kwargs)
        elif args.source == "both":
            kwargs = {
                "target_handle": args.handle,
                "full": args.full,
                "verbose": True,
                "branches": branches,
            }
            if args.months:
                kwargs["months"] = args.months
            if args.count:
                kwargs["count"] = args.count
            apps_a, total_a = await scan_for_target_via_holodex(**{
                "target_handle": args.handle, "months": args.months,
                "full": args.full, "branches": branches, "verbose": False,
            })
            apps_b, total_b = await scan_for_target(**kwargs)
            appearances = apps_a + apps_b
            total_v = total_a + total_b
        else:
            kwargs = {
                "target_handle": args.handle,
                "full": args.full,
                "verbose": True,
                "branches": branches,
            }
            if args.months:
                kwargs["months"] = args.months
            if args.count:
                kwargs["count"] = args.count
            appearances, total_v = await scan_for_target(**kwargs)

        print()
        print(f"Scan complete. {total_v} videos checked, {len(appearances)} new appearances.")
        total = len(load_appearances(args.handle))
        print(f"Total recorded for @{args.handle}: {total}")
    asyncio.run(run())


def cmd_scan_unknowns(args):
    async def run():
        found = await scan_all_unknowns()
        print(f"\nFound {len(found)} new unknown handles")
    asyncio.run(run())


def cmd_show(args):
    handle = args.handle.lower().lstrip("@")
    apps = load_appearances(handle)
    if not apps:
        print(f"No appearances recorded for @{handle}")
        return

    print(f"Appearances for @{handle}: {len(apps)} total")
    print()

    # Group by channel
    by_channel = {}
    for a in apps:
        by_channel.setdefault(a.channel_handle, []).append(a)

    for ch, ch_apps in sorted(by_channel.items()):
        unreviewed = sum(1 for a in ch_apps if a.status == "unreviewed")
        confirmed = sum(1 for a in ch_apps if a.status == "confirmed")
        rejected = sum(1 for a in ch_apps if a.status == "rejected")
        print(f"  @{ch}: {len(ch_apps)} total ({confirmed} confirmed, {unreviewed} unreviewed, {rejected} rejected)")
        if args.detail:
            for a in ch_apps:
                status_mark = {"unreviewed": "◇", "confirmed": "✅", "rejected": "❌"}.get(a.status, "◇")
                date = a.published_at[:8] if len(a.published_at) >= 8 else "??????"
                print(f"    {status_mark} [{date}] {a.title[:70]}")
                print(f"       {a.url}")


def cmd_unknowns(args):
    unknowns = load_unknowns()
    if not unknowns:
        print("No unknown handles discovered yet")
        return
    print(f"Unknown handles: {len(unknowns)}")
    for u in unknowns:
        print(f"  @{u['handle']} (first seen: @{u['first_seen_in']})")
        if args.detail:
            print(f"    {u['video_title'][:60]}")
            print(f"    {u['video_url']}")


def cmd_config(args):
    cfg = load_config()
    if args.get:
        print(json.dumps(cfg, indent=2))
    elif args.set:
        key, value = args.set
        if value.isdigit():
            value = int(value)
        else:
            try:
                value = float(value)
            except ValueError:
                pass
        cfg[key] = value
        save_config(cfg)
        print(f"Set {key} = {value}")


def cmd_stats(args):
    members = load_members()
    total_appearances = 0

    print(f"=== Hololive Collab Tracker — Stats ===")
    print(f"Total members: {len(members)}")
    active = [m for m in members if m.status == MemberStatus.ACTIVE]
    graduated = [m for m in members if m.status != MemberStatus.ACTIVE]
    print(f"  Active: {len(active)}")
    print(f"  Graduated/Terminated: {len(graduated)}")
    print()

    for b in Branch:
        branch_members = [m for m in members if m.branch == b]
        if not branch_members:
            continue
        total = 0
        for m in branch_members:
            total += len(load_appearances(m.handle))
        total_appearances += total
        print(f"  {b.value}: {total} appearances across {len(branch_members)} members")

    print(f"\nTotal appearances recorded: {total_appearances}")
    unknowns = len(load_unknowns())
    if unknowns:
        print(f"Unknown @handles discovered: {unknowns}")


def cmd_scan_state(args):
    state = load_scan_state()
    if not state:
        print("No scan state found")
        return
    for key, channels in state.items():
        done = sum(1 for c in channels.values() if c.get("done"))
        total = len(channels)
        print(f"{key}: {done}/{total} channels complete")
        for ch, ch_state in channels.items():
            idx = ch_state.get("index", 0)
            total_v = ch_state.get("total", 0)
            done_flag = "✅" if ch_state.get("done") else "▶"
            print(f"  {done_flag} @{ch}: {idx}/{total_v}")


def cmd_build_site(args):
    print("Building static site for GitHub Pages...")
    build_site()
    print(f"Done! Site generated in {get_data_dir().parent / '_site'}")


def cmd_reset_state(args):
    confirm = input(f"Reset scan state for @{args.handle}? This cannot be undone. (y/N): ")
    if confirm.lower() == "y":
        state = load_scan_state()
        state.pop(f"scan_{args.handle.lower()}", None)
        save_scan_state(state)
        print("State reset.")


def main():
    parser = argparse.ArgumentParser(description="Hololive Cross-Appearance Tracker")
    sub = parser.add_subparsers(dest="command")

    # scan members
    p = sub.add_parser("members", help="List all members")
    p.set_defaults(func=cmd_scan_members)

    # scan videos
    p = sub.add_parser("scan", help="Scan for appearances")
    p.add_argument("handle", nargs="?", help="Target member handle (e.g. ourokronii)")
    p.add_argument("--all", dest="all_members", action="store_true", help="Scan all members (Holodex only)")
    p.add_argument("--source", choices=["ytdlp", "holodex", "both"], default="holodex", help="Data source (default: holodex)")
    p.add_argument("--full", action="store_true", help="Scan ALL videos")
    p.add_argument("--months", type=int, help="Scan recent N months (default: 3)")
    p.add_argument("--count", type=int, help="Scan last N videos per channel (yt-dlp only)")
    p.add_argument("--en-only", action="store_true", help="Only scan EN + Official channels (testing)")
    p.set_defaults(func=cmd_scan_videos)

    # scan unknowns
    p = sub.add_parser("unknowns", help="Discover unknown @handles")
    p.add_argument("--detail", action="store_true", help="Show details")
    p.set_defaults(func=cmd_unknowns)

    # show appearances
    p = sub.add_parser("show", help="Show recorded appearances")
    p.add_argument("handle", help="Member handle")
    p.add_argument("--detail", action="store_true", help="Show details")
    p.set_defaults(func=cmd_show)

    # config
    p = sub.add_parser("config", help="View/set configuration")
    p.add_argument("--get", action="store_true", help="Show config")
    p.add_argument("--set", nargs=2, metavar=("KEY", "VALUE"), help="Set config value")
    p.set_defaults(func=cmd_config)

    # stats
    p = sub.add_parser("stats", help="Show statistics")
    p.set_defaults(func=cmd_stats)

    # scan state
    p = sub.add_parser("state", help="Show scan progress")
    p.set_defaults(func=cmd_scan_state)

    # build-site
    p = sub.add_parser("build-site", help="Generate GitHub Pages site")
    p.set_defaults(func=cmd_build_site)

    # reset state
    p = sub.add_parser("reset", help="Reset scan state for a member")
    p.add_argument("handle", help="Member handle")
    p.set_defaults(func=cmd_reset_state)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
