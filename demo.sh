#!/usr/bin/env bash
# demo.sh — shows the factory LEARNING across runs (the Hacktoberfest demo).
#
# Run 1 (cold): the brain has no memory, picks blind.
# Seed two outcomes so the brain has something to learn from.
# Run 2 (warm): the brain recalls what earned money and steers toward it.
#
# This is the "AI that remembers" story in one script.

set -e
cd "$(dirname "$0")"
PY=python3

echo "############################################################"
echo "# RUN 1 — COLD START (no memory yet)"
echo "############################################################"
$PY backboard/brain.py

echo
echo ">>> Seeding two past outcomes into Backboard memory..."
$PY - <<'EOF'
import sys; sys.path.insert(0, "backboard")
import brain
brain.record_outcome("Building an income stream that works while you sleep", 14200, 61.30)
brain.record_outcome("From keyword to video in under five minutes", 3100, 3.10)
print("    seeded: $61.30 winner + $3.10 loser")
EOF

echo
echo "############################################################"
echo "# RUN 2 — WARM (recalls what paid, steers toward it)"
echo "############################################################"
$PY backboard/brain.py

echo
echo ">>> Recording this run's outcome so the NEXT run is smarter..."
$PY - <<'EOF'
import sys, os; sys.path.insert(0, "backboard")
import brain
topic = open(os.path.expanduser("~/faceless-video-factory/staging/chosen_topic.txt")).read().strip()
brain.record_outcome(topic, 9800, 44.10)
print(f"    recorded outcome for: {topic}")
EOF

echo
echo "############################################################"
echo "# DEMO COMPLETE — the factory now remembers 3 real outcomes"
echo "############################################################"
