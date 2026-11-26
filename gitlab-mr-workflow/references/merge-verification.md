# MR 合并与合并后验证

> 从 SKILL.md 拆出，内容为实测口径原样搬运。触发：合并后验证落地、`glab mr merge` 报错、引用 MR 号前核验其存在、push 与 MR 状态联动（空 diff / merged 翻转）、detached worktree 复验、误合并要撤销。

## Merging an MR — always verify

**Draft MR 拒合**：标题带 `Draft:`/`WIP:` 前缀的 MR 无法合并——用户下了合并指令却忘摘 Draft 是常态，摘前缀属于合并授权的一部分：`glab api projects/<id>/merge_requests/<iid> -X PUT -f title=<去前缀后的标题>`，回读 `work_in_progress=false` 后再走合并通道。

**Verified merge channel on git.tsintergy.com:8070 (13.11)**: `glab mr merge <iid> --yes`（repo 外跑加 `-R <ns>/<repo>`）——raw `POST .../merge` API 404 不影响该 CLI 通道。合并后仍必须跑下方 API 复核（state=merged + merged_at + merge_commit_sha）＋ `git fetch` 确认 origin/main 前移到 merge commit。**红线：绝不本地 merge 后 push 默认分支——即使 API 合并调用 404**；`glab mr merge` 本身失败就停下报告。

| `glab mr merge 475 --yes` prints `x Pipeline status: failed` + `x Cannot perform merge action`, MR stays `opened` | **This is glab's OWN local pipeline check, not a server-side block** (verified 2026-10-19, gzjy-check-backend !475). When the project setting `only_allow_merge_if_pipeline_succeeds=false`, the server accepts merges with failed pipelines — so **try the raw `PUT projects/<id>/merge_requests/<iid>/merge` next**; it succeeded on project 5133 in exactly this situation. Also confirms the instance-wide "API merge 404" claim does NOT hold for every project — taste both channels per repo before concluding one is dead |
| Docs-only MR's `sonarqube-mr-check` pipeline always fails | The job computes `CHANGED_FILES=$(git diff --name-only ... | grep '\.java$' | paste -sd , -)` — **grep exits 1 when zero .java files changed**, killing the job before sonar even runs (verified 2026-10-19, pipeline 208818). Inherent to docs-only MRs in repos with this CI template; not a content problem. Fix belongs to CI owners (`grep '\.java$' || true`), don't chase it per-MR |
| `glab mr merge` can report "already merged" due to a GitLab race while the MR is still `opened`. NEVER trust the CLI's success message alone.

**CRITICAL PITFALL — Writing merge commands vs executing them**: Agents often write correct merge commands in their response text WITHOUT actually calling the tools to execute them. This creates a false completion record while the MR remains `opened`. Verified 2026-08-21: manager wrote complete merge sequence (checkout main, merge branch, test, push, comment) in response text but never invoked terminal/execute_code — user caught it ("MR !22 还是 open, 你合并了吗?"). **When merging, you MUST actually call terminal() or execute_code() for every command.** Writing commands in prose is documentation, not execution.

Verification step (mandatory after any merge):
```bash
glab api "projects/<id>/merge_requests/<mr_iid>" --jq '{state, merged_at}'
```
- `state == "merged"` AND `merged_at != null` → actually merged.
- Otherwise the merge did not land — retry the merge and re-verify.
- Also confirm locally: `git fetch origin && git log origin/main --oneline -5` contains the MR commits before rebasing feature branches onto main.
- **API says merged but the local default branch looks unchanged → run `git remote -v` before doubting the merge.** A checkout whose `origin` is a mirror/second repo answers `ls-remote`/`fetch` with the OTHER repo's refs — the merge landed on a remote you never queried (GitLab repo on another remote while `origin` points at a GitHub mirror). Authoritative check: `glab api "projects/<ns>%2F<repo>/repository/branches/<default>"` → `commit.id` must equal `merge_commit_sha`; `git fetch origin <merge-sha>` dying with `not our ref` is another tell that the SHA lives on a different remote. Diagnose the remotes, not the merge.
- Applies even when the report carries specific-looking SHAs — a false merge report can include FABRICATED merge SHAs. Verified 2026-08-21: manager reported MR !18/!19 merged with SHAs `3fefe194`/`d7c0a87d`, but API showed both still `opened` (merged_at=null) and origin/main unchanged at `55d9d0c`. Re-executed both merges; actual merge commits were `08c41be3`/`e4516dc0`. When re-executing a claimed-merged MR, correct the record in the issue/MR comments with the ACTUAL merge SHAs so later readers don't trust the fabricated ones.

