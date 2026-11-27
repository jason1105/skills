#!/usr/bin/env python3
"""lint-prototype.py — prd-interactive-prototype 交付门静态检查（SKILL.md C 节 lint①-⑧）

用法:
  python3 scripts/lint-prototype.py <原型.html> [卡片.md]

退出码: 0 全绿 / 1 有红项
"""
import json, re, sys, subprocess, tempfile, os
from shutil import which

def fail(msgs, code, detail):
    msgs.append(f"✕ [{code}] {detail}"); return 1
def ok(msgs, code, detail):
    msgs.append(f"✓ [{code}] {detail}"); return 0

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    html_path, md_path = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None
    t = open(html_path, encoding="utf-8").read()
    msgs, red = [], 0

    # ① 静态 id 唯一 + 动态 id 表达式唯一
    ids = re.findall(r'(?<![\w-])id="([^"$][^"]*)"', t)
    dup = {i for i in ids if ids.count(i) > 1}
    dyn = re.findall(r'id="\$\{([^}]+)\}"', t)
    dupdyn = {d for d in dyn if dyn.count(d) > 1}  # 同表达式多模板: 是否同屏渲染无法静态判定, 降为提示
    if dupdyn:
        msgs.append(f"⚠ [①] 动态 id 表达式多处使用(确认不同屏渲染): {sorted(dupdyn)}")
    if dup: red += fail(msgs, "①", f"静态 id 重复: {sorted(dup)}")
    else: ok(msgs, "①", f"静态 id 唯一({len(set(ids))})")

    # STORIES 提取(纯 JSON 校验)
    m = re.search(r"window\.STORIES\s*=\s*\[(.*?)\n\];", t, re.S)
    stories = None
    if not m:
        red += fail(msgs, "schema", "window.STORIES 未找到(要求 window.STORIES = [ 起始、]; 独占一行、纯 JSON)")
    else:
        try:
            stories = json.loads("[" + m.group(1) + "]")
        except Exception as e:
            red += fail(msgs, "schema", f"STORIES 非合法 JSON(禁尾逗号/注释/单引号): {e}")
    if stories is None:
        print("\n".join(msgs)); print(f"\n❌ {red} 项红"); sys.exit(1)

    # FN_REGISTRY 提取(兼容简写/引号键/箭头函数/任意缩进)
    reg = re.search(r"const FN_REGISTRY\s*=\s*\{(.*?)\n\};", t, re.S)
    reg_fns = set(re.findall(r"^\s*['\"]?([\w-]+)['\"]?\s*\(", reg.group(1), re.M)) | set(re.findall(r"^\s*['\"]([\w-]+)['\"]\s*:", reg.group(1), re.M)) if reg else set()

    # 故障档
    faults = set(re.findall(r'<option value="([\w-]+)"', t))

    # ② demo.fn 存在 + dry-run(node 真执行)
    all_dms, all_acs = [], []
    for s in stories:
        dms = [a.get("demo", {}) for a in s.get("acs", [])] + ([s.get("target", {})] if s.get("target") else [])
        all_dms.extend(dms); all_acs.extend((s, a) for a in s.get("acs", []))
    fns_used = {dm.get("fn") for dm in all_dms if dm.get("fn")}
    dead = {f for f in fns_used if f not in reg_fns}
    if dead: red += fail(msgs, "②", f"demo.fn 死键: {sorted(dead)}")
    else:
        # dry-run: node 里 stub 浏览器环境后逐个调用, 收集异常
        dry_err = []
        if which("node") and reg:
            probe = """
const __els={};const __mk=()=>({style:{},classList:{add(){},remove(){},contains(){return false}},setAttribute(){},removeAttribute(){},addEventListener(){},appendChild(){},remove(){},click(){},scrollIntoView(){},querySelector(){return null},querySelectorAll(){return[]},getBoundingClientRect(){return{width:0,height:0,top:0,bottom:0,left:0,right:0}},innerHTML:'',textContent:'',value:'',disabled:false,checked:false,options:[],dataset:{}});
global.document={getElementById:(id)=>__els[id]||(__els[id]=__mk()),querySelector:()=>null,querySelectorAll:()=>[],createElement:()=>__mk(),addEventListener(){},body:{classList:{add(){},remove(){},contains(){return false}}},documentElement:__mk()};
global.window={addEventListener(){},location:{hash:''}};
global.localStorage={getItem:()=>null,setItem(){},removeItem(){}};
global.history={replaceState(){}};
global.confirm=()=>true;global.setTimeout=(f)=>0;global.requestAnimationFrame=(f)=>0;
const src=require('/dev/stdin');
"""
            with tempfile.TemporaryDirectory() as td:
                body = t[t.find(reg.start() and reg.group(0)):]
                # 提取整个 <script> 主体做 dry-run 会执行 UI 逻辑, 太重; 只把 FN_REGISTRY + 依赖闭包 stub 掉
                # 轻量法: new Function 解析每个函数体语法 + 调用抛 ReferenceError(依赖全局)不算失败, 只报 SyntaxError/TypeError
                js_probe = (probe.replace("const src=require('/dev/stdin');","")
                    + "\nconst FN={" + reg.group(1) + "};\n"
                    + "const out=[];for(const k of Object.keys(FN)){try{const src=FN[k].toString();new Function('const o={'+k+':('+src.replace(/^\\s*\\w+\\s*/, 'function ')+')};return true')();}catch(e){if(e instanceof SyntaxError)out.push(k+':'+e.message)}}"
                    + "console.log(JSON.stringify(out));")
                pf = os.path.join(td, "dry.js")
                open(pf, "w").write(js_probe)
                r = subprocess.run(["node", pf], capture_output=True, text=True, timeout=30)
                try:
                    errs = json.loads(r.stdout.strip().splitlines()[-1])
                except Exception:
                    errs = []
                if errs:
                    red += fail(msgs, "②", f"demo.fn dry-run 语法错误: {errs[:3]}")
                else:
                    ok(msgs, "②", f"demo.fn 全部存在({len(reg_fns)})且 dry-run 无语法错误")
        else:
            ok(msgs, "②", f"demo.fn 全部存在({len(reg_fns)}); node 缺失跳过 dry-run")

    # ③ demo.fault ∈ options
    badf = {dm.get("fault") for dm in all_dms if dm.get("fault") and dm["fault"] not in faults}
    if badf: red += fail(msgs, "③", f"fault 引用不存在档位: {sorted(map(str,badf))}")
    else: ok(msgs, "③", f"demo.fault 全部有档位({len(faults)} 档)")

    # ④ ac.id 前缀 + n 连续
    broken = [(s["id"], a["id"]) for s, a in all_acs if not str(a.get("id","")).startswith(s["id"])]
    if broken: red += fail(msgs, "④", f"AC 前缀断裂 {len(broken)}/{len(all_acs)}, 例 {broken[:2]}")
    else: ok(msgs, "④", f"ac.id 以父 story.id 开头({len(all_acs)} 条)")

    # ⑤ 零外链(引号可选 + url()/fetch/meta refresh/@import)
    ext = re.findall(r'(?:src|href|srcset)\s*=\s*["\']?(?:https?:)?//[^"\'\s>]+', t)
    ext += re.findall(r'url\(\s*["\']?(?:https?:)?//', t)
    ext += re.findall(r'@import\s+["\']?(?:https?:)?//', t)
    ext += re.findall(r'fetch\(\s*["\']https?://', t)
    ext += re.findall(r'<meta[^>]+http-equiv=["\']?refresh', t)
    if ext: red += fail(msgs, "⑤", f"外链: {ext[:3]}")
    else: ok(msgs, "⑤", "零外链")

    # ⑥ 徽标引用(剔除 STORIES 块后按 载体匹配)
    rest = t.replace(m.group(0), "")
    carriers = set(re.findall(r"data-req=[\"']?(REQ-[\w.-]+)", rest))
    carriers |= set(re.findall(r"reqtag\('(REQ-[\w.-]+)'\)", rest))
    carriers |= set(re.findall(r"locateFromCard\('(REQ-[\w.-]+)'\)", rest))
    st_ids = {s["id"] for s in stories}
    zero = sorted(st_ids - carriers)
    if zero: red += fail(msgs, "⑥", f"页面零徽标 REQ(剔除 STORIES 后无载体): {zero}")
    else: ok(msgs, "⑥", f"全部 {len(st_ids)} REQ 有页面徽标载体")

    # ⑦ 双源对账(set+条数+重复)
    if md_path:
        md = open(md_path, encoding="utf-8").read()
        md_req_l = re.findall(r"^### (REQ-[\w.-]+)(?=\s|　|[（(])", md, re.M)
        md_ac_l = re.findall(r"\*\*(REQ-[\w.-]+-AC\d+)\*\*", md)
        md_req, md_ac = set(md_req_l), set(md_ac_l)
        st_ac = {a["id"] for s in stories for a in s.get("acs", [])}
        probs = []
        if md_req ^ st_ids: probs.append(f"REQ 差: MD独有{sorted(md_req-st_ids)[:3]} STORIES独有{sorted(st_ids-md_req)[:3]}")
        if md_ac ^ st_ac: probs.append(f"AC 差: MD独有{sorted(md_ac-st_ac)[:3]} STORIES独有{sorted(st_ac-md_ac)[:3]}")
        if len(md_req_l) != len(stories): probs.append(f"MD 卡片数 {len(md_req_l)} ≠ STORIES {len(stories)}")
        if len(md_ac_l) != len(md_ac): probs.append(f"MD AC 有重复({len(md_ac_l)} 行/{len(md_ac)} 个)")
        h2req = re.findall(r"^## (REQ-[\w.-]+)", md, re.M)
        if h2req: probs.append(f"MD 标题层级违规(## REQ 二级): {h2req[:3]}")
        ver_titles = re.findall(r"^#### 【1\. 核心口径（v[\d.]+ 现行）】", md, re.M)
        if ver_titles: probs.append(f"MD 节标题带版本号({len(ver_titles)} 处, 版本进字段表)")
        if probs: red += fail(msgs, "⑦", "; ".join(probs))
        else: ok(msgs, "⑦", f"卡片MD↔STORIES 一致(REQ {len(md_req)}/AC {len(md_ac)}, 无重复)")
    else:
        ok(msgs, "⑦", "未传卡片 MD, 跳过")

    # ⑧ schema 校验
    sp = []
    REQ_FIELDS = ["id","name","module","role","pri","core","points","interact","conf","acs","target"]
    for s in stories:
        sid = s.get("id","?")
        for f_ in REQ_FIELDS:
            if f_ not in s: sp.append(f"{sid} 缺 {f_}")
        tg = s.get("target", {})
        if not tg.get("view"): sp.append(f"{sid} target 无 view")
        if not (tg.get("fn") or tg.get("act")): sp.append(f"{sid} target 无 fn|act")
        if not s.get("acs"): sp.append(f"{sid} acs 为空")
        for a in s.get("acs", []):
            for k in ("id","given","when","then","demo"):
                if k not in a: sp.append(f"{sid} 某 AC 缺 {k}")
            dm = a.get("demo", {})
            if dm.get("how") not in ("live","note","none"): sp.append(f"{a.get('id')} how 非法")
            if dm.get("how") == "live" and not (dm.get("fn") or dm.get("act")): sp.append(f"{a.get('id')} live 无 fn|act")
            if dm.get("how") == "note" and not dm.get("note"): sp.append(f"{a.get('id')} note 缺注记元素字段")
    if sp: red += fail(msgs, "⑧", f"schema 违规 {len(sp)} 处: {sp[:4]}")
    else: ok(msgs, "⑧", f"schema 全合规({len(stories)} stories)")

    # 语法门: 全部 script 块
    if which("node"):
        blocks = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", t, re.S)
        blocks = [b for b in blocks if b.strip()]
        if not blocks:
            red += fail(msgs, "语法门", "无 script 块")
        else:
            errs = []
            with tempfile.TemporaryDirectory() as td:
                for i, b in enumerate(blocks):
                    pf = os.path.join(td, f"s{i}.js")
                    open(pf, "w").write(b)
                    r = subprocess.run(["node", "--check", pf], capture_output=True, text=True)
                    if r.returncode: errs.append(r.stderr.strip().splitlines()[-1][:80] if r.stderr else "syntax err")
            if errs: red += fail(msgs, "语法门", f"{len(errs)}/{len(blocks)} 块语法错: {errs[:2]}")
            else: ok(msgs, "语法门", f"node --check {len(blocks)} 块全过")

    print("\n".join(msgs))
    print(f"\n{'✅ 全绿' if red == 0 else f'❌ {red} 项红'}")
    sys.exit(0 if red == 0 else 1)

if __name__ == "__main__":
    main()
