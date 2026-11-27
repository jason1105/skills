#!/usr/bin/env python3
"""lint-prototype.py — prd-interactive-prototype 交付门静态检查（SKILL.md C 节 lint①-⑦）

用法:
  python3 scripts/lint-prototype.py <原型.html> [卡片.md]

退出码: 0 全绿 / 1 有红项
"""
import json, re, sys, subprocess, tempfile, os

def fail(msgs, code, detail):
    msgs.append(f"✕ [{code}] {detail}")

def ok(msgs, code, detail):
    msgs.append(f"✓ [{code}] {detail}")

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    html_path, md_path = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None
    t = open(html_path, encoding="utf-8").read()
    msgs, red = [], 0

    # ① id 唯一性(含模板串内静态 id + 动态拼接前缀)
    ids = re.findall(r'id="([\w-]+)"', t)
    dup = {i for i in ids if ids.count(i) > 1}
    if dup: fail(msgs, "①", f"id 重复: {sorted(dup)}"); red += 1
    else: ok(msgs, "①", f"id 唯一 ({len(set(ids))} 个)")

    # STORIES 提取
    m = re.search(r"window\.STORIES\s*=\s*\[(.*?)\n\];", t, re.S)
    if not m:
        fail(msgs, "schema", "window.STORIES 未找到"); print("\n".join(msgs)); sys.exit(1)
    stories = json.loads("[" + m.group(1) + "]")

    # FN_REGISTRY 提取
    reg = re.search(r"const FN_REGISTRY\s*=\s*\{(.*?)\n\};", t, re.S)
    reg_fns = set(re.findall(r"^\s{2}(\w+)\(", reg.group(1), re.M)) if reg else set()

    # 故障档 options
    faults = set(re.findall(r'<option value="([\w-]+)"', t))

    # ② demo.fn ∈ FN_REGISTRY (死键)
    dead_fn, all_acs = set(), []
    for s in stories:
        dms = [a.get("demo", {}) for a in s.get("acs", [])] + ([s.get("target", {})] if s.get("target") else [])
        for dm in dms:
            fn = dm.get("fn")
            if fn and fn not in reg_fns: dead_fn.add(fn)
        all_acs.extend((s, a) for a in s.get("acs", []))
    if dead_fn: fail(msgs, "②", f"demo.fn 死键(不在 FN_REGISTRY): {sorted(dead_fn)}"); red += 1
    else: ok(msgs, "②", f"demo.fn 全部存在于 FN_REGISTRY ({len(reg_fns)} 个函数)")

    # ③ demo.fault ∈ options
    bad_fault = {dm.get("fault") for s in stories for a in s.get("acs", [])
                 if (dm := a.get("demo", {})).get("fault") and dm["fault"] not in faults}
    if bad_fault: fail(msgs, "③", f"demo.fault 引用不存在的档位: {sorted(map(str,bad_fault))}"); red += 1
    else: ok(msgs, "③", f"demo.fault 全部有对应档位 ({len(faults)} 档)")

    # ④ ac.id 以父 story.id 开头
    broken = [(s["id"], a["id"]) for s, a in all_acs if not a.get("id", "").startswith(s["id"])]
    if broken: fail(msgs, "④", f"AC 前缀断裂 {len(broken)}/{len(all_acs)}，例: {broken[:2]}"); red += 1
    else: ok(msgs, "④", f"ac.id 全部以父 story.id 开头 ({len(all_acs)} 条)")

    # ⑤ 零外链
    ext = re.findall(r'(?:src|href)\s*=\s*["\'](?:https?:)?//[^"\']+', t)
    ext += re.findall(r'<link[^>]+href\s*=\s*["\']http', t)
    if ext: fail(msgs, "⑤", f"发现外链: {ext[:3]}"); red += 1
    else: ok(msgs, "⑤", "零外链")

    # ⑥ ∀story 全文件存在徽标/定位引用
    no_ref = [s["id"] for s in stories
              if s["id"] not in t.replace(json.dumps(stories, ensure_ascii=False), "")]
    if no_ref: fail(msgs, "⑥", f"页面零引用的 REQ: {no_ref}"); red += 1
    else: ok(msgs, "⑥", f"全部 {len(stories)} 条 REQ 在页面有引用")

    # ⑦ 双源对账(可选)
    if md_path:
        md = open(md_path, encoding="utf-8").read()
        md_req = set(re.findall(r"^### (REQ-[\w.-]+) ", md, re.M))
        st_req = {s["id"] for s in stories}
        md_ac = set(re.findall(r"\*\*(REQ-[\w.-]+-AC\d)\*\*", md))
        st_ac = {a["id"] for s in stories for a in s.get("acs", [])}
        d1, d2 = md_req ^ st_req, md_ac ^ st_ac
        if d1 or d2:
            fail(msgs, "⑦", f"双源漂移: REQ差={sorted(d1)[:3]} AC差={sorted(d2)[:3]}"); red += 1
        else: ok(msgs, "⑦", f"卡片MD↔STORIES 一致 (REQ {len(md_req)} / AC {len(md_ac)})")
    else:
        ok(msgs, "⑦", "未传卡片 MD，跳过双源对账")

    # 语法门: <script> node --check
    sm = re.search(r"<script>(.*)</script>", t, re.S)
    if sm and shutil_which("node"):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write(sm.group(1)); tmp = f.name
        r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
        os.unlink(tmp)
        if r.returncode: fail(msgs, "语法门", f"node --check: {r.stderr[:120]}"); red += 1
        else: ok(msgs, "语法门", "node --check 通过")

    print("\n".join(msgs))
    print(f"\n{'✅ 全绿' if red == 0 else f'❌ {red} 项红'}")
    sys.exit(0 if red == 0 else 1)

def shutil_which(x):
    from shutil import which; return which(x)

if __name__ == "__main__":
    main()
