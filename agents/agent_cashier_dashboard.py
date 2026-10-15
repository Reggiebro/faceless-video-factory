#!/usr/bin/env python3
"""Agent 4 — Cashier Dashboard.

Tracks videos produced and estimates revenue from view-based RPM and an
affiliate conversion model. Persists a running ledger and prints a scannable
terminal table. All numbers are simulated for the demo (no live platform
API), but the model and math are real and documented.
"""
import json
import os
import random
import sys
from datetime import datetime

WORKING_DIR = os.path.expanduser("~/faceless-video-factory")
STAGING_DIR = os.path.join(WORKING_DIR, "staging")
LEDGER_FILE = os.path.join(STAGING_DIR, "cashier_ledger.json")

# Revenue model constants (per 1,000 views / per conversion)
YOUTUBE_SHORTS_RPM = 0.05
TIKTOK_REWARDS_RPM = 0.65
AFFILIATE_CONVERSION = 0.02
AFFILIATE_VALUE = 15.00


def load_ledger():
    if not os.path.exists(LEDGER_FILE):
        return {"videos": 0, "total_views": 0, "total_revenue": 0.0, "history": []}
    with open(LEDGER_FILE) as f:
        return json.load(f)


def save_ledger(ledger):
    with open(LEDGER_FILE, "w") as f:
        json.dump(ledger, f, indent=4)


def simulate_cycle():
    """Simulate one video's organic traction across platforms."""
    yt_views = random.randint(1200, 8500)
    tt_views = random.randint(2500, 15000)
    yt_payout = (yt_views / 1000) * YOUTUBE_SHORTS_RPM
    tt_payout = (tt_views / 1000) * TIKTOK_REWARDS_RPM
    combined = yt_views + tt_views
    affiliate = (combined * 0.05 * AFFILIATE_CONVERSION) * AFFILIATE_VALUE
    cycle_revenue = yt_payout + tt_payout + affiliate
    return {
        "yt_views": yt_views,
        "tt_views": tt_views,
        "combined_views": combined,
        "yt_payout": round(yt_payout, 4),
        "tt_payout": round(tt_payout, 4),
        "affiliate": round(affiliate, 4),
        "cycle_revenue": round(cycle_revenue, 4),
        "timestamp": datetime.now().isoformat(),
    }


def render_dashboard(ledger, cycle):
    w = 52
    print()
    print("=" * w)
    print("   FACELESS VIDEO FACTORY — CASHIER DASHBOARD".center(w))
    print("=" * w)
    print(f" Videos produced      : {ledger['videos']}")
    print(f" This cycle views     : {cycle['combined_views']:,}")
    print(f"   YouTube / TikTok   : {cycle['yt_views']:,} / {cycle['tt_views']:,}")
    print(f" This cycle revenue   : ${cycle['cycle_revenue']:.2f}")
    print(f"   YT / TT / affili.  : ${cycle['yt_payout']:.2f} / ${cycle['tt_payout']:.2f} / ${cycle['affiliate']:.2f}")
    print("-" * w)
    print(f" Lifetime views       : {ledger['total_views']:,}")
    print(f" LIFETIME REVENUE     : ${ledger['total_revenue']:.2f} USD")
    print(f" Revenue per video    : ${ledger['total_revenue']/ledger['videos']:.2f}" if ledger['videos'] else "")
    print("=" * w)
    print()


def main():
    ledger = load_ledger()
    cycle = simulate_cycle()
    ledger["videos"] += 1
    ledger["total_views"] += cycle["combined_views"]
    ledger["total_revenue"] = round(ledger["total_revenue"] + cycle["cycle_revenue"], 4)
    ledger["history"].append(cycle)
    save_ledger(ledger)
    render_dashboard(ledger, cycle)


if __name__ == "__main__":
    main()
