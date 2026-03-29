# 可视化 Widget 模板

本文件提供 `visualize:show_widget` 的 HTML 代码框架，覆盖扫描报告所有标准区块。

## CSS 变量与样式基础

```html
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
.report { padding: 1rem 0; font-family: var(--font-sans); }
.section { margin-bottom: 2rem; }
.section-title {
  font-size: 12px; font-weight: 500; color: var(--color-text-secondary);
  text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 12px;
}

/* ── 概览卡片 ─────────────────────────────── */
.cards { display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); gap:10px; margin-bottom:1rem; }
.card { background:var(--color-background-secondary); border-radius:var(--border-radius-md); padding:14px 16px; }
.card-label { font-size:12px; color:var(--color-text-secondary); margin-bottom:6px; }
.card-value { font-size:26px; font-weight:500; }
.card-sub   { font-size:12px; color:var(--color-text-tertiary); margin-top:2px; }
.card.high   .card-value { color:#A32D2D; }
.card.medium .card-value { color:#BA7517; }
.card.low    .card-value { color:#3B6D11; }

/* ── 分类统计小卡片 ───────────────────────── */
.cat-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; }
.cat-item {
  background:var(--color-background-secondary); border-radius:var(--border-radius-md);
  padding:10px 12px; display:flex; align-items:center; justify-content:space-between;
}
.cat-name  { font-size:12px; color:var(--color-text-secondary); }
.cat-count { font-size:14px; font-weight:500; }

/* ── 条形图 ───────────────────────────────── */
.bar-wrap { margin-top:10px; }
.bar-row  { display:flex; align-items:center; gap:10px; margin-bottom:7px; }
.bar-label { font-size:12px; color:var(--color-text-secondary); width:210px; flex-shrink:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.bar-bg   { flex:1; height:6px; background:var(--color-background-secondary); border-radius:3px; overflow:hidden; }
.bar-fill { height:100%; border-radius:3px; background:#EF9F27; }
.bar-fill.high { background:#E24B4A; }
.bar-num  { font-size:12px; font-weight:500; color:var(--color-text-primary); min-width:44px; text-align:right; }

/* ── 缺陷卡片 ────────────────────────────── */
.vuln-list { display:flex; flex-direction:column; gap:12px; }
.vuln-item {
  background:var(--color-background-primary);
  border:0.5px solid var(--color-border-tertiary);
  border-radius:var(--border-radius-lg); padding:16px 18px;
}
.vuln-item.high-risk   { border-left:3px solid #E24B4A; }
.vuln-item.medium-risk { border-left:3px solid #EF9F27; }
.vuln-header { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:8px; gap:12px; }
.vuln-name   { font-size:14px; font-weight:500; color:var(--color-text-primary); flex:1; }
.badge       { font-size:11px; font-weight:500; padding:3px 10px; border-radius:99px; white-space:nowrap; }
.badge.high  { background:#FCEBEB; color:#791F1F; }
.badge.medium{ background:#FAEEDA; color:#854F0B; }
.vuln-desc   { font-size:13px; color:var(--color-text-secondary); margin-bottom:10px; line-height:1.55; }

/* ── 代码块 ───────────────────────────────── */
.code-block {
  background:var(--color-background-secondary);
  border-left:3px solid var(--color-border-secondary);
  border-radius:0 6px 6px 0; padding:10px 14px;
  font-family:var(--font-mono); font-size:12px;
  color:var(--color-text-secondary); margin-bottom:10px;
  line-height:1.6; overflow-x:auto; white-space:pre;
}

/* ── 处理层级标签 ─────────────────────────── */
.advice-pills { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:8px; }
.pill         { font-size:11px; padding:3px 10px; border-radius:99px; border:0.5px solid var(--color-border-tertiary); color:var(--color-text-secondary); background:var(--color-background-secondary); }
.pill.framework { background:#E1F5EE; color:#0F6E56; border-color:#5DCAA5; }
.pill.scan      { background:#EEEDFE; color:#3C3489; border-color:#AFA9EC; }
.pill.code      { background:#FAEEDA; color:#633806; border-color:#EF9F27; }
.pill.config    { background:#FCEBEB; color:#791F1F; border-color:#F09595; }

/* ── 修复建议文本 ─────────────────────────── */
.advice-text { font-size:13px; color:var(--color-text-secondary); line-height:1.65; }
.advice-text li { margin-left:16px; margin-bottom:4px; }
.divider { border:none; border-top:0.5px solid var(--color-border-tertiary); margin:12px 0; }
.meta-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:14px; }
.meta-row { font-size:13px; }
.meta-key { color:var(--color-text-secondary); }
.meta-val { color:var(--color-text-primary); font-weight:500; }
</style>
```

