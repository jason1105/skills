# PR branch base-divergence pollution (fork + mirror setup)

## When this bites

Repo is mirror-duplicated across **two remotes** — GitLab `origin` (production, backed by
`git.tsintergy.com:8070`) and GitHub `github` (mirror, with `remote.pushDefault=github`).
A single local `main` can be **ahead of** one remote's `main` (or the two `main`s simply
diverge at an earlier commit).

If you branch off the LOCAL `main` and push to a remote whose `main` is at a DIFFERENT
commit, the resulting PR diff **silently absorbs the commits your local `main` has that
the remote `main` lacks** — source/config/test files you never touched appear in the diff.

## Worked example (verified 2026-09-02, README PR #4 on chrome-show-issue-and-mr-no)

Symptom: opened a README-only PR, but `gh pr view N --json files` listed
`src/config.js`, `tests/config.test.js`, `tests/content.test.js` alongside README.md —
files I never edited.

### Diagnose the divergence

```bash
# local main vs the target remote's main
git merge-base --is-ancestor local-main github/main && echo "linear" || echo "DIVERGED"
git log --oneline github/main -5        # inspect what the TRUE target base actually is
# In this project: local main = 76fe029 (has #21 full-repo / config.js),
#   github/main     = 597ab16 (has PRIVACY.md, != local main) → DIVERGED at afc9370
git rev-list --left-right --count local-main github/main   # "0  1" etc = diverge shape
```

The PR was polluted because it was based on the local `main` (76fe029) while the PR
targeted GitHub's `main` (597ab16). The divergence commits (the #21 config.js change)
rode into the PR.

### Fix — rebase ONLY your commit(s) onto the true base

```bash
# SYNTAX: git rebase --onto <new-base> <old-base-that-carried-the-foreign-commits> <branch>
git rebase --onto github/main main feature/readme-bilingual
```

`--onto` re-plays the branch's own commits directly onto `<new-base>` (GitHub's true
`main`), discarding everything between `<old-base>` (local main) and the branch — i.e. it
drops the foreign #21 config.js commits and keeps only the README commit.

### Verify clean, then force-push

A PR is a moving ref — the commit SHA changes after rebasing, so a normal push is
rejected; force-push is required (the PR stays open, it just updates its head):

```bash
git diff github/main..feature/readme-bilingual --stat   # MUST list ONLY your files
git push --force-with-lease github feature/readme-bilingual
gh pr view 4 --json files    # confirm only README + screenshots remain
```

Result: PR went from 9 files (6 intended + 3 polluted) to the exact 6 intended files.

## Key rules

1. **ALWAYS check `gh pr view N --json files` right after opening a PR.** If it lists
   files you didn't edit, the PR is polluted — do NOT merge it, fix it first.
2. The fix is `rebase --onto`, NOT `git rebase <remote>/main <branch>` (the plain form
   replays foreign commits too). `--onto` is what lets you drop the divergent history.
3. `<new-base>` = the **target remote's actual current main**, not your local main.
4. After rebase, verify the diff (steps above) before force-pushing; then re-read the PR
   files list to confirm.
5. This bites specifically in mirror/fork setups with `remote.pushDefault` pointing away
   from the PR target — keep local `main` in sync with the remote you're going to PR
   against before branching.

## Cross-reference

- `gitlab-mr-workflow` SKILL.md — the local `main`/`git tsintergy`/GitHub mirror topology
  for chrome-show-issue-and-mr-no, and the general "verify before claiming done" rule that
  applies equally to PR cleanliness.
