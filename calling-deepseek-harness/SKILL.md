---
name: calling-deepseek-harness
description: Use when calling DeepSeek Harness (dsh, @deepseek-ai/dsh) programmatically — running a task on a SPECIFIC provider/model, especially picking a specific tsintergy-claude model (glm-5.x / deepseek-v4-pro / claude-sonnet-5 / step-*) per call, which the dsh CLI cannot do. Covers the Python SDK entry and how to verify which model actually ran.
---

# Calling DeepSeek Harness

## Overview

DeepSeek Harness = `@deepseek-ai/dsh`, a plugin-based agent framework. A web instance runs via `dsh web` (default `http://127.0.0.1:3080`). All config lives under `$DSH_HOME` (default `~/.dsh`): `settings.yaml` + `.credentials.yaml`. Doc: https://deepseek-harness.github.io/deepseek-harness/guide/python-sdk

## ✅ Verified this session — the CLI cannot switch model per call

`dsh --profile headless "task"` runs one task and prints the result, BUT the model is pinned by `settings.yaml` → `agent-default-model`. **Both `--patch` overlay and the `DSH_MODEL` env var were overridden by settings.yaml at runtime** (proved by decoding session logs — all runs used the settings.yaml model regardless). So headless is fine only when you want the *current default* model.

**Gotcha (verified):** `settings.yaml` is shared with the live `dsh web` on :3080. Switching model in the web UI rewrites `agent-default-model`, changing what headless uses too. Don't fight a live UI session by editing it underneath.

## The direct per-model entry — Python SDK (⚠️ documented, NOT yet run here)

```python
from pathlib import Path
from deepseek_harness import DeepSeekHarness   # pip install deepseek-harness-sdk  (official; import stays deepseek_harness)

with DeepSeekHarness(
    provider="tsintergy-claude",     # explicit — bypasses settings.yaml default
    model="glm-5.3",                 # or deepseek-v4-pro / claude-sonnet-5 / step-3.7-flash ...
    max_tokens=49_152,
    cwd="/abs/workspace",
    session_root="/abs/sessions",
    cordis="<preset>/agent.cordis.yml",
) as h:
    print(h.run("your task", session_id="probe-001").final_response)
```

`provider`/`model` are constructor args → the only reliable per-call model selection.

**Install (✅ verified from official repo):** the PyPI distribution is **`deepseek-harness-sdk`** (author: DeepSeek); import module stays `deepseek_harness`. It also pulls `deepseek-harness-runtime-bin`.

> ⚠️ **Name trap (verified):** `pip install deepseek-harness` (no `-sdk`) is a **different, third-party package** — author "Henry Zhang", repo `HenryZ838978/deepseek-harness`, a thin protocol client, NOT this SDK. Installing it gets the wrong API. Always use `deepseek-harness-sdk`.

**Reaching tsintergy-claude (✅ per official `python/sdk/README.md`):** the SDK's **bundled default Cordis composition registers only `deepseek-official`**. To use a custom provider like `tsintergy-claude`, supply a **custom Cordis composition** that mounts the `llm-pi-ai` plugin with that provider's baseURL + apiKey, then pass `provider="tsintergy-claude", model="glm-5.3"`. Those creds already exist in `~/.dsh/settings.yaml` (`llm-pi-ai.providers.tsintergy-claude`, baseURL `http://new-api.saas-vpp.tsintergy.com`) + `~/.dsh/.credentials.yaml` — a custom cordis can point there. Example standalone cordis: repo `examples/jsonrpc-agent/`.

**⚠️ Not yet run end-to-end here:** the exact custom-cordis wiring for tsintergy-claude needs a first verified run before this recipe is battle-tested.

## Always verify which model ACTUALLY ran (✅ hard-won lesson)

**Never trust the model's self-ID** — this session, models under one gateway self-reported the wrong name repeatedly. Decode the session log for ground truth:

```bash
NEW=$(ls -t ~/.dsh/sessions/*/session-*/session.jsonl.zstd | head -1)
zstd -dc "$NEW" | grep -oE '"(model|provider)":\s*"[^"]*"' | sort -u
```

## tsintergy-claude models (from settings.yaml)

`claude-sonnet-5`, `deepseek-v4-flash`, `deepseek-v4-pro`, `glm-5` / `glm-5-turbo` / `glm-5.1` / `5.2` / `5.3`, `step-3.5-flash`, `step-3.7-flash`, plus multimodal `step-image-edit-2` / `stepaudio-2.5-*` (not for text headless).

## Related

- One-shot answer from the same tsintergy gateway without dsh: `calling-opencode`.
- OpenHands autonomous agent via REST: `calling-openhands`.
