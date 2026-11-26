#!/usr/bin/env python3
"""Conflict-block lister + resolver for a git merge in progress.

Why: a merge of an advanced main into a long-lived branch often has several
conflict blocks per file, and the rule differs per block
(`main` = main moved/rewrote it, `head` = ours is an addition, `both` = one
side changed line A, the other line B -> keep BOTH, `custom` = hand-written
replacement). Doing that by hand with sed/edit is where files get mangled.

Usage
-----
  # 1. inspect every unresolved block in every conflicted file
  python3 resolve_merge_conflicts.py --list

  # 2. write a plan (JSON) and apply it
  python3 resolve_merge_conflicts.py --plan /tmp/plan.json

plan.json
---------
  {
    "docs/design/x.md": [
      {"idx": 0, "rule": "main"},
      {"idx": 1, "rule": "custom",
       "lines": ["- line one from main", "- line two from ours"]},
      {"idx": 2, "rule": "both"},
      {"idx": 3, "rule": "head", "append": ["| v1.0 | 2026-09-21 | 修改 | ... |"]}
    ]
  }

  * idx      = block index from --list (0-based, order in file)
  * rule     = main | head | both | custom
  * lines    = replacement lines (rule=custom)
  * lines_file = same, read from a file (rule=custom)
  * append   = extra lines appended at END OF FILE (used when main MOVED a
               section to the doc end and your row must follow it there)

The script refuses to write if the plan does not cover EVERY block
(the `assert len(blocks) == len(plan)` guard), and prints a per-block report
plus the scope-parity command to run afterwards:

  git add -A <paths> && git diff --name-only --diff-filter=U   # must be empty
  git diff --stat --cached origin/main -- <paths>             # must equal
  git diff --stat <merge-base>..<branch-before-merge>          # ...this size
"""

import argparse
import json
import subprocess
import sys


def conflicted_files():
    out = subprocess.run(["git", "diff", "--name-only", "--diff-filter=U"],
                         capture_output=True, text=True, check=True).stdout
    return [l for l in out.splitlines() if l.strip()]


def blocks_of(lines):
    """Return [(start, end)] index ranges of conflict blocks, markers included."""
    out, i = [], 0
    while i < len(lines):
        if lines[i].startswith("<<<<<<<"):
            j = i
            while not lines[j].startswith(">>>>>>>"):
                j += 1
            out.append((i, j))
            i = j + 1
        else:
            i += 1
    return out


def sides(lines, start, end):
    mid = [k for k in range(start, end) if lines[k].startswith("=======")][0]
    return lines[start + 1:mid], lines[mid + 1:end]


def cmd_list(paths):
    files = paths or conflicted_files()
    if not files:
        print("no conflicted files")
        return 0
    for p in files:
        lines = open(p, encoding="utf-8").readlines()
        bl = blocks_of(lines)
        print(f"===== {p}  ({len(bl)} block(s), {len(lines)} lines)")
        for i, (s, e) in enumerate(bl):
            head, main = sides(lines, s, e)
            print(f"  -- block {i}: file lines {s + 1}-{e + 1} "
                  f"(HEAD {len(head)} line(s) / origin-side {len(main)} line(s))")
            for tag, part in (("HEAD", head), ("MAIN", main)):
                for l in part[:6]:
                    print(f"     {tag}| {l.rstrip()[:150]}")
                if len(part) > 6:
                    print(f"     {tag}| ... ({len(part) - 6} more)")
    return 0


def apply_plan(plan):
    report = {}
    for p, entries in plan.items():
        lines = open(p, encoding="utf-8").readlines()
        bl = blocks_of(lines)
        if len(bl) != len(entries):
            raise SystemExit(
                f"{p}: plan has {len(entries)} entries but file has {len(bl)} "
                f"conflict block(s) — re-run --list and fix the plan")
        out, prev, notes = [], 0, []
        for (s, e), ent in zip(bl, entries):
            out.extend(lines[prev:s])
            head, main = sides(lines, s, e)
            rule = ent["rule"]
            if rule == "main":
                out.extend(main)
            elif rule == "head":
                out.extend(head)
            elif rule == "both":
                out.extend(main)
                out.extend(head)
            elif rule == "custom":
                repl = ent.get("lines")
                if repl is None and ent.get("lines_file"):
                    repl = open(ent["lines_file"], encoding="utf-8").read().splitlines()
                if repl is None:
                    raise SystemExit(f"{p}: rule=custom needs 'lines' or 'lines_file'")
                out.extend([l if l.endswith("\n") else l + "\n" for l in repl])
            else:
                raise SystemExit(f"{p}: unknown rule {rule!r}")
            notes.append((ent.get("idx", "?"), rule, len(head), len(main)))
            prev = e + 1
        out.extend(lines[prev:])
        for ent in entries:
            if ent.get("append"):
                if not out[-1].endswith("\n"):
                    out[-1] += "\n"
                out.extend([l if l.endswith("\n") else l + "\n" for l in ent["append"]])
                notes.append(("append", "end-of-file", 0, len(ent["append"])))
        open(p, "w", encoding="utf-8").write("".join(out))
        report[p] = notes
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--plan")
    ap.add_argument("paths", nargs="*")
    a = ap.parse_args()
    if a.list or not a.plan:
        return cmd_list(a.paths)
    rep = apply_plan(json.load(open(a.plan, encoding="utf-8")))
    for p, notes in rep.items():
        print(p)
        for idx, rule, nh, nm in notes:
            print(f"   block {idx}: rule={rule} (HEAD {nh} / MAIN {nm})")
    print("\nnext (must be empty / must match pre-merge size):")
    paths = " ".join(json.load(open(a.plan, encoding="utf-8")).keys())
    print(f"  grep -rn -E '^(<<<<<<<|=======$|>>>>>>>)' {paths}")
    print("  git add -A . && git diff --name-only --diff-filter=U")
    print(f"  git diff --stat --cached origin/main -- {paths}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