## 区块 1：扫描概况

```html
<div class="section">
  <div class="section-title">扫描概况</div>
  <div class="meta-grid">
    <div class="meta-row"><span class="meta-key">项目名称：</span><span class="meta-val">XXX</span></div>
    <div class="meta-row"><span class="meta-key">扫描时间：</span><span class="meta-val">YYYY-MM-DD</span></div>
    <div class="meta-row"><span class="meta-key">文件数：</span><span class="meta-val">N 个</span></div>
    <div class="meta-row"><span class="meta-key">代码行数：</span><span class="meta-val">N 行</span></div>
  </div>
  <div class="cards">
    <div class="card high">
      <div class="card-label">高危 (High)</div>
      <div class="card-value">10</div>
      <div class="card-sub">需立即处理</div>
    </div>
    <div class="card medium">
      <div class="card-label">中危 (Medium)</div>
      <div class="card-value">2347</div>
      <div class="card-sub">优先整改</div>
    </div>
    <div class="card low">
      <div class="card-label">低危 (Low)</div>
      <div class="card-value">0</div>
      <div class="card-sub">暂无</div>
    </div>
    <div class="card">
      <div class="card-label">缺陷总数</div>
      <div class="card-value">2357</div>
      <div class="card-sub">密度 0.88‰</div>
    </div>
  </div>
</div>
```

## 区块 2：漏洞分类条形图

```html
<div class="section">
  <div class="section-title">中危缺陷 Top 分类</div>
  <div class="bar-wrap">
    <!-- width 百分比 = 该类数量 / 最大类数量 * 100% -->
    <div class="bar-row">
      <span class="bar-label">泛化的抛出异常</span>
      <div class="bar-bg"><div class="bar-fill" style="width:100%"></div></div>
      <span class="bar-num">457</span>
    </div>
    <!-- 更多行... -->
  </div>
</div>
```

## 区块 3：单条缺陷卡片（中危示例）

```html
<div class="vuln-item medium-risk">
  <div class="vuln-header">
    <span class="vuln-name">N. 缺陷名称</span>
    <span class="badge medium">中危 × 数量</span>
  </div>
  <div class="vuln-desc">简短描述（1-2句，说明危害）</div>
  
  <div style="font-size:12px;color:var(--color-text-secondary);margin-bottom:6px;">问题代码片段</div>
  <div class="code-block">// ❌ 文件名.java line XX
有问题的代码</div>

  <div style="font-size:12px;font-weight:500;color:var(--color-text-secondary);margin:10px 0 6px;">处理层级</div>
  <div class="advice-pills">
    <span class="pill code">代码层：具体措施</span>
    <span class="pill framework">框架层：下沉方案</span>
    <span class="pill scan">扫描：规则配置</span>
  </div>
  <div class="advice-text">
    <ul>
      <li><strong>代码层</strong>：具体修复步骤</li>
      <li><strong>框架层（下沉处理）</strong>：框架配置方案</li>
      <li><strong>扫描层</strong>：SonarQube/Checkmarx 规则</li>
    </ul>
  </div>

  <!-- 可选：推荐修复代码 -->
  <div class="divider"></div>
  <div style="font-size:12px;color:var(--color-text-secondary);margin-bottom:6px;">推荐修复代码</div>
  <div class="code-block">// ✅ 修复后代码
安全的实现方式</div>
</div>
```

## 高危卡片（加红色左边框）

```html
<div class="vuln-item high-risk">
  <div class="vuln-header">
    <span class="vuln-name">N. 高危漏洞名称</span>
    <span class="badge high">高危 × 数量</span>
  </div>
  <!-- 内容同上 -->
</div>
```

## loading_messages 建议

```python
# 扫描报告分析
loading_messages=["解析扫描数据...", "分类整理漏洞信息...", "生成统计图表..."]
```
