# Planning-comment workflow for "待规划" GitLab issues

Pattern proven on chrome-show-issue-and-mr-no #9 (refactor planning, note 746901): the team
expectation is that planning output lands as an issue comment (留痕), NOT as a branch/commit/MR.

## Steps

1. Fetch the issue body first — it contains the real requirements, candidate module
   boundaries, and design principles. `glab api "projects/<id>/issues/<iid>"` (NOT
   `glab issue view` — nil-pointer panic). The body often already lists candidate
   boundaries; the plan must reference them, not invent parallel ones.
2. Survey the actual code BEFORE writing the plan:
   - `grep -nE "^(async )?function |^const |^let " src/<file>` — function inventory with line numbers.
   - Read the top of the file for closure state variables (IIFE `let` block) and the end for
     lifecycle wiring (event listeners, bootstrap).
   - Check manifest / script registration arrays for load-order constraints (new files must
     be added there too).
3. Write the plan to a temp file (e.g. `.issue<N>-plan.md` in repo root) with:
   - 现状职责清单 table: domain | representative functions (line refs) | owned state | LOC estimate.
   - Phased steps, each independently mergeable/revertible, with a dependency direction diagram.
   - Explicit "不建议抽" (do-not-extract) items to resist over-modularization.
   - Implementation-order recommendation and which steps gate other known issues.
4. Publish: `glab api -X POST "projects/<id>/issues/<iid>/notes" -f "body=$(cat .issue<N>-plan.md)"`.
   (`--input <json>` returns 400 "body is missing" on this glab build — see SKILL.md pitfalls.)
5. Verify the note body in the response JSON (id + body prefix), then delete the temp file.
6. Group-chat report: cite the note id, summarize the plan in 4-6 bullets, @manager for
   review/prioritization, and flag cross-issue coupling points for parallel planners.
