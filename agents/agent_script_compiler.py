#!/usr/bin/env python3
"""Agent 2 — Script Compiler.

Turns a queued topic into a voiceover script. Uses a local LLM endpoint
(OpenAI-compatible, e.g. llama.cpp) when available; otherwise falls back to
a deterministic template so the demo pipeline never blocks on the model.
"""
import json
import os
import sys
import urllib.request

WORKING_DIR = os.path.expanduser("~/faceless-video-factory")
STAGING_DIR = os.path.join(WORKING_DIR, "staging")
TRENDS_FILE = os.path.join(STAGING_DIR, "staged_topics.json")

AI_URL = "http://127.0.0.1:8080/v1/chat/completions"
AI_MODEL = os.path.expanduser("~/.local/share/llama/qwen-uncensored.gguf")
AI_TIMEOUT = 45  # short — demo must not hang


def load_next_topic():
    if not os.path.exists(TRENDS_FILE):
        print(f"[-] Queue missing: {TRENDS_FILE}")
        sys.exit(1)
    with open(TRENDS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    for topic in data.get("topics", []):
        if not topic.get("compiled", False):
            return topic, data
    print("[-] All topics already compiled")
    sys.exit(0)


def ask_local_ai(prompt, max_tokens=220):
    """Query a local OpenAI-compatible endpoint. Returns None on any failure."""
    try:
        payload = json.dumps({
            "model": AI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.4,
            "stream": False,
        }).encode()
        req = urllib.request.Request(
            AI_URL, data=payload, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=AI_TIMEOUT) as resp:
            result = json.loads(resp.read())
        content = result["choices"][0]["message"]["content"].strip()
        return content or None
    except Exception:
        return None


def template_script(topic):
    """Deterministic fallback script — no model needed."""
    return (
        f"{topic}.\n\n"
        "Here's the short version. I wanted a side hustle that ran itself, "
        "so I built a pipeline that turns a single topic into a finished "
        "short video, start to finish, on one machine.\n\n"
        "The first step harvests topics and queues them. The second writes a "
        "voiceover script. The third assembles the video with a generated "
        "narration track. A dashboard tracks every view and the estimated "
        "revenue as it climbs.\n\n"
        "No cloud bills. No per-token costs. Everything runs locally, which "
        "means the margin stays where it belongs.\n\n"
        "If you've been looking for a side hustle that compounds instead of "
        "trading hours for dollars, start with the pipeline and let the "
        "dashboard show you what's working."
    )


def compile_script(topic):
    prompt = (
        f"Write a 90-120 word voiceover script for a faceless short video on: "
        f"{topic}. Conversational, first-person, no filler. Plain text only."
    )
    script = ask_local_ai(prompt)
    if script and not script.startswith("ERROR") and len(script) > 80:
        source = "local-ai"
    else:
        script = template_script(topic)
        source = "template-fallback"
    return script, source


def mark_compiled(target, data):
    target["compiled"] = True
    with open(TRENDS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def main():
    topic_item, data = load_next_topic()
    topic = topic_item["topic"]
    script, source = compile_script(topic)
    script_file = os.path.join(
        STAGING_DIR,
        "script_" + "".join(c if c.isalnum() else "_" for c in topic).lower() + ".txt",
    )
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(script)
    mark_compiled(topic_item, data)
    print(f"[+] Script for '{topic}' [{source}] -> {os.path.basename(script_file)}")
    print(f"    {len(script.split())} words")


if __name__ == "__main__":
    main()
