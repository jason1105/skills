---
name: calling-openhands
description: Use when you need to drive the local OpenHands (agent-canvas) autonomous coding agent from Claude Code — dispatching a task to its deepseek-v4-flash / deepseek-v4-pro / gpt-5.6-sol agent, reading its result via the agent-server REST API, or comparing OpenHands' model against another. NOT a one-shot CLI; it runs a full agent-server stack.
---

# Calling OpenHands (agent-canvas)

## Overview

OpenHands here is the Node package `@openhands/agent-canvas` (global npm). It is **NOT** a one-shot CLI — running it starts a full stack: a Python **agent-server** (via `uvx`) + automation backend + web UI. You drive it through the agent-server **REST API**. Config lives under `~/.openhands/`.

**⚠️ It runs a `CodeActAgent` that acts autonomously** — with `run:true` it uses bash/file/browser tools, auto-runs `git init` in the workspace, and may self-commit. Treat every dispatch as a side-effecting action.

## Step 0 — Is a stack already running?

```bash
ps aux | grep -E "agent-server|agent-canvas" | grep -v grep
lsof -nP -iTCP:19000 -sTCP:LISTEN        # agent-server usually on :19000
```
The port is in the process args (`agent-server --host 127.0.0.1 --port 19000`) — **discover it, don't assume**. If nothing is running, start with `npx @openhands/agent-canvas` (heavy: uvx downloads on first run).

## Step 1 — Auth

Header `X-Session-API-Key: <key>`; key file:
```bash
KEY=$(tr -d '\n' < ~/.openhands/agent-canvas/api-key.txt)
curl -s -o /dev/null -w "%{http_code}\n" -H "X-Session-API-Key: $KEY" http://localhost:19000/api/conversations/count   # expect 200
```

## Step 2 — Discover the agent_profile_id

```bash
for f in ~/.openhands/agent-profiles/*.json; do
  python3 -c "import json;d=json.load(open('$f'));print(d['id'], d.get('llm_profile_ref'))" ; done
```
Each agent-profile references an LLM profile in `~/.openhands/profiles/<name>.json` (that file has the real `model` + `base_url`; e.g. `deepseek-v4-flash` → `deepseek/deepseek-v4-flash` @ `https://api.deepseek.com`). **IDs are machine-specific — always discover, never hardcode.**

## Step 3 — The verified recipe (create → run → read result)

```python
import json,urllib.request,time,os
KEY=open(os.path.expanduser('~/.openhands/agent-canvas/api-key.txt')).read().strip()
BASE='http://localhost:19000'; H={'X-Session-API-Key':KEY,'Content-Type':'application/json'}
PROFILE='<agent_profile_id from step 2>'
def req(m,p,b=None):
    d=json.dumps(b).encode() if b is not None else None
    return json.loads(urllib.request.urlopen(urllib.request.Request(BASE+p,data=d,headers=H,method=m),timeout=90).read())
c=req('POST','/api/conversations',{'workspace':{'working_dir':'/tmp/oh-sandbox','kind':'LocalWorkspace'},
    'agent_profile_id':PROFILE,'initial_message':{'role':'user','content':[{'type':'text','text':GOAL}],'run':True},
    'max_iterations':6})
cid=c.get('id')
while True:
    time.sleep(3)
    if req('GET','/api/conversations/'+cid).get('execution_status') in ('finished','stopped','error','paused'): break
print(req('GET','/api/conversations/'+cid+'/agent_final_response')['response'])
```

Key endpoints: `POST /api/conversations` (build+run), `GET /api/conversations/{id}` → `execution_status`, `GET /api/conversations/{id}/agent_final_response` → `{"response": "..."}`, `POST /{id}/pause` / `/interrupt` to stop it.

## Gotchas

- **Identity is masked.** The CodeActAgent persona makes the model answer "I am OpenHands / All Hands AI" and refuse its underlying model. To probe the raw model, ask it to drop the persona; to get a plain answer, tell it **"禁用任何工具、直接回复"** and set a low `max_iterations`.
- **For a raw-model answer, forbid tools** — otherwise the agent test-and-fixes with its scaffolding, which is the harness helping, not the model.
- **Sandbox the workspace.** Point `working_dir` at `/tmp/...` for tests; it will `git init` and write there.

## Safety (CLAUDE.md iron rules apply)

- Never point it at a real repo without authorization; **never let it push a default branch** — open a PR/MR instead.
- Autonomous file/bash/git = side effects → in unattended/cron runs, **stop and ask** before dispatching.

## Related

- For a lightweight one-shot answer from the *same* models (no autonomous tools), use `calling-opencode`.
