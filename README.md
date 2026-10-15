# Faceless Video Factory — an AI that remembers which content pays

A local-first pipeline that turns a single topic into a finished vertical
short-form video and tracks estimated revenue — **and learns across runs which
topics actually make money.**

Built as a demo entry for the **Hacktoberfest 2026 Open-Source AI Challenge,
Week 2: Side Hustle** (DEV).

## The idea

Most faceless-content tools are script runners: same topic list, same output,
run after run. This one closes the loop:

```
                 ┌──────────────────────────────────────────┐
                 │  Backboard persistent memory + RAG        │
                 │  (survives across runs & sessions)        │
                 └───────┬───────────────────────▲──────────┘
          recall what paid│                       │remember the outcome
                         ▼                       │
   [Brain] ──pick topic──▶ [Script] ──▶ [Assemble] ──▶ [Cashier]
    (local LLM +           (local LLM)   (FFmpeg)       (revenue sim)
     recalled facts)
```

- **Before** each video, the brain recalls what earned money from Backboard
  memory and lets that steer the next topic.
- **After** each video, the outcome (topic, views, revenue) is written back to
  memory, so the next run is smarter than the last.

## Architecture

| Layer | Component | Role |
|-------|-----------|------|
| Memory | **Backboard API** | Persistent facts + document RAG (the "remembers") |
| Reasoning | Local LLM (`llama.cpp` on `:8080`) | Turn memory into a topic decision + write scripts |
| Render | FFmpeg + espeak-ng | Vertical MP4 + narration |
| Revenue | Cashier agent | RPM + affiliate model, running ledger |

**Why the split?** Backboard's hackathon credit covers Memory + RAG (not LLM
chat), so generation runs on a local model. That's also the side-hustle point:
zero per-token cloud bill, full margin. Backboard supplies the long-term
memory that makes the factory *compound*; the local model keeps costs at zero.

## Quick start

Requirements: Python 3.8+, FFmpeg. Optional: `espeak-ng` (narration), a local
OpenAI-compatible LLM on `:8080` (scripts), a Backboard API key (memory).

```bash
# the learning demo: cold start -> seed outcomes -> warm run
bash demo.sh

# or one full pipeline pass (brain -> harvest -> script -> video -> cashier)
python3 orchestrator.py
```

Set `BACKBOARD_API_KEY` to your own key (defaults to the bundled demo key with
Memory + RAG credit).

## The learning loop, concretely

`backboard/brain.py` is the centerpiece:

1. `recall_past_wins()` — one semantic query to Backboard pulls every stored
   outcome.
2. `pick_topic()` — the local LLM reads those facts + the topic bank and picks
   the next video, with a reason.
3. `record_outcome()` — after rendering, the revenue result is remembered.

Cold start picks blind. After a couple of recorded outcomes it steers toward
the topics that paid. See `staging/brain_decisions.json` for the audit trail.

## Revenue model

The cashier simulates one video's organic traction and applies a documented
RPM + affiliate model (YouTube $0.05/1k, TikTok $0.65/1k, affiliate 2% × $15).
Numbers are simulated for the demo; the model and math are real and editable
in `agents/agent_cashier_dashboard.py`.

## License

MIT — see [LICENSE](LICENSE).
