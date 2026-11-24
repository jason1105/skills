---
name: calling-opencode
description: Use when you need to delegate a prompt or task to a model through the local `opencode` CLI — e.g. running deepseek-v4-flash / gpt-5.6-sol / glm-5.x / claude-sonnet-5 via the tsintergy gateway, comparing models, or getting a one-shot non-interactive answer from another model without leaving Claude Code.
---

# Calling opencode

## Overview

`opencode` (v1.18.x, `/opt/homebrew/bin/opencode`) is a local coding-agent CLI. Use its **non-interactive** `run` subcommand to send a one-shot prompt to any configured model and capture the text answer. Config lives at `~/.config/opencode/opencode.json`.

## The verified recipe (one-shot answer)

```bash
opencode run -m <provider>/<model> "your prompt here"
```

Verified working (2026-08-14):
```bash
opencode run -m tsintergy-claude/deepseek-v4-flash "用一句话回答:1+1=?"
```

## Providers & models (discover, don't memorize)

```bash
opencode models            # all provider/model ids
opencode models tsintergy  # one provider
```

On this machine the tsintergy gateway (`http://new-api.saas-vpp.tsintergy.com/v1`) exposes two providers:

| provider | protocol | example models |
|---|---|---|
| `tsintergy` | OpenAI-compatible | `gpt-5.5`, `gpt-5.6-sol` |
| `tsintergy-claude` | Anthropic-compatible | `deepseek-v4-flash`, `deepseek-v4-pro`, `glm-5`/`glm-5.1`/`5.2`/`5.3`, `claude-sonnet-5`, `step-3.7-flash` |

## Gotchas (all hit in practice)

- **Provider name ≠ model lineage.** `deepseek-v4-flash` lives under `tsintergy-claude` but self-reports "由 DeepSeek 训练". The `-claude` suffix only means "goes through the Anthropic-protocol gateway", not that the weights are Claude.
- **Latency is bumpy.** A short prompt returns in seconds, but a longer/multi-part prompt once ran >2 min. For anything non-trivial, run in the **background** and read the file instead of blocking:
  ```bash
  nohup opencode run -m tsintergy-claude/deepseek-v4-flash "$(cat prompt.txt)" > /tmp/oc.out 2>&1 &
  ```
- **Output has TUI noise.** Answers are prefixed with a `> build · <model>` header and wrapped in ANSI codes. Strip before parsing:
  ```bash
  sed -E 's/\x1b\[[0-9;]*[mGKHF]//g' /tmp/oc.out
  ```
- **`timeout` doesn't exist on macOS** — don't wrap the call in it; use background + poll, or a generous foreground wait.

## Related

- To drive the heavier autonomous OpenHands agent (tools, file edits) instead of a one-shot answer, use `calling-openhands`.
