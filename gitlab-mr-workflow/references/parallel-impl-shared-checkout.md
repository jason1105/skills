# Parallel implementation lines in the chrome-show-issue-and-mr-no collab flow

Session evidence (2026-08-19, issue #6/#9 kickoff): manager launched three parallel
lines on the SAME single checkout — dev doing #9 step 1 (extracting ~732 lines of
`src/content.js` into a new `src/ui.js`), dev2 doing #6 stage A (surgical edits in
`fetchWithTimeout` / `resetNavigation` / `loadOpenItems` / `loadMoreOpenItems` /
`updateConfig` / `sync`), test building `tests/browser-helpers.js`.

## What went wrong

Manager had verified "function-level non-overlap" between dev and dev2 — true at
the function level, but both wrote to the same file on disk with no staging
boundary. Mid-way through dev2's edits:

- `patch` reported "file was modified since you last read on disk" plus a
  syntax error at a line dev2 never touched (`return icon` orphaned by dev's
  in-progress extraction).
- `git diff --stat` showed `src/content.js | 787 +++---` and a new untracked
  `src/ui.js` — dev's WIP interleaved with dev2's completed edits.
- The two writers' changes became inseparable in the working tree; no clean
  revert existed that would not destroy one side's work.

## Correct handling (what worked)

1. **Stop editing on first sign of a foreign writer** — "modified since last
   read" warning or lint/syntax errors in untouched regions are the signal.
2. **Do NOT revert** (`git checkout --` would destroy the other agent's WIP).
3. **Audit, don't assume**: `git status --short` + `git diff --stat` to see the
   full foreign footprint (modified + untracked files).
4. **Escalate to the coordinator** (manager) with evidence and two options:
   - one side lands/commits its boundary first, the other rebases and replays
     function-level changes onto the new HEAD (cheap for surgical edits);
   - or the paused side commits first.
5. Keep your own change list written down (function names + intent per edit) so
   the replay after rebase is mechanical, not archaeology.

## Prevention rule for orchestrators

When assigning parallel implementation tasks, function-level non-overlap is NOT
sufficient — one writer per checkout. Assign each line its own branch or
`git worktree` before code is written (see also skill `merge-reconciler` /
`orca-cli` for worktree management). If tasks must share a checkout, serialize
them explicitly in the task assignment.

## Review/verification side: isolate, don't trust the dirty tree

The shared checkout is not only a WRITE hazard — it also invalidates local
verification. When a reviewer (manager) or tester runs `npm run test` in the
shared tree while another agent's WIP is uncommitted, failures can be pure
pollution. Observed (2026-08-19, MR !10 gate review): `npm run test` failed 5
cases in the shared tree (`handleNavigationEvent is not defined`,
manifest test expecting `2 !== 1` content scripts, `'release' !== ''`) — the
tree held an uncommitted `manifest.json` adding a `navigation-hook.js`
content-script entry, `src/content.js` +83 lines, and untracked
`src/navigation-hook.js`. The MR branch itself (`feature/issue-9-step1-ui-extraction`,
`a602f3a`) was clean: full suite 104/104.

Review procedure when `git status --porcelain` shows foreign WIP:

1. `git worktree add /tmp/<review-name> <mr-branch>` — clean checkout of the MR branch.
2. Run tests there; that result is the gate verdict.
3. `git worktree remove /tmp/<review-name> --force` when done.
4. Post BOTH facts in the MR note: clean-baseline result AND the pollution
   inventory, so the WIP owner knows their tree is being read and other
   agents don't chase phantom regressions. Do NOT `glab mr checkout` in the
   shared tree — it would overwrite the other agent's uncommitted WIP.

`git worktree list` also reveals other reviewers' worktrees (e.g. a detached
`.wt-9a-accept` tree at the reviewed SHA) — useful to know who else is
verifying the same branch.

## Also from this session: skip-render guard pitfalls

While implementing "#6 stage A: skip re-render when reference unchanged" in
`sync()`, two unit tests broke: the storage-change → `updateConfig` →
`sync({resetCopy:false})` path relies on `sync()` re-rendering to reflect new
display config (listFilter, search memory) even though the URL reference is
identical. Fix: add a `forceRender` option to `sync()`; `updateConfig` passes
`forceRender: navigationDisplayChanged` on its display-change branch. Lesson:
any render-skip optimization must enumerate ALL callers and check which ones
depend on the render as a side effect of reaching sync, not of the reference
changing.
