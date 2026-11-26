# 合并后清理

> 从 SKILL.md 拆出，内容为实测口径原样搬运。触发：合并落地后清理本地分支/worktree、批量清扫已合并 worktree、删除已关闭 MR 的分支。

## Post-merge cleanup (local branches + worktrees)

After verifying merges landed, clean up in this order:
```bash
git checkout main && git merge origin/main   # 检出停在特性分支/带未跟踪产物、不便切换时改用: git fetch . origin/main:main（ff-only 更新本地 main，不动工作树）
git branch --merged main | grep -E "issue-|fix-"   # candidate list
git worktree remove /path/to/worktree   # branch checked out in a worktree (git branch output shows `+` prefix = checked out in a worktree) — MUST remove worktree BEFORE deleting the branch
git branch -d <merged-branch>   # -d (not -D) refuses if not actually merged — a free safety check; use -D only when branch intentionally not merged (e.g. admin confirmed abandoned)
```
- `git branch --merged main` marks fully-merged branches; a `+` prefix in `git branch` output means the branch is checked out in a worktree — delete order is worktree first, then branch.
- **Worktree blocking branch deletion**: `git branch -d <branch>` fails with "cannot delete branch '<branch>' used by worktree at '<path>'" when the branch is checked out in a worktree. Fix: `git worktree remove <path>` first. Verified 2026-08-21: deleting `wip/i18n-manual-switch-dev` failed until worktree at `/Users/lvwei/MyProjects/lvwei/app/i18n-wip-dev` was removed.
- **Force-delete unmerged branches**: `git branch -d` refuses if branch is not fully merged to main (safety check). When admin confirms branch should be deleted anyway (e.g. abandoned feature, superseded by another implementation), use `git branch -D` to force delete. Verified 2026-08-21: `wip/i18n-manual-switch-dev` was not fully merged, required `-D` after admin confirmed deletion.
- NEVER delete branches based on another agent's claimed merge alone — `git branch -d`'s merged check plus your own `git fetch` are the proof.
- Red-line worktrees (`.acc1-min`, `.acc1-main`) stay untouched; only remove the worktrees you/your role created (`.wt-*`).
- **Bulk sweep when admin authorizes cleaning merged worktrees**: enumerate `git worktree list` and verify each non-main entry's HEAD — not its branch name, detached test worktrees carry no branch — is an ancestor of `origin/main` (`git merge-base --is-ancestor <head> origin/main` after a fresh fetch). Check dirty files first (`git -C <path> status --porcelain`) and classify them: non-code artifacts (old test logs, tool caches, evidence dirs) vs uncommitted source; archive evidence dirs to `~/.hermes/workspace/` before deleting so acceptance traces stay retrievable. Remove the verified-merged set, KEEP unmerged checkouts and report them by name (outside the authorization scope), then `git worktree prune` (drops stale metadata such as orphaned /var/folders entries) and re-list to verify.
- **Deleting a branch whose MR was CLOSED (not merged) needs the same evidence discipline** once admin authorizes it: API `state=closed` + MR sha == branch tip, and `git log --oneline origin/main..<branch>` to confirm the unique commits are superseded (no content worth keeping) — then delete in order worktree → local branch (`-d`; `-D` only if it refuses and deletion was explicitly confirmed) → `git push origin --delete <branch>`, verifying each step (dir gone, no local branch, origin reports `[deleted]`). Default stays keep-until-asked.
