---
name: code-scan-report
description: >
  分析代码安全扫描报告（Checkmarx、CEPRI 检测工具等），生成包含统计图表、逐条缺陷分析、
  错误代码片段和修复建议的可视化报告与 Excel 文件。当用户上传扫描报告 PDF、提及代码扫描、
  漏洞分析、安全检测报告、缺陷报告或要求分析扫描结果时，必须使用本 skill。
  同样适用于：生成安全报告 Excel、将扫描报告转为可视化分析、提取扫描统计数据、
  对比多个项目的扫描结果。
---

# 代码安全扫描报告分析 Skill

本 skill 指导如何将代码扫描工具（Checkmarx、CEPRI 全量检测模板等）输出的 PDF 报告，
转化为带可视化图表的在线报告与结构化 Excel 文件。

## 工作流程总览

```
1. 读取 PDF → 2. 提取统计数据 → 3. 渲染可视化 Widget → 4. 生成 Excel → 5. 输出文件
```

---

## Step 1：读取 PDF

先用 `pdfinfo` 检查页数，再用 `pdftotext -layout` 提取全文：

```bash
pdfinfo "report.pdf"
pdftotext -layout "report.pdf" /tmp/report.txt
wc -l /tmp/report.txt
```

然后用 `grep` + `sed` 定位关键段落：

```bash
# 定位等级统计表
grep -n "高危\|中危\|低危\|缺陷总数\|High\|Medium\|Low" /tmp/report.txt | head -30

# 定位漏洞分类列表
grep -n "分类\|Vulnerability Type\|Query Path\|Result Summary" /tmp/report.txt | head -30

# 定位各类缺陷的章节行号
grep -n "^2\.[0-9]\|^[0-9]\+\.[0-9]\+\." /tmp/report.txt | head -60
```

**注意**：CEPRI 报告存在水印文字干扰（如"心有限数据中"），提取时需忽略这些片段。

---

## Step 2：提取核心数据

需要提取以下信息，详见 `references/data-extraction.md`：

| 数据项 | 说明 |
|--------|------|
| 扫描元信息 | 项目名、时间、工具版本、文件数、代码行数 |
| 等级统计 | 高危/中危/低危数量及占比、缺陷密度 |
| 分类统计 | 每种漏洞类型的名称、等级、数量 |
| 缺陷详情 | 每类缺陷的：描述、爆发行代码、修复建议 |

**Checkmarx 报告**关注：`Result Summary` 表格（漏洞类型/数量/严重程度）  
**CEPRI 报告**关注：`1.2 等级统计` + `1.3 分类统计` + `2.x 详细信息`

---

## Step 3：渲染可视化 Widget

使用 `visualize:show_widget` 工具渲染内联报告，详细模板见 `references/widget-template.md`。

Widget 应包含以下区块（从上到下）：

1. **扫描概况卡片区** — 4 列卡片：高危/中危/低危/总数，含项目元信息网格
2. **高危缺陷分类** — 小卡片网格，展示高危漏洞各子类数量（若无高危可跳过）
3. **中危 Top 分类** — 横向条形图，按数量降序展示前 10 类
4. **缺陷详细分析列表** — 每个漏洞一张卡片，包含：
   - 漏洞名称 + 等级徽章（高危红边/中危黄边）
   - 漏洞描述（1-2句）
   - 问题代码片段（`code-block` 样式，含 `❌` 注释）
   - 处理层级标签（框架层绿色/代码层橙色/扫描层紫色/配置层红色）
   - 修复建议列表
   - 推荐修复代码（可选，当修复逻辑非显然时提供）

---

## Step 4：生成 Excel

使用 openpyxl 生成三个 Sheet，详细代码见 `references/excel-template.md`：

### Sheet 1：扫描概况
- 标题行（深蓝背景白字）
- 元信息网格（2列，key-value）
- 等级统计表（高危红/中危橙/低危绿，含合计公式 `=SUM(B13:B15)`）

### Sheet 2：缺陷分析（核心）
每行一种缺陷，列定义如下：

| 列 | 内容 | 宽度 |
|----|------|------|
| A | 序号 | 6 |
| B | 缺陷名称（含换行） | 22 |
| C | 等级（颜色填充） | 10 |
| D | 数量 | 8 |
| E | 受影响文件（示例） | 32 |
| F | 问题代码片段 | 40 |
| G | 修复建议（代码层） | 40 |
| H | 修复建议（框架/扫描层） | 38 |
| I | OWASP/CWE 映射 | 26 |
| J | 优先级 | 16 |

- 高危行底色：`FCE4E4`；中危行底色：`FFF2CC`
- 等级列：高危 `C00000` 白字；中危 `ED7D31` 白字
- 优先级列：P0 `C00000`、P1 `ED7D31`、P2 `70AD47`，均白字
- 行高 90，开启 `wrap_text=True`，`freeze_panes="A3"`

### Sheet 3：修复优先级看板
- 按 P0/P1/P2 分组汇总
- 列：优先级、缺陷类别、等级、数量、核心修复方向、责任层级、建议完成时限

生成后必须运行公式重算：
```bash
python /mnt/skills/public/xlsx/scripts/recalc.py output.xlsx
```

---

## Step 5：输出文件

```python
import shutil
shutil.copy("/home/claude/output.xlsx", "/mnt/user-data/outputs/xxx_scan_report.xlsx")
```

调用 `present_files` 提供下载链接。如用户同时需要 HTML 文件，参考 `references/html-artifact.md`。

---

## 修复建议通用框架

为每类漏洞提供**三个层面**的修复建议：

```
代码层    → 直接修改代码（最细粒度）
框架层    → 下沉到框架/中间件统一处理（推荐，减少重复）
扫描层    → 在扫描工具/CI 中配置规则或标记误报
```

各漏洞类型的标准处理方式见 `references/vuln-fix-patterns.md`。

---

## 命名规范

输出文件统一命名：`{项目简称}_scan_report.xlsx / .html`  
Widget title 使用：`{项目简称}_scan_report`（snake_case）

## 缺陷展示粒度：必须询问用户

在生成 Widget 和 Excel 之前，若报告中存在**数量较多、子类繁杂的低危/信息级缺陷**（子类 ≥ 8 种或总数 ≥ 50 条），必须先向用户提问，不得自行决定合并或省略：

> "检测到低危缺陷共 N 种子类（共 M 条），请问展示方式：
> 1. 逐一展开每种子类（完整版）
> 2. 按一级分类合并归组展示（精简版）
> 请选择 1 或 2？"

- 用户选择 **1**：每种子类单独一张卡片，不得合并。
- 用户选择 **2**：相似子类合并为大类，卡片末尾注明"已合并 N 个子类"及各子类名称与数量。
- **无论哪种选择，均不得静默省略任何缺陷类型。**
