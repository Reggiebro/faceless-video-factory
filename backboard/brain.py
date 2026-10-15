#!/usr/bin/env python3
"""
brain.py — the memory-aware content strategist.

This is what makes the factory more than a script runner: it closes the loop.

  BEFORE each video: recall what worked (topics, hooks, revenue) from Backboard
                     memory and let that steer topic selection.
  AFTER  each video: remember the outcome (topic, views, revenue) so the next
                     run is smarter than the last.

Backboard = long-term memory (survives across runs/sessions).
Local LLM  = the reasoning/generation that turns memory into a decision.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backboard_client as bb

WORKING_DIR = os.path.expanduser("~/faceless-video-factory")
STAGING_DIR = os.path.join(WORKING_DIR, "staging")
LEDGER_FILE = os.path.join(STAGING_DIR, "cashier_ledger.json")
BRAIN_FILE = os.path.join(STAGING_DIR, "brain_decisions.json")

TOPIC_BANK = [
    "How local AI models changed my side hustle",
    "Three tools that pay for themselves in a week",
    "Automating content without losing your voice",
    "The side hustle nobody talks about: faceless video",
    "Why I run my whole pipeline on one laptop",
    "From keyword to video in under five minutes",
    "What I learned monetizing 40 short videos",
    "Building an income stream that works while you sleep",
]


def recall_past_wins():
    """Pull everything the factory has learned so far (one broad query)."""
    facts = []
    # One broad query is enough — Backboard semantic recall returns the
    # relevant facts regardless of phrasing. Keeps the demo snappy.
    for m in bb.recall(
        "everything about which video topics, formats, hooks and revenue "
        "results worked or failed for this factory"
    ):
        facts.append(m)
    # de-dupe, preserve order
    seen, out = set(), []
    for f in facts:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def load_ledger():
    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE) as f:
            return json.load(f)
    return {"videos": 0, "total_views": 0, "total_revenue": 0.0, "history": []}


def pick_topic(memory_facts):
    """Use local LLM + recalled memory to choose the next topic from the bank."""
    mem_block = "\n".join(f"- {m}" for m in memory_facts) or "- (no past performance yet — first run)"
    candidates = "\n".join(f"{i+1}. {t}" for i, t in enumerate(TOPIC_BANK))
    prompt = f"""You are the strategist for a faceless-video side hustle. Pick the ONE
best topic to produce next.

What the factory has learned from past videos:
{mem_block}

Candidate topics:
{candidates}

Reply with ONLY the number of the best topic and a 1-sentence reason.
Format: <number> | <reason>"""
    raw = bb.generate(prompt, max_tokens=80)
    # parse leading number
    idx = 0
    for ch in raw.strip():
        if ch.isdigit():
            idx = int(ch) - 1
            break
    if not (0 <= idx < len(TOPIC_BANK)):
        idx = 0
    reason = raw.split("|", 1)[1].strip() if "|" in raw else "default pick"
    return TOPIC_BANK[idx], reason


def record_outcome(topic, views, revenue):
    """Remember the result so future runs benefit."""
    bb.remember(
        f"Video on '{topic}' earned ${revenue:.2f} from {views:,} views."
    )
    if revenue > 50:
        bb.remember(f"Topic '{topic}' is a high earner — prioritize similar content.")
    elif revenue < 5:
        bb.remember(f"Topic '{topic}' underperformed — deprioritize it.")


def log_decision(topic, reason, memory_used):
    os.makedirs(STAGING_DIR, exist_ok=True)
    entry = {"topic": topic, "reason": reason, "memory_facts_used": memory_used}
    if os.path.exists(BRAIN_FILE):
        with open(BRAIN_FILE) as f:
            hist = json.load(f)
    else:
        hist = []
    hist.append(entry)
    with open(BRAIN_FILE, "w") as f:
        json.dump(hist, f, indent=2)
    return entry


def main():
    print("[brain] Recalling past performance from Backboard memory...")
    memory_facts = recall_past_wins()
    print(f"[brain] {len(memory_facts)} fact(s) recalled:")
    for m in memory_facts:
        print(f"         - {m[:80]}")

    topic, reason = pick_topic(memory_facts)
    print(f"[brain] Next topic: {topic}")
    print(f"[brain] Reason: {reason}")
    log_decision(topic, reason, memory_facts)

    # write chosen topic for the pipeline to consume
    with open(os.path.join(STAGING_DIR, "chosen_topic.txt"), "w") as f:
        f.write(topic)
    print(f"[brain] Topic written to staging/chosen_topic.txt")


if __name__ == "__main__":
    main()
