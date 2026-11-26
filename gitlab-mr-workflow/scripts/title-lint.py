#!/usr/bin/env python3
"""标题前缀码校验：议题 `[类别][状态?] 摘要` / MR `type(scope): 摘要`。

合法组合表解析自 references/title-prefix-code.md——改表即改规则。

用法:
  title-lint.py issue "<标题>" [<标题>...]
  title-lint.py mr "<标题>" [<标题>...]
  title-lint.py < 清单     # 每行: issue<TAB>标题 | mr<TAB>标题 | #32<TAB>标题 | !73<TAB>标题
退出码: 0 全部合规 / 1 有不合规 / 2 用法错误或组合表解析失败
"""
import re
import sys
from pathlib import Path

TABLE_MD = Path(__file__).resolve().parent.parent / "references" / "title-prefix-code.md"
TABLE_HEADER_PREFIX = "| 类别 \\ 状态 |"
NONE_COL = "无状态"
MR_TYPES = ("feat", "fix", "docs", "refactor", "test", "chore", "revert")

ISSUE_RE = re.compile(r"^\[(?P<cat>[^\]\[]+)\](?:\[(?P<status>[^\]\[]+)\])?\s+(?P<summary>\S.*)$")
MR_RE = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[a-z0-9_./-]+)\))?!?: (?P<summary>\S.*)$")
DRAFT_RE = re.compile(r"^(Draft:\s*|\[Draft\]:?\s*|\(Draft\):?\s*)", re.I)
REF_RE = re.compile(r"\b(Closes|Refs)\s*#\d+", re.I)
CARD_RE = re.compile(r"^(issue\s*#\d+|!\d+|#\d+|t\d+(\.\d+)*)\b", re.I)
BRANCH_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*/[A-Za-z0-9_/-]+$")


def load_matrix(path):
    """解析组合表 → (状态列顺序, 含「无状态」; {类别: {允许的状态, 含「无状态」}})。"""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.startswith(TABLE_HEADER_PREFIX)), None)
    if start is None:
        raise ValueError("未找到组合表（表头 %r）于 %s" % (TABLE_HEADER_PREFIX, path))

    def cells(line):
        return [c.strip() for c in line.strip().strip("|").split("|")]

    cols = cells(lines[start])[1:-1]  # 末列是「示例」
    matrix = {}
    for ln in lines[start + 2:]:  # 跳过表头与 |---| 分隔行
        if not ln.startswith("|"):
            break
        row = cells(ln)
        matrix[row[0]] = {c for c, cell in zip(cols, row[1:-1]) if cell == "✅"}
    if not matrix:
        raise ValueError("组合表无数据行: %s" % path)
    return cols, matrix


def check_issue(title, cols, matrix):
    m = ISSUE_RE.match(title)
    if not m:
        hint = "；类别与状态分两个方括号，如 `[缺陷][生产]`" if re.match(r"^\[[^\]]+\s[^\]]+\]", title) else ""
        return "期望 `[类别][状态?] 摘要`" + hint
    cat, status, summary = m.group("cat"), m.group("status"), m.group("summary")
    if cat not in matrix:
        hint = "；类别与状态分两个方括号" if cat.split(" ")[0] in matrix else ""
        return "未知类别「%s」%s；合法类别：%s" % (cat, hint, " / ".join(matrix))
    allowed = matrix[cat]
    if status is None:
        if NONE_COL not in allowed:
            return "类别「%s」须带状态位；允许：%s" % (cat, " / ".join(c for c in cols if c in allowed))
    elif status not in cols:
        return "未知状态「%s」；合法状态：%s" % (status, " / ".join(c for c in cols if c != NONE_COL))
    elif status not in allowed:
        return "类别「%s」不适用状态「%s」；该类别允许：%s" % (
            cat, status, " / ".join(c for c in cols if c in allowed))
    if summary.endswith("。"):
        return "摘要不以句号结尾"
    return None


def check_mr(title):
    t = DRAFT_RE.sub("", title, count=1)  # Draft 前缀合法，校验时剥掉
    m = MR_RE.match(t)
    if not m:
        return "期望 `type(scope): 摘要`；type ∈ %s" % " / ".join(MR_TYPES)
    typ, summary = m.group("type"), m.group("summary")
    if typ not in MR_TYPES:
        return "未知 type「%s」；type ∈ %s" % (typ, " / ".join(MR_TYPES))
    if REF_RE.search(t):
        return "Closes/Refs 写正文首行，不进标题"
    if CARD_RE.match(summary):
        return "卡号不当标题；写进 scope 或正文"
    if BRANCH_RE.match(summary):
        return "分支名不当标题"
    if summary.endswith("。"):
        return "摘要不以句号结尾"
    return None


def main(argv):
    if len(argv) >= 2 and argv[1] in ("issue", "mr"):
        items = [(argv[1], t) for t in argv[2:]]
    elif len(argv) == 1:
        if hasattr(sys.stdin, "reconfigure"):
            sys.stdin.reconfigure(encoding="utf-8")
        items = []
        for raw in sys.stdin:
            raw = raw.rstrip("\n")
            if not raw.strip():
                continue
            head, sep, title = raw.partition("\t")
            head = head.strip()
            if head.lower() in ("issue", "mr"):
                kind = head.lower()
            elif head.startswith("#"):
                kind = "issue"
            elif head.startswith("!"):
                kind = "mr"
            else:
                kind = None
            if not kind or not sep:
                print("用法错误 | %r | 每行须为 issue<TAB>标题 或 mr<TAB>标题" % raw, file=sys.stderr)
                return 2
            items.append((kind, title))
    else:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if not items:
        print(__doc__.strip(), file=sys.stderr)
        return 2

    cols = matrix = None
    if any(k == "issue" for k, _ in items):
        try:
            cols, matrix = load_matrix(TABLE_MD)
        except (OSError, ValueError, IndexError) as e:
            print("组合表解析失败: %s" % e, file=sys.stderr)
            return 2

    bad = 0
    for kind, title in items:
        err = check_issue(title, cols, matrix) if kind == "issue" else check_mr(title)
        if err:
            bad += 1
            print("%s | %s | %s" % (kind, title, err))
    print("合规 %d / 违规 %d" % (len(items) - bad, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
