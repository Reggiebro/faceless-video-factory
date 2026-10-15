#!/usr/bin/env python3
"""Orchestrator — runs the full faceless video factory pipeline.

Phases (each is an independent agent module in agents/):
  1. Topic Harvester  -> fills the queue
  2. Script Compiler  -> topic -> voiceover script
  3. Video Assembler  -> script -> rendered vertical short
  4. Cashier Dashboard-> simulated revenue tracking

Every phase degrades gracefully: no network, no cloud LLM, no external
assets required. Run `python3 orchestrator.py` for one full pass.
"""
import os
import subprocess
import sys
from datetime import datetime

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENTS_DIR = os.path.join(AGENT_DIR, "agents")

PIPELINE = [
    ("backboard/brain.py", "Brain: recall + pick topic"),
    ("agents/agent_topic_harvester.py", "Harvest topics"),
    ("agents/agent_script_compiler.py", "Compile script"),
    ("agents/agent_video_assembler.py", "Assemble video"),
    ("agents/agent_cashier_dashboard.py", "Update cashier"),
]


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def run_agent(script, label):
    # brain.py lives in backboard/, the rest in agents/ — resolve either
    path = os.path.join(AGENT_DIR, script)
    if not os.path.exists(path):
        path = os.path.join(AGENTS_DIR, script)
    if not os.path.exists(path):
        log(f"SKIP {label}: {script} missing")
        return False
    log(f"Running {label}...")
    result = subprocess.run(
        [sys.executable, path],
        capture_output=True, text=True, timeout=240,
    )
    if result.returncode == 0:
        log(f"  {label}: OK")
        for line in result.stdout.strip().split("\n")[:4]:
            if line.strip():
                log(f"    {line}")
        return True
    log(f"  {label}: FAILED (code {result.returncode})")
    if result.stderr.strip():
        log(f"    {result.stderr.strip()[:200]}")
    return False


def main():
    log("=" * 46)
    log("FACELESS VIDEO FACTORY — PIPELINE START")
    log("=" * 46)
    ok = 0
    for script, label in PIPELINE:
        if run_agent(script, label):
            ok += 1
    log("=" * 46)
    log(f"PIPELINE COMPLETE — {ok}/{len(PIPELINE)} phases succeeded")
    log("=" * 46)


if __name__ == "__main__":
    main()
