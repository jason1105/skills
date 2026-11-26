# Regression-test gate handoff: 补测 after a conditional-pass review, and mutation-check validation

Class pattern from the chrome-show-issue-and-mr-no group-chat flow (dev2 role), 2026-08-19 (MR !12 / issue #6 step 1). Applies whenever a reviewer (manager gate review) passes an MR conditionally with "test gap" as the blocking item and the implementer must add regression tests on top of an existing green branch.

## Workflow (kept short — sequence matters)

1. **Locate the branch's checkout, don't fight git.** Parallel agents often leave the branch checked out in a temp worktree. `git branch -vv | grep <branch>` shows `(path)` when a worktree holds it — `cd` into that worktree and work there. Trying `git checkout <branch>` in the main repo fails with "already used by worktree"; `git worktree list` also helps. Do NOT create a second branch/checkout unless asked — push to the SAME branch the MR tracks so the MR picks up the new commit.
2. **Tests only, no src changes.** A gate-review blocker "missing tests for new behavior" means: add tests that pin the EXISTING (already reviewed) implementation. Resist the urge to "fix" the minor non-blocking observations the reviewer listed — mention in the MR note that they were left untouched (维持不阻塞结论).
3. **Map every guard to a test.** Read the diff'd code, list each new guard (abort call, re-entry check, unchanged-skip, generation check), and write one test per guard. If a guard cannot be observed from the DOM, assert on internal side effects exposed by the harness (e.g. `fetchCalls[n].init.signal.aborted === true`).
4. **Run the suite, then MUTATION-CHECK the tests** (this is what convinces the reviewer the tests aren't decoration):
   - `cp src/<file> /tmp/<file>.bak`
   - Use python string-replace (not sed with `,+Np` — BSD sed rejects it and complex inline sed trips the Hermes command blocklist; write a small python3 -c or a script file) to remove/neutralize each guard.
   - `npm test` → at least one new test must flip to `not ok`.
   - `cp /tmp/<file>.bak src/<file>` → full suite green again.
   - Report the mutation results explicitly in the MR note ("移除守卫 X → 用例 N 转 not ok，恢复后全绿").
   - Caveat: one mutation pass may only flip ONE test even if you removed several guards (whichever fires first aborts the run's cleanliness). That's fine — but be honest in the note about which guards were proven by which mutation. If a removed guard flips NOTHING, either the test is weak or the guard is dead code — investigate before pushing.
5. **Commit + push to the MR branch**, then leave a trace note on the MR via glab API (URL-encoded project path, `-f body=...` form) with: commit sha, per-test mapping to the review's requested cases, test counts (old/new/total), and the mutation-check evidence. Sign with name+role per room convention, then @reviewer for re-review.

## Node `vm` DOM-harness test patterns (chrome-show content script harness)

The project's `tests/content.test.js` harness runs src in a `vm.runInNewContext` with a fake DOM. Reusable recipes:

- **Deferred fetch**: `fetchResults: [deferred(), deferred()]` — promises you resolve later to simulate slow/out-of-order responses. The harness's fetch wrapper already rejects on `signal` abort (`init.signal.addEventListener('abort', ...)`) — so `signal.aborted === true` is directly assertable from `harness.fetchCalls[n].init`.
- **Re-render proof via node identity**: for "unchanged does not re-render", grab the DOM child (`results.querySelector('[data-open-items-group]')`) before the trigger, then compare by **reference equality** after — `replaceChildren` creates new nodes, so same-reference ⇒ no re-render. More robust than textContent comparison.
- **Triggering sync() without navigation**: `harness.dispatchWindow('resize'); harness.flushAnimationFrames();` — resize routes through `scheduleSync` (rAF) → `sync()` with unchanged URL, exercising the unchanged-skip branch without touching location.
- **Re-entry (guard-level) testing**: if the UI layer already disables the button during loading (so a click can't reach the guard), simulate the guard-failure path by calling the guarded function through whatever handle the harness context exposes, and assert the observable side effect (fetch call count unchanged). Note this honestly in the MR comment — DOM-layer prevention is covered by other tests.
- **SPA navigation**: `harness.location.href = <newUrl>; harness.dispatchWindow('popstate'); harness.flushAnimationFrames();` then flush microtasks.

## Failure/quota notes

- Reviewer-side HTTP 429s can interrupt manager responses mid-review — expect the review to arrive in fragments across several messages; reconcile fragments before starting work.
- The merge sequence (!10 → !11 → !12 → !13 style ordering) is owned by manager/admin; the implementer's job on a conditional pass is strictly: tests + push + note + @reviewer. Don't rebase or touch other branches unless told.
