# 分支基线

> 从 SKILL.md 拆出，内容为实测口径原样搬运。触发：为独立议题开分支、声称合并后从 main 开分支前核对、把已验证但未提交的实现落成 MR。

## Branch isolation for an "independent follow-up" GitLab issue

When an issue is tagged as out-of-scope for a frozen parent feature branch (e.g. a badge fix separate from the gated C-line a11y work), but the implementation draft was stashed from ONTO that branch, DO NOT base the new MR on the frozen branch — even when the frozen tip's commits touch DIFFERENT files than your fix. Any MR created from the frozen branch would carry the frozen commit set into your MR diff, contaminating scope. Verified 2026-09-03 (#22 boot-badge MR): C-line `7b5698d` only touched `src/content.js`/`tests/content.test.js`, but branching off it still would have pulled those C-line commits into the #22 MR.

Correct base = `origin/main` (or current main lineage), verified these ways BEFORE opening the MR:
```bash
git fetch origin
git merge-base --is-ancestor origin/main <frozen-tip> && echo "frozen >= origin/main"
git merge-base --is-ancestor <last-change-to-your-file> origin/main && echo "your file's last touch is in main"  # file unchanged since a main commit → draft applies cleanly
git checkout -b fix/<issue>-<desc> origin/main
git stash apply stash@{0}          # applies clean because your target file's content == frozen-tip's content
git diff origin/main...HEAD --stat # MUST list ONLY the files your issue owns (e.g. "src/background.js | 13 +.., tests/.. +37") — no feature-file extras
```
After commit+push, `git diff origin/main...HEAD --stat` is the authoritative no-pollution proof; confirm local HEAD == `origin/<branch>` too. This is distinct from the GitHub mirror-divergence trap below (foreign commits absorbed via a stale local `main`); here the contaminated commits come from basing off the WRONG (feature) branch deliberately.

Also note: when a frozen feature branch's test suite differs from `origin/main`'s (the feature adds branch-local test files), `npm test` counts differ per branch. Report the accurate per-branch number and SAY it is an origin/main baseline, not a feature-branch number — a "180/180"/"178/178" figure from the C-line branch will NOT reproduce on an origin/main-based MR (there it was 173/173). Don't carry a feature-branch test count into an issue-MR report without noting the branch baseline.

## Before branching off main after a claimed merge

Confirm the merge actually landed (see verification step) AND that local main is refreshed — see also skill `gitlab-branch-baseline`.

**Mirror/fork base-divergence pollution:** when this repo is mirrored to GitHub (`remote.pushDefault=github`) and you open a GitHub PR off a LOCAL `main` that has diverged from GitHub's `main`, the PR diff silently absorbs the foreign commits (source/config/test files you never touched). ALWAYS check `gh pr view N --json files` right after opening a PR; if it lists files you didn't edit, fix with `git rebase --onto github/main main <branch>` + force-push. Full worked example: `references/pr-base-divergence-pollution.md`.

### Formalize a locally-verified-but-UNCOMMITTED final implementation (release-blocking "缺口补齐")

When real-browser verification passed but the verified code was never committed/merged (lived only as local working-tree changes), formalize it safely before it blocks a release:
1. Record the merge base (`git log -1` of the main the verified work sat on, e.g. `2bcd048`).
2. Open a NEW branch off that base (e.g. `fix/<n>-planb-merge`) and re-apply the exact working-tree file set onto it — don't commit onto a diverged branch.
3. Confirm the new branch's diff vs main EXACTLY matches the intended set BEFORE opening the MR: `git diff <base> <branch> --stat` should list only the expected files (e.g. background.js +7, content.js sendMessage, tests) with no extras.
4. Run the full test suite ON the new branch (not the old checkout), confirm green, and confirm local == `origin/<branch>`.
5. Query MRs for that source branch (`?source_branch=...&scope=all`); empty = no MR yet. Create via curl (above) with an admin-addressed description that STATES the release-blocking gap (current main is the obsolete form → publishing regresses the fix) and lists the admin decisions required before merge. Manager does NOT self-merge. glab config lives at `~/Library/Application Support/glab-cli/config.yml` on macOS (NOT `~/.config/glab-cli/`) |

## 完整案例：GitHub 镜像仓本地 main 分叉，PR 吸收外来提交


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
git merge-base --is-ancestor local-main github/main && echo "linear" || echo "DIVERGED"
git log --oneline github/main -5        # inspect what the TRUE target base actually is
git rev-list --left-right --count local-main github/main   # "0  1" etc = diverge shape
```

The PR was polluted because it was based on the local `main` (76fe029) while the PR
targeted GitHub's `main` (597ab16). The divergence commits (the #21 config.js change)
rode into the PR.

### Fix — rebase ONLY your commit(s) onto the true base

```bash
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

