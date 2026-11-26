# Large-block verbatim refactor + pure-refactor MR evidence (issue-11 BADGE_CSS split, 2026-09)

Pattern from moving the 720-line `BADGE_CSS` template string out of `src/ui.js` into a new UMD sibling `src/badge-css.js` (chore: zero behavior change, prerequisite for splitting UI/dev file ownership on #11).

## Do big verbatim moves with execute_code Python marker surgery, NOT multi-line `patch`

A `patch` whose `old_string` abuts/spans the target block got **fuzzy-matched into ALSO deleting the adjacent icon-constant block** (COPY_ICON_PATHS / SUCCESS_ICON_PATHS), leaving `src/ui.js` syntactically broken. Recovery that worked:

1. `git checkout -- <file>` immediately (restores HEAD — the new file you already wrote survives; it's untracked).
2. Redo the move in Python: slice between exact start/end markers (`  const X = \`` ... `  \`;`), assert the extracted body contains no backtick/`${` (proves it's a static string), then reassemble.
3. Verify the seam (print lines around the cut) before re-running tests.

Prefer small, targeted `patch` calls (one per hunk: e.g. the `return { BADGE_CSS,` export line) — those apply cleanly. The failure was specifically a large old_string that abuts multiple regions.

## New file must mirror sibling UMD + be wired into every loading chain

- New file uses the SAME IIFE wrapper as its siblings: `module.exports` + `root.GitLabReferenceBadgeCss` dual-expose.
- `CONTENT_SCRIPT_FILES` in `src/permissions.js` inserts `'src/badge-css.js'` BEFORE `'src/ui.js'` (data before consumer).
- Mirror the change in BOTH order-assertion tests (`tests/manifest.test.js` regex + `tests/permissions.test.js` exact array) AND the vm loading chain in `tests/content.test.js` `createHarness` (add `badgeCssSource` read + `vm.runInNewContext(badgeCssSource, ...)` line).

## Zero-behavior-change evidence chain for the MR description

All five ran green this session — reuse as a checklist for any pure-refactor MR:

1. baseline `npm run test` BEFORE editing — record pass count (was 171/171);
2. byte-compare moved block vs same block from `git show HEAD:<oldfile>` → must print `VERBATIM IDENTICAL: True`;
3. `node --check` every touched file;
4. grep old file for residual references to the moved symbol (`ui.js` BADGE_CSS → 0) and the consumer for stale old-path refs (`uiApi.BADGE_CSS` → gone);
5. re-run suite → same counts as baseline.

## GitLab API notes hit while landing the MR

- **Branch off `origin/main`, not local main, when the clone is diverged.** `git status --short --branch` shows `ahead N, behind M`. Here local main was behind 2 and upstream had edited the same `tests/content.test.js` harness the branch needed to change; basing on `origin/main` (after `git fetch`) avoided a guaranteed MR conflict.
- **POST response is authoritative for MR creation — skip the ceremonial follow-up GET.** `HTTP 201` + `iid` + `state:"opened"` + `web_url` in the POST response proves the MR exists. A redundant GET right after can trip the security scanner's "downloads content" approval gate on this plain-HTTP instance and block the session waiting for user consent (happened this session: `BLOCKED: Command timed out without user response`). Report from the POST response you already hold; use GETs later only for real state changes.
- `git credential fill` (`protocol=http\nhost=git.tsintergy.com:8070`) returns a real 20-char token; write it to a temp file and pass via `PRIVATE-TOKEN` header. Never print it.

## execute_code file I/O

In execute_code, read/write files with plain `open()` — the session cwd is the repo root. The imported `hermes_tools.read_file` returned a dict WITHOUT the documented `content` key (KeyError) in this session.
