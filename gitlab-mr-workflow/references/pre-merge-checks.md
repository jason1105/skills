# 合并前预检

> 从 SKILL.md 拆出，内容为实测口径原样搬运。触发：合并前的可合并性核验、顺序合并遇 406、批量合并摸底、堆叠 MR，及「提交推送但不合并」「继续」类推进指令。

## Pre-merge pre-check (manager-executed merges)

Before `glab mr merge`, verify the MR is still mergeable (fetch first so local refs are current):
```bash
glab api "projects/<id>/merge_requests/<iid>" | tee /tmp/mr.json
# key fields: state=opened, sha=<expected HEAD>, has_conflicts=false, draft=null
```
- `has_conflicts=false` is GitLab's own check; for a DEEP conflict check against a moved main (main advanced past the MR's base), use local merge-tree with the NEW syntax (git ≥2.38):
  `git merge-tree --write-tree --name-only origin/main origin/<branch>` → exit code 0 = clean, non-zero = conflict (conflicting paths printed). 输出重定向的文件名别用分支名——含 `/` 会建不出路径；退出码直接取 `$?`，勿隔着管道判。
  ⚠️ DO NOT use the OLD 3-arg form `git merge-tree <base> <b1> <b2> | grep -c CONFLICT` — on git 2.38+ the old form's conflict output is `<<<<<<<` markers, NOT the literal word "CONFLICT", so grep always returns 0 and the check silently passes as false-green. Verified 2026-08-19: MR !9 pre-check used the old form and reported "zero conflicts" while manifest.json + tests/manifest.test.js actually conflicted; GitLab correctly refused the merge. If you only have the old form, grep `changed in both` (git prints that line above each conflict block) or `^<<<<<<<` — never the word CONFLICT (verified 2026-09-28: `git merge-tree <mb> <tgt> <src> | grep -E "changed in both|^<<<<<<<"` correctly caught a same-file conflict GitLab reported as clean).
