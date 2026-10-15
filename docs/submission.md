*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)*

![Faceless Video Factory pipeline diagram](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/faceless-factory-cover.png)

# I Built a Faceless Video Factory That Remembers Which Content Actually Pays

My side hustle is faceless short-form video. The problem with every tool I tried: they're script runners. Same topic list, same output, run after run. Nothing learns. So I built one that does — **a factory that remembers what earned money and steers the next video toward it.**

## The loop nobody closes

Here's the insight that made this worth building. A faceless-content pipeline has two halves, and everyone only builds the first:

1. **Produce** a video from a topic (script → render → post)
2. **Learn** which topics paid, so the next one is better

Half 2 is where the money compounds, and it's the half everyone skips. This factory closes it with **Backboard's persistent memory**:

```
   recall what paid ──▶ [Brain] ──pick topic──▶ [Script] ──▶ [Assemble] ──▶ [Cashier]
        ▲                    (local LLM +        (local)     (FFmpeg)       (revenue)
        │                     recalled facts)
        └──────────────────── remember the outcome ───────────────┘
```

Before each video, the brain asks Backboard *"what earned money before?"* and
lets that steer the pick. After each video, the revenue result is written back
to memory. Run it twice and the second run is measurably smarter than the first.

## Why Backboard + a local model

Backboard's memory is the differentiator — facts persist across runs and
sessions, so the factory compounds instead of resetting. But its hackathon
credit covers Memory + RAG, not LLM chat. So generation runs on a **local
`llama.cpp` model** on my own machine.

That split isn't a workaround, it's the whole side-hustle thesis: **Backboard
supplies the long-term memory that makes the factory smarter; the local model
keeps the per-video cost at zero.** No cloud token bill eating the margin.

## The learning, measured

I ran the brain cold, then seeded two outcomes, then ran it warm. Here's what
changed:

| Run | Memory state | Topic picked | Why |
|-----|-------------|--------------|-----|
| 1 (cold) | 0 facts recalled | *What I learned monetizing 40 short videos* | No history — picked blind |
| 2 (warm) | 4 facts recalled | *The side hustle nobody talks about: faceless video* | Steered by the $61.30 earner in memory |

The seeded facts the brain learned from:

| Past video | Views | Revenue | Signal |
|-----------|-------|---------|--------|
| "Building an income stream that works while you sleep" | 14,200 | $61.30 | 🟢 high earner |
| "From keyword to video in under five minutes" | 3,100 | $3.10 | 🔴 underperformed |

And the rendered output it produces each run — a real 1080×1920 vertical MP4:

| Property | Value |
|----------|-------|
| Resolution | 1080×1920 (9:16) |
| Codec | h264 + aac |
| Narration | espeak-ng (on-device) |
| Background | FFmpeg gradient (generated, not downloaded) |

The revenue model behind the cashier is real math, not a mock — YouTube Shorts
RPM, TikTok Rewards RPM, and an affiliate conversion model, all documented and
editable in one file.

## What's actually local-first

The whole point of a side hustle is margin, so nothing here phones home for
the expensive parts:

- **Scripts** → local `llama.cpp` on `:8080` (falls back to a template if the
  server's down, so the pipeline never blocks)
- **Narration** → `espeak-ng` on-device
- **Background** → FFmpeg `gradients` filter, generated locally
- **Memory** → Backboard (the one cloud call, and it's the free Memory + RAG tier)

## Try it

```bash
git clone <repo> && cd faceless-video-factory
bash demo.sh        # cold start -> seed -> warm run, the learning in one script
python3 orchestrator.py   # full pass: brain -> script -> video -> cashier
```

The repo is MIT. The brain (`backboard/brain.py`) is ~150 lines and readable
end to end — recall, pick, record. That's the whole idea.

---

Has anyone else used persistent memory to make a content pipeline *compound*
rather than just repeat? I'm curious whether the recall-steers-the-pick loop
holds up at scale, or whether it starts chasing its own tail after a few dozen
runs. What would you add to the feedback signal beyond revenue?
