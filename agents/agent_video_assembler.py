#!/usr/bin/env python3
"""Agent 3 — Video Assembler.

Builds a vertical short-form video from the latest compiled script.
Generates a synthetic background locally (no external video required) and
renders narration with espeak-ng if available, otherwise produces a silent
video so the demo always completes. Uses FFmpeg for the final mux.
"""
import json
import os
import subprocess
import sys
import time

WORKING_DIR = os.path.expanduser("~/faceless-video-factory")
STAGING_DIR = os.path.join(WORKING_DIR, "staging")
AUDIO_DIR = os.path.join(WORKING_DIR, "assets", "audio")
OUTPUT_DIR = os.path.join(WORKING_DIR, "output_gallery")
TRENDS_FILE = os.path.join(STAGING_DIR, "staged_topics.json")

VIDEO_W, VIDEO_H = 1080, 1920  # 9:16 vertical


def latest_script():
    scripts = [f for f in os.listdir(STAGING_DIR) if f.startswith("script_") and f.endswith(".txt")]
    if not scripts:
        print("[-] No compiled scripts found. Run agent_script_compiler first.")
        sys.exit(1)
    scripts.sort(key=lambda x: os.path.getmtime(os.path.join(STAGING_DIR, x)), reverse=True)
    path = os.path.join(STAGING_DIR, scripts[0])
    with open(path, encoding="utf-8") as f:
        return scripts[0], f.read()


def generate_background(out_path):
    """Create a vertical gradient video locally — no download needed."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"gradients=s={VIDEO_W}x{VIDEO_H}:c0=0x1a1a2e:c1=0x0f3460:speed=0.05",
        "-t", "8",
        "-pix_fmt", "yuv420p",
        out_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def generate_narration(script, out_audio):
    """Try espeak-ng for a real narration track; return True if audio exists."""
    try:
        # espeak-ng writes WAV directly
        subprocess.run(
            ["espeak-ng", "-w", out_audio, "-s", "150", script[:600]],
            check=True, capture_output=True, timeout=60,
        )
        return os.path.exists(out_audio) and os.path.getsize(out_audio) > 1000
    except Exception:
        return False


def assemble_video(script, script_name):
    os.makedirs(AUDIO_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    base = script_name.replace("script_", "").replace(".txt", "")

    bg_path = os.path.join(AUDIO_DIR, f"bg_{base}.mp4")
    generate_background(bg_path)

    audio_path = os.path.join(AUDIO_DIR, f"narration_{base}.wav")
    has_audio = generate_narration(script, audio_path)

    timestamp = int(time.time())
    out_path = os.path.join(OUTPUT_DIR, f"final_{base}_{timestamp}.mp4")

    # Title overlay from the script's first line
    title = script.strip().split("\n")[0][:60].replace("'", "").replace(":", "")

    cmd = ["ffmpeg", "-y", "-i", bg_path]
    if has_audio:
        cmd += ["-i", audio_path]
    cmd += [
        "-vf", (
            f"drawtext=text='{title}':fontcolor=white:fontsize=64:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:box=1:boxcolor=black@0.6:boxborderw=20"
        ),
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
    ]
    if has_audio:
        cmd += ["-c:a", "aac", "-shortest"]
    cmd += [out_path]

    subprocess.run(cmd, check=True, capture_output=True)
    if not (os.path.exists(out_path) and os.path.getsize(out_path) > 0):
        raise RuntimeError("Video render produced an empty file")

    print(f"[+] Video rendered: {os.path.basename(out_path)}")
    print(f"    audio: {'yes' if has_audio else 'silent (espeak-ng not installed)'}")
    return out_path


def main():
    script_name, script = latest_script()
    assemble_video(script, script_name)


if __name__ == "__main__":
    main()