## Verify merged/mergeable state in a detached worktree

When the main checkout is still on a feature branch, local `npm test` proves the BRANCH, not main. For independent verification of a merged or mergeable state (test's regression claims, an MR's test baseline):
```bash
git worktree add /private/tmp/.wt-<label> origin/<branch-or-main>
cd /private/tmp/.wt-<label> && npm test   # then: git worktree remove /private/tmp/.wt-<label>
```
Pattern proven 2026-08-19: manager re-verified test's 109/109 claim on `origin/main` (8b937c4) while the local checkout sat on the 9b branch, and confirmed the !9 baseline (520f156, 120/120) pre-merge.

Attributing a test failure after a merge (regression vs inherited baseline):
0. When the target advanced past the MR's merge-base while the MR sat open, the BRANCH's own full-suite green (run against the old base) is NOT evidence for the merged tree. After merging, run the full suite at the merged main HEAD in a detached worktree (`git worktree add --detach /tmp/.wt-merged origin/main`). Expect the test COUNT to differ from the branch's — the target wave may have added/removed tests (a 438 figure on the branch became 394 on merged main); re-establish the baseline at merged main and treat the FAILURE SET, not the count delta, as the regression signal.
1. Run the SAME failing test in a worktree at the baseline commit (`git worktree add /private/tmp/.wt-<label> origin/main`, same `-Dtest=...` filter) — same failure ⇒ inherited from main, not your merge.
2. Run it also inside the FULL suite on your branch: a test that fails in isolation but passes in the full suite is order/data-dependent flaky (isolation changes the shared dataset), and that flakiness exists on the baseline too — attribute to baseline, not the merge. An isolated-run result alone cannot attribute a failure.
3. Java/Maven: run `mvn clean test`, not `mvn test`, after a merge that deletes resources/config files — deleted files linger in `target/classes` (maven-resources-plugin does not prune stale outputs), and a test loading `ClassPathResource` from the classpath fails on the phantom copy: a false failure that looks merge-caused until you clean.

## Verify an MR actually exists before citing it

Group-chat flow: dev reports "MR !N opened", manager asks for branch/sha, then pulls. If the MR never landed (create call failed, misreported), you can chase a ghost. Before quoting any MR number/branch/sha, confirm it exists:

```bash
TOKEN=$(grep -A3 "git.tsintergy.com:8070" "$HOME/Library/Application Support/glab-cli/config.yml" | grep token | sed 's/.*token: *//')
curl -s -H "PRIVATE-TOKEN: $TOKEN" \
  "http://git.tsintergy.com:8070/api/v4/projects/lvwei%2F<repo>/merge_requests?per_page=100&scope=all" \
  | python3 -c "import sys,json; [print(x['iid'],x['state'],x['sha'][:10],x['source_branch']) for x in json.load(sys.stdin)]"
```
- `scope=all` returns every MR (merged/closed included) — the iid must appear there. A "opened" MR absent from the full list = never created or already deleted.
- `state=opened` filter returning `[]` is a LEGIT result (nothing open), NOT an auth/config failure — don't re-diagnose the host; check the full list instead.
- Cross-check the branch actually exists on origin: `git ls-remote origin | grep <branch>`; a local-only branch with uncommitted worktree changes usually means the MR create step silently failed (glab API call 404/400, wrong host default `gitlab.com`).