- **`has_conflicts` goes STALE once the target advances** (verified 2026-09-28, MR !28): GitLab computes it against the target head at MR-creation/update time; after ANOTHER MR merges into the target, the field can still read `false` while a real same-file conflict exists. Always re-run merge-tree against the CURRENT `origin/<target>`, and check the MR's cut point first: `git merge-base origin/<src> origin/<target>` — a merge-base OLDER than the target's current head means the MR was cut before later merges, so it conflicts wherever those merges touched the same files. Flag those MRs in review before anyone clicks merge.
- Review `git log --oneline origin/main..origin/<branch>` (what the MR brings) and the reverse (what main gained since) to confirm scope and no cross-MR pollution.
- **The `sha` guard on `PUT .../merge_requests/<iid>/merge` requires the FULL 40-char SHA** — an abbreviated sha is rejected (GitLab compares the literal string against the branch head), so read `sha` from the MR GET response or `git rev-parse`; never hand-type a short hash into the merge call.
- **Keep an issue OPEN through the merge → scrub closing keywords from BOTH channels before merging.** Channel 1, MR description: `Closes #N` fires on `glab mr merge` — rewrite it to a keyword-free reference (「详见议题 #N」) via the argv `PUT .../merge_requests/<iid>` form, then re-GET and grep to confirm. Channel 2, commit messages: closing keywords in commits landing on the default branch close issues too — `git log --format='%B' origin/main..origin/<branch> | grep -inE 'closes|fixes|resolves|closed|关闭'` must return empty before merging. A post-merge reopen loses the record trail; scrub pre-merge.

## Sequential merges: HTTP 406 after a prior MR lands

Merging two MRs back-to-back: after MR A merges, main advances and MR B (previously `can_be_merged`) can flip to `cannot_be_merged` — `PUT .../merge_requests/B/merge` returns **HTTP 406 "Branch cannot be merged"** and the API shows `has_conflicts: true` even though `conflicts` is null. Verified 2026-08-21: MR !18 merged at 13:13:40, then MR !19 (was `can_be_merged` minutes earlier) returned 406.

**Triage the 406 before touching the source branch**: right after a prior merge lands, the next MR's `merge_status` can still read `checking` — a stale recompute, not a conflict. Deep-check with `git merge-tree --write-tree --name-only origin/main origin/<branch>` (exit 0 = content clean); if clean, poll `GET .../merge_requests/<iid>` every few seconds until `merge_status` recomputes to `can_be_merged`, then retry the same `PUT .../merge` — it succeeds with zero source-branch changes. Only use the rebase path below when merge-tree reports real conflicts or the 406 persists after `can_be_merged`.

Recovery (the merge instruction already authorizes the merge — re-merging after conflict resolution does NOT need new approval):
```bash
git checkout <source-branch> && git fetch origin main && git merge origin/main
# resolve conflicts (keep BOTH features — it's a merge, not a choice)
npm run test   # full suite must stay green after conflict resolution
git push origin <source-branch>   # MR auto-updates to new head
glab api -X PUT "projects/<id>/merge_requests/<iid>/merge"   # retry; then verify state=merged + merged_at
```
- Conflict resolution tips: source files often auto-merge cleanly; the conflict is typically in shared test harnesses/mocks. When both branches touched the same line (e.g. a harness default `areaName='sync'` vs `'local'`), keep the newer feature's semantics PLUS the other branch's additions (`runtimeOpenOptionsCalls` etc.). Check what each side added: `git diff <base>...HEAD -- <file>` and `git diff <base>...origin/main -- <file>`.
- After merge, verify `state=merged` AND `merged_at != null` (mandatory verification still applies).

## 批量合并指令：先出方案、确认后逐条执行

用户一句「这几个 MR 都该合并了」≠ 闷头逐个合——先摸底出方案，用户确认再动：

1. **摸底**：逐条 GET MR（state／Draft 前缀／has_conflicts／sha）；`git rev-list --count origin/<branch>..origin/main` 量落后提交数；merge-tree 深检每条拿真冲突文件清单；看分支最近提交时间——仍在被推进的分支停下来向用户确认，别替活跃开发分支拍板。
2. **排序**：无冲突且非 Draft 的先合；Draft 摘前缀属合并授权的一部分；真冲突的排最后——在源分支 `git merge origin/main` 解冲突（docs 冲突按块分流见「归位/改名撞在途 MR」节）、push 后再合。
3. **逐条执行 + 逐条复核**：每合一条 API 复核 state=merged＋merged_at 再动下一条——合完 A 后 B 的冲突状态会重算（406／`checking` 语义见 Sequential merges 节）。
4. **关单核验**：描述用 `Refs #N`（非 Closes）的 MR 合并不自动关议题——re-GET 议题 state，没关就发证据 note 再 `PUT state_event=close`。

## 堆叠 MR 与推进指令纪律

**堆叠 MR（前置 MR 还开着、后续改动不能等时）**：从前置 MR 的源分支开新分支，MR 的 `target_branch` 指向该源分支而非默认分支——diff 只含后续改动，评审不夹带前置内容；描述写明「依赖：需先合并 !<base>」。开 MR 前用 `git diff --stat <base-branch>...HEAD` 自证只含自己的改动。合并顺序：先合基线 MR；GitLab 13.11 不会自动 retarget，需 `PUT .../merge_requests/<iid> -f target_branch=master` 把堆叠 MR 重指到默认分支后再合并。

**用户明确要求“提交、推送、更新评论但不要合并”时**：先用 `git status --short` 和 `git diff --name-only` 列出范围，只 `git add <目标文件>`，不要用 `git add -A`，以保留未跟踪文件原样；提交后核对 `git show --stat` 与工作树，再 `git push`。随后用 `git ls-remote origin <branch>` 和 GitLab MR GET 同时确认远端 SHA 与 MR `sha` 一致、`state=opened`、`merged_at=null`、`has_conflicts` 状态明确。长评论写入文件并通过可靠的 argv/`-F body=@file` 通道发布，立即回读 note，比较正文（允许存储层去掉末尾换行）并确认署名存在；只有用户明确授权合并时才进入合并流程。

**收到“继续”后不要把可验证事项升级成阻塞**：若修改口径已经确定，直接按既定范围完成验证、提交、推送和留痕；尚未确定的细节应标为风险并继续完成不依赖它的步骤，除非它确实改变写入内容或安全边界。这样可避免把调度判断误报成系统停止，也避免任务停在半完成状态。
