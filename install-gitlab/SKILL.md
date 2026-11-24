---
name: install-gitlab
description: Onboard a GitLab repo to cloud-agent (AI code-review bot). Use when the user wants to enable cloud-agent review on a GitLab project — adds the bot as a member, creates the webhook, and registers the secret, all in one command with zero token operations for the user.
---

# install-gitlab

Onboard a GitLab repository to cloud-agent so that `@bot` mentions in that repo's MRs/Issues trigger AI code review.

## Step 0 — Ensure the CLI is installed and working (do this FIRST)

The skill drives a CLI binary `cloud-agent-install`. Before invoking it, **verify it actually runs** — not just that the command name exists (a broken symlink or stale install will make `which` find it but execution fail). Run this self-check, and if it fails, **reinstall automatically**:

```bash
# Try to actually run it (with no args it prompts for a repo — we just check it boots).
# Use `--help`-style smoke: a working install prints the repo-inference prompt or help;
# a broken/missing install errors with "command not found" or a node module error.
if ! echo | cloud-agent-install 2>&1 | head -1 | grep -qiE "command not found|Cannot find module|Error:"; then
  echo "cloud-agent-install OK"
else
  echo "cloud-agent-install missing or broken — reinstalling..."
  npm install -g @tsintergy/cloud-agent-cc-plugin --registry http://npmreg.gzdevops.tsintergy.com
fi
```

Notes:
- The package is `@tsintergy/cloud-agent-cc-plugin` on the private registry `http://npmreg.gzdevops.tsintergy.com` (the `@tsintergy` scope must resolve to this registry — the install command passes `--registry` explicitly to be safe).
- Reinstall is idempotent and fixes the common failure modes: never installed, or installed via `npm link` that later broke (e.g. the linked source moved/was deleted).
- If `npm install -g` itself fails (registry unreachable, no node, permission denied), surface that to the user — it's an environment issue you can't fix from here.

## How to use

The user runs `/install-gitlab <project_path>` (e.g. `/install-gitlab group/my-repo`). After Step 0 confirms the CLI works, invoke it:

```bash
cloud-agent-install [project_path] [--reuse-session | --fresh-login]
```

If no project_path is given, it infers from the current directory's git remote and asks the user to confirm.

**Session reuse (登录态):**
- If a previous login session exists, the CLI **asks** whether to reuse it (回车=reuse, n=fresh login).
- `--reuse-session` → reuse without asking.
- `--fresh-login` → discard saved session, force a fresh browser login (for switching accounts / stale session).
- To clear the session entirely, use `/logout-gitlab`.

## What the CLI does (so you can guide the user)

1. **First-time only**: the CLI opens a browser window to the GitLab login page. **The user must log in there themselves** (their password goes to the official GitLab page, never to the CLI). Tell the user: "a browser window opened — please log in to GitLab in it, then the CLI continues automatically." The session is saved for reuse, so subsequent runs need no login.
2. The CLI then adds the cloud-agent bot as a Reporter member of the repo, creates the webhook (note_events), and hands the secret to cloud-agent — all automatically.
3. On success it prints a completion message; on failure it rolls back and reports the exact failing step.

## If it fails

Common failures and what to tell the user:
- **"你不是 ... 的 Maintainer"** — the user lacks Maintainer on the repo; they need the repo Owner to run it, or to get Maintainer permission.
- **Login timeout** — the user didn't log in within 5 min; re-run.
- **"CLOUD_AGENT_URL 未配置" / "ADMIN_TOKEN 未配置" / "CC_BOT_USER_ID 未配置"** — the CLI's pre-set config is missing; this is an operator setup issue, point them to the operator.

Do NOT attempt to fix these by editing config or tokens yourself — surface them to the user.

## After success

Tell the user: "Done. In `<project_path>`, comment `@bot review` on any MR/Issue to trigger a code review."