Recreate path (verified 2026-08-20, MR !18): commit in the worktree → `git push -u origin <branch>` → POST the MR via curl (`-X POST .../merge_requests` with JSON `{source_branch, target_branch, title, description, remove_source_branch:false}`) → verify `iid`/`state`/`sha` in the response, then re-read via API to confirm. Note: re-creating can land the SAME iid the ghost MR claimed (GitLab iid counter is monotonic) — the response iid is authoritative.

**PITFALL — pushing a branch ≠ creating the MR.** An agent CAN `git push -u origin <branch>` successfully (branch lands, remote SHA confirms) and STILL not have created the MR. The `merge_requests/new?...` URL GitLab/REDIRECTS to after a push is the "new MR" ENTRY PAGE, not a real MR. Verified 2026-08-27: CC pushed `docs/render-6080-ff115-kiosk` (remote SHA `ff83b4c` confirmed) but reported the MR only via a `merge_requests/new` link; `glab mr list -s all` returned `No open merge requests match` — no MR existed. **Before claiming "MR created", run `glab mr list -s all --source-branch <branch>` (or the API `?source_branch=<branch>&scope=all`) and confirm an iid + `state:opened`. A bare git push with only a `/new` URL = no MR yet.** Fix: `glab mr create --source-branch <branch> --target-branch master --title "..." --description-file <file>` then `glab mr view <iid>` to confirm `open`.

## Accidentally merged an MR? revert -m 1, don't reset

Undoing a merge that landed on the target by mistake (admin: 「被我不小心合并了」):

- **`git revert -m 1 <merge_commit>` on the target branch** — undoes only that MR's changes, preserves every commit/MR-state that landed after it, keeps history intact. `git log --first-parent` shows what landed on top (another already-merged MR stays merged). The revert is a normal forward commit, so other open MRs cut before the merge still need a rebase check (their merge-base vs the new head).
- **`git reset --hard <pre-merge> + force-push`** — wipes the merge AND everything merged after it, rewrites history, and leaves already-merged MR records dangling. Only viable when literally nothing else landed on top.
- **If the merged content was planned work that merely went in early** (its review passes), keep it and rebase the dependent MRs instead — un-merging then re-merging the same content is churn. Present all three options (revert / reset / keep+rebase) with a recommendation to admin; never self-decide a history rewrite, and never let a stale `has_conflicts=false` on the remaining MRs mask the rebase work.

## push 与 MR 状态联动（空 diff / merged 翻转机制）

**坑（2026-09-12 实测，MR !1 llm-monitor）：push 分支先于 commit → MR 空 diff。** 若分支在改动 commit 之前就 push 过（如中途被审批打断），MR 建出来 diff 为空；补 commit 再 push 同名分支，MR 自动更新到新 sha（GET `/merge_requests/<iid>` 的 sha 变化即确认），无需重建 MR。另外 commit+push+建 MR 不要串成一条长命令——审批闸会拦整条链，拆成单步逐个执行。

**合并检测只在 push 时对 open 状态的 MR 生效（2026-09-12 实测，MR !2/!4 llm-monitor）**：这台 GitLab 13.11 标记 merged 的唯一途径是 push master 时的 post-receive 自动检测（本实例 merge API 当时全 404/405；⚠️ 2026-10-19 复测部分仓可用，见症状表 `glab mr merge 475` 行）。因此 **push master 前 MR 必须处于 open 状态**——提前 close（或 push 发生在 close 之后）会让 MR 永远停在 closed，事后 reopen + 再 push（no-op 不触发 post-receive）也救不回来，只能 close + 评论注明「以 master 为准」。顺序铁律：确认 state=merged → 最后才清理分支（⛔ 本段「本地 merge + push main」为旧通道，已被红线禁止——post-receive 机制仅解释存量 MR 的状态；现行通道=`glab mr merge --yes -R`，见症状表 merge 404 行）。同因果链的坑：**不要照搬上一个"坏 MR"的 close 流程**（MR !4 因照搬 !2 的 close-先于-push 流程而丢了 merged 状态）。
