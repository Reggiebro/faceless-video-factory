#!/usr/bin/env python3
"""Agent 1 — Topic Harvester.

Generates a queue of content topics from a local keyword bank (no network
required). In live mode it can optionally pull trending topics from dev.to;
in demo/offline mode it falls back to a curated list so the pipeline always
produces something.
"""
import json
import os
import sys
from datetime import datetime

WORKING_DIR = os.path.expanduser("~/faceless-video-factory")
STAGING_DIR = os.path.join(WORKING_DIR, "staging")
TRENDS_FILE = os.path.join(STAGING_DIR, "staged_topics.json")

# Curated topic bank — stands in for a live trend feed so the demo runs
# completely offline. Each entry is a seed the content agent can build on.
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


def harvest_topics(count=6):
    """Return a deterministic slice of the topic bank."""
    # Rotate through the bank based on the day so runs differ but stay stable
    day_seed = datetime.now().toordinal()
    rotated = TOPIC_BANK[day_seed % len(TOPIC_BANK):] + TOPIC_BANK[:day_seed % len(TOPIC_BANK)]
    topics = []
    for topic in rotated[:count]:
        topics.append({"topic": topic, "compiled": False})
    return topics


def save_queue(topics):
    os.makedirs(STAGING_DIR, exist_ok=True)
    with open(TRENDS_FILE, "w", encoding="utf-8") as f:
        json.dump({"topics": topics}, f, indent=4, ensure_ascii=False)


def main():
    topics = harvest_topics()
    save_queue(topics)
    print(f"[+] Harvested {len(topics)} topics into queue")
    for t in topics:
        print(f"    - {t['topic']}")


if __name__ == "__main__":
    main()
