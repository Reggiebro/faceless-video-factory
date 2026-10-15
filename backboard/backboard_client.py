#!/usr/bin/env python3
"""
backboard_client.py — Backboard API client (Memory + RAG + local-LLM generation).

Backboard provides two things this project uses:
  - Persistent Memory: facts saved/recalled across sessions (assistant-scoped)
  - Document RAG: upload docs, retrieve grounded context

LLM text generation is NOT covered by the hackathon free credit, so generation
runs against a local OpenAI-compatible endpoint (e.g. llama.cpp on :8080).
Backboard supplies the remembered context; the local model writes the script.

Pure stdlib — no SDK dependency, runs anywhere Python 3.8+ is installed.
"""
import json
import os
import urllib.request
import urllib.error

# ---- Configuration (env-overridable) --------------------------------------
API_KEY = os.environ.get(
    "BACKBOARD_API_KEY",
    "espr_Ky1Tj3WmDoZfKx2OO5Cf9MEzFRFK7xnaDVj6HUbyzy8",
)
BASE_URL = os.environ.get("BACKBOARD_BASE_URL", "https://app.backboard.io/api")

# Local OpenAI-compatible LLM (llama.cpp server)
LOCAL_LLM_URL = os.environ.get("LOCAL_LLM_URL", "http://127.0.0.1:8080/v1/chat/completions")
LOCAL_LLM_MODEL = os.environ.get(
    "LOCAL_LLM_MODEL",
    os.path.expanduser("~/.local/share/llama/qwen-uncensored.gguf"),
)


def _headers():
    return {"X-API-Key": API_KEY, "Content-Type": "application/json"}


def _request(method, path, payload=None, timeout=60):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers=_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300]
        raise RuntimeError(f"Backboard {method} {path} -> {e.code}: {body}")


# Cached assistant id (persisted to disk so every run reuses ONE brain)
_ASSISTANT_ID = None
_ASSISTANT_ID_FILE = os.path.expanduser("~/faceless-video-factory/staging/backboard_assistant_id")


def _load_cached_assistant():
    if os.path.exists(_ASSISTANT_ID_FILE):
        with open(_ASSISTANT_ID_FILE) as f:
            return f.read().strip() or None
    return None


def _save_assistant_id(aid):
    os.makedirs(os.path.dirname(_ASSISTANT_ID_FILE), exist_ok=True)
    with open(_ASSISTANT_ID_FILE, "w") as f:
        f.write(aid)


def get_assistant_id():
    """Return a reusable assistant id, creating one on first call.

    The id is persisted to disk so every pipeline run — and every separate
    process — talks to the SAME assistant and therefore the SAME memory.
    """
    global _ASSISTANT_ID
    if _ASSISTANT_ID:
        return _ASSISTANT_ID
    cached = _load_cached_assistant()
    if cached:
        _ASSISTANT_ID = cached
        return cached
    a = _request("POST", "/assistants", {
        "name": "Faceless Video Factory Brain",
        "system_prompt": (
            "You are the intelligence layer of an automated faceless-video "
            "side hustle. You remember which topics, formats and revenue "
            "strategies worked, and you recall them to guide future videos."
        ),
    })
    _ASSISTANT_ID = a["assistant_id"]
    _save_assistant_id(_ASSISTANT_ID)
    return _ASSISTANT_ID


# ---- Memory ----------------------------------------------------------------
def remember(fact, assistant_id=None):
    """Store a durable fact. Returns the memory operation id.

    Uses memory=Auto so Backboard extracts & persists the fact. The LLM reply
    is not covered by the free credit, but the memory write still lands.
    """
    aid = assistant_id or get_assistant_id()
    r = _request("POST", "/threads/messages", {
        "content": f"Remember this fact: {fact}",
        "assistant_id": aid,
        "memory": "Auto",
    })
    return r.get("memory_operation_id")


def recall(query, assistant_id=None):
    """Return the list of memory strings relevant to a query."""
    aid = assistant_id or get_assistant_id()
    r = _request("POST", "/threads/messages", {
        "content": query,
        "assistant_id": aid,
        "memory": "Readonly",
    })
    mems = r.get("retrieved_memories") or []
    if isinstance(mems, list):
        out = []
        for m in mems:
            if isinstance(m, dict):
                out.append(m.get("content") or m.get("memory") or str(m))
            else:
                out.append(str(m))
        return out
    return []


def list_memories(assistant_id=None):
    aid = assistant_id or get_assistant_id()
    r = _request("GET", f"/assistants/{aid}/memories")
    return [m.get("content", "") for m in r.get("memories", [])]


# ---- Documents / RAG -------------------------------------------------------
def upload_document(path, assistant_id=None):
    """Upload a file for RAG indexing. Returns the document record."""
    aid = assistant_id or get_assistant_id()
    import mimetypes
    boundary = "----bbboundary"
    filename = os.path.basename(path)
    with open(path, "rb") as f:
        file_bytes = f.read()
    ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    body = b""
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()
    body += f"Content-Type: {ctype}\r\n\r\n".encode()
    body += file_bytes + b"\r\n"
    body += f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{BASE_URL}/assistants/{aid}/documents",
        data=body,
        headers={"X-API-Key": API_KEY, "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def list_documents(assistant_id=None):
    aid = assistant_id or get_assistant_id()
    return _request("GET", f"/assistants/{aid}/documents")


# ---- Local LLM generation --------------------------------------------------
def generate(prompt, max_tokens=300, timeout=180):
    """Generate text with the local LLM. Returns string (empty on failure)."""
    payload = json.dumps({
        "model": LOCAL_LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.4,
        "stream": False,
    }).encode()
    req = urllib.request.Request(
        LOCAL_LLM_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            d = json.loads(resp.read().decode())
        return d["choices"][0]["message"]["content"].strip()
    except Exception:
        return ""


def recall_or_empty(query, assistant_id=None):
    """Safe recall that never raises — returns a newline-joined string."""
    try:
        mems = recall(query, assistant_id)
        return "\n".join(f"- {m}" for m in mems)
    except Exception:
        return ""


if __name__ == "__main__":
    # Smoke test: proves memory + generation work end to end
    aid = get_assistant_id()
    print("assistant_id:", aid)
    print("remember:", remember("The factory targets $500/month from short-form video.", aid))
    print("recall:", recall("what is the revenue target", aid))
    print("local LLM:", generate("Say 'local LLM online' and nothing else.", max_tokens=20)[:80])
