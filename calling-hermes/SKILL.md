---
name: calling-hermes
description: Use when you need to delegate a task to Hermes Agent — an OpenAI-compatible API server running on a LAN Windows machine whose tools (terminal, file read/write, web search, memory) execute ON that Windows box, not on the caller. Use to run commands / file ops on that remote Windows machine, or to get an agentic (tool-using) answer from the `hermes-agent` model. NOT for local models (use calling-opencode) — Hermes is remote + stateful-on-Windows.
---

# Calling Hermes

## Overview

Hermes Agent runs on a **LAN Windows machine** and exposes an **OpenAI Chat Completions–compatible** API (`/v1/chat/completions`). Unlike a plain LLM endpoint, every request runs a **full agent with tools** — terminal commands, file read/write, web search — and **those tools execute on the Windows machine**, not on the caller. So calling Hermes = "have an autonomous agent do something on that Windows box and report back."

Reachable directly from this Mac over the LAN. Verified 2026-10-19: `hermes-agent v0.20.0`, key auth OK.

## Step 0 — Discover the current IP (it's DHCP, do NOT hardcode)

The host IP changes with DHCP. **Always health-check first** (no key needed) to confirm the live address before doing anything else:

```bash
curl -s --max-time 8 http://192.168.2.117:8642/health
# → {"status": "ok", "platform": "hermes-agent", "version": "0.19.0"}
```

`192.168.2.117` was live on 2026-10-19; a stale doc value `192.168.2.8` had already died. If `.117` times out, ask the user for the current IP (they can run `ipconfig` on the Windows box), or scan the LAN's `:8642/health`. Port is always **8642**.

## Step 1 — Auth key

Bearer token in the request header: `Authorization: Bearer <KEY>`.

- The key is `API_SERVER_KEY` in the Windows machine's `.env`:
  `C:\Users\tsintergy\AppData\Local\Hermes Agent CN Desktop\data\hermes-home\.env`
- **You do not have the key by default — ask the user for it.** Use it transiently; do NOT write it into files, memory, or commits.
- ⚠️ The key = full command-execution power on that Windows machine (terminal + file access). Treat like a live shell credential.

Validate the key cheaply (lists models, does NOT run the agent):

```bash
curl -s -H "Authorization: Bearer <KEY>" http://192.168.2.117:8642/v1/models
# → {"data":[{"id":"hermes-agent",...}]}   200 = key OK
```

## The verified recipe (agentic call)

`model` is always `hermes-agent`. Body is standard OpenAI. **Set a long timeout (≥300s)** — the agent may run several tool calls before answering, so 30s–minutes is normal.

```python
import urllib.request, json
IP  = "192.168.2.117"   # confirm via /health first
KEY = "<KEY>"          # ask the user; do not persist
req = urllib.request.Request(
    f"http://{IP}:8642/v1/chat/completions",
    data=json.dumps({
        "model": "hermes-agent",
        "messages": [{"role": "user", "content": "在 C 盘列出当前目录并告诉我 Node 版本"}],
        "stream": False,
    }).encode("utf-8"),
    headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
)
with urllib.request.urlopen(req, timeout=300) as r:
    print(json.loads(r.read().decode("utf-8"))["choices"][0]["message"]["content"])
```

curl equivalent (UTF-8 is fine in curl by default):

```bash
curl -s --max-time 300 http://192.168.2.117:8642/v1/chat/completions \
  -H "Authorization: Bearer <KEY>" -H "Content-Type: application/json" \
  -d '{"model":"hermes-agent","messages":[{"role":"user","content":"..."}],"stream":false}'
```

## Gotchas (all real)

- **IP drifts (DHCP).** Never hardcode; `/health` first. A timeout usually means the IP moved, not that Hermes is down.
- **Tools run on Windows, not here.** "列出当前目录" lists the Windows machine's directory. Phrase tasks from that machine's point of view (paths are `C:\...`). This is the whole point — use it to act *on that Windows box*.
- **Slow is normal.** Multi-tool agent runs take tens of seconds to minutes. Set timeout ≥300s; don't retry early.
- **Side effects are real.** The agent can write files / run commands on that Windows machine. Treat a Hermes call like dispatching an autonomous agent with a live shell — scope the prompt, avoid destructive asks unless intended.
- **Chinese encoding:** send body as UTF-8 (curl OK; PowerShell 5.1 needs explicit UTF-8 bytes).
- **Endpoints:** `GET /health` (no key), `GET /v1/models` (key, no agent run), `POST /v1/chat/completions` (key, runs agent). `stream:true` gives SSE.

## Related

- Full source doc (durable reference): `/Users/lvwei/Documents/Lv-s-blog/blogs/AI/Hermes-API-Server调用文档.md`
- For a one-shot answer from a **local** model instead (no remote Windows tools), use `calling-opencode`.
- For the local autonomous OpenHands agent, use `calling-openhands`.
