---
name: check-gitlab
description: Diagnose why cloud-agent isn't responding on a GitLab repo. Use when the user reports that @bot mentions aren't getting reviews — checks the three onboarding links (bot membership, webhook, cloud-agent secret) and reports which is broken.
---

# check-gitlab

Diagnose a GitLab repo's cloud-agent onboarding status — the three links that must all be in place for `@bot` to trigger a review.

## Step 0 — Ensure the CLI is installed and working (do this FIRST)

Before invoking `cloud-agent-check`, verify it actually runs (a broken symlink or stale install makes `which` find it but execution fail):

```bash
if command -v cloud-agent-check >/dev/null 2>&1; then
  echo "cloud-agent-check OK"
else
  echo "cloud-agent-check missing or broken — reinstalling..."
  npm install -g @tsintergy/cloud-agent-cc-plugin --registry http://npmreg.gzdevops.tsintergy.com
fi
```

If `npm install -g` fails (registry unreachable, no node, permission), surface it to the user — environment issue.

## How to use

`/check-gitlab <project_path>` (e.g. `/check-gitlab group/my-repo`). Invoke:

```bash
cloud-agent-check <project_path> [--reuse-session | --fresh-login]
```

Supports the same session flags as install-gitlab (`--reuse-session` / `--fresh-login`); asks before reusing an existing session by default.

## What it checks (three links)

1. **bot member** — is the cloud-agent bot a member (Reporter+) of the repo?
2. **webhook** — does the repo have a webhook pointing at cloud-agent's `/webhook/gitlab` with note_events on?
3. **cloud-agent** — is cloud-agent online and does it have a secret for this project?

It prints `[✓]`/`[✗]` for each. The broken link is where to focus.

## Interpreting results for the user

- **bot member ✗** → run `/install-gitlab <project_path>` (or have a Maintainer do it).
- **webhook ✗** → same; onboarding creates the webhook.
- **cloud-agent ✗** → cloud-agent service issue (down / unreachable / secret missing); this is an operator/cloud-agent-side problem, not a repo-side one.
- **all ✓ but still no review** → the onboarding is correct; the issue is in cloud-agent's review processing (model down, etc.) — check cloud-agent logs.

As with install-gitlab, the CLI may open a browser for GitLab login on first run; tell the user to log in there.
