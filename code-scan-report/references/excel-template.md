# Excel 报告生成模板

本文件提供生成扫描报告 Excel 的完整 Python 代码框架。
使用 openpyxl，生成后必须运行 `scripts/recalc.py` 重算公式。

## 依赖
```bash
pip install openpyxl --break-system-packages
```

## 通用辅助函数

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def cell_border():
    s = Side(style="thin", color="CCCCCC")
    return Border(left=s, right=s, top=s, bottom=s)

def set_cell(ws, row, col, value, bold=False, bg=None, font_color="000000",
             align="left", wrap=False, size=11):
    c = ws.cell(row=row, column=col, value=value)
    c.font = Font(name="Arial", bold=bold, color=font_color, size=size)
    if bg:
        c.fill = PatternFill("solid", start_color=bg, fgColor=bg)
    c.alignment = Alignment(horizontal=align, vertical="center", wrap_text=wrap)
    c.border = cell_border()
    return c
```

## Sheet 1：扫描概况

```python
ws1 = wb.active
ws1.title = "扫描概况"

# 标题行（深蓝背景，跨列合并）
ws1.merge_cells("A1:F1")
c = ws1["A1"]
c.value = "项目名称  代码安全扫描报告"
c.font = Font(name="Arial", bold=True, size=14, color="FFFFFF")
c.fill = PatternFill("solid", start_color="1F3864", fgColor="1F3864")
c.alignment = Alignment(horizontal="center", vertical="center")
ws1.row_dimensions[1].height = 36

# 元信息区（从第3行开始，key-value 两列，右侧合并）
meta = [
    ("项目名称", scan_info["project"]),
    ("检测时间", scan_info["date"]),
    ("检测工具", scan_info["tool"]),
    ("检测语言", scan_info["language"]),
    ("文件数",   str(scan_info["files"]) + " 个"),
    ("代码行数", f'{scan_info["loc"]:,} 行'),
    ("缺陷密度", scan_info["density"]),
]
for i, (k, v) in enumerate(meta, start=3):
    set_cell(ws1, i, 1, k, bold=True, bg="D9E1F2", align="center")
    ws1.merge_cells(f"B{i}:F{i}")
    set_cell(ws1, i, 2, v, bg="EEF2FA")
    ws1.row_dimensions[i].height = 22

# 等级统计表（第11行起）
ws1.merge_cells("A11:F11")
set_cell(ws1, 11, 1, "等级统计", bold=True, bg="1F3864",
         font_color="FFFFFF", align="center", size=12)
ws1.row_dimensions[11].height = 28

# 表头
hdrs = ["等级", "数量", "占比 %", "状态", "说明", ""]
for j, h in enumerate(hdrs, 1):
    set_cell(ws1, 12, j, h, bold=True, bg="2E75B6",
             font_color="FFFFFF", align="center")

# 数据行
severity_rows = [
    ("高危", severity_counts["high"],   f'{severity_counts["high"]/severity_counts["total"]*100:.2f}%', "需立即处理", "命令注入/XXE/XSS 等"),
    ("中危", severity_counts["medium"], f'{severity_counts["medium"]/severity_counts["total"]*100:.2f}%', "优先整改",   "路径穿越/异常处理/信息泄露等"),
    ("低危", severity_counts["low"],    "0%",                                                              "暂无",       "-"),
]
level_bg = ["C00000", "ED7D31", "70AD47"]
for i, (lv, cnt, pct, sts, desc) in enumerate(severity_rows, start=13):
    set_cell(ws1, i, 1, lv, bold=True, bg=level_bg[i-13],
             font_color="FFFFFF", align="center")
    set_cell(ws1, i, 2, cnt, align="center")
    set_cell(ws1, i, 3, pct, align="center")
    set_cell(ws1, i, 4, sts, align="center")
    ws1.merge_cells(f"E{i}:F{i}")
    set_cell(ws1, i, 5, desc)
    ws1.row_dimensions[i].height = 22

# 合计行（使用公式）
set_cell(ws1, 16, 1, "合计", bold=True, bg="D9D9D9", align="center")
c = ws1.cell(row=16, column=2, value="=SUM(B13:B15)")
c.font = Font(name="Arial", bold=True)
c.fill = PatternFill("solid", start_color="D9D9D9", fgColor="D9D9D9")
c.alignment = Alignment(horizontal="center", vertical="center")
c.border = cell_border()
set_cell(ws1, 16, 3, "100%", bold=True, bg="D9D9D9", align="center")
ws1.row_dimensions[16].height = 22

# 列宽
for col, w in zip("ABCDEF", [14, 10, 12, 18, 40, 10]):
    ws1.column_dimensions[col].width = w
```

## Sheet 2：缺陷分析

```python
ws2 = wb.create_sheet("缺陷分析")

# 标题
ws2.merge_cells("A1:J1")
c = ws2["A1"]
c.value = "代码安全缺陷分析表"
c.font = Font(name="Arial", bold=True, size=13, color="FFFFFF")
c.fill = PatternFill("solid", start_color="1F3864", fgColor="1F3864")
c.alignment = Alignment(horizontal="center", vertical="center")
ws2.row_dimensions[1].height = 34

# 表头
headers = ["序号","缺陷名称","等级","数量","受影响文件（示例）",
           "问题代码片段","修复建议（代码层）","修复建议（框架/扫描层）",
           "OWASP/CWE 映射","优先级"]
for j, h in enumerate(headers, 1):
    set_cell(ws2, 2, j, h, bold=True, bg="2E75B6",
             font_color="FFFFFF", align="center")
ws2.row_dimensions[2].height = 26

# 颜色常量
HIGH_BG = "FCE4E4"
MED_BG  = "FFF2CC"
LEVEL_COLORS = {"高危": ("C00000","FFFFFF"), "中危": ("ED7D31","FFFFFF"), "低危": ("70AD47","FFFFFF")}
PRIORITY_COLORS = {"P0 立即修复": "C00000", "P1 优先修复": "ED7D31", "P2 分批处理": "70AD47"}

# 数据行（每个 defect 对应一行）
for i, d in enumerate(defects, start=3):
    row_bg = HIGH_BG if d["level"] == "高危" else MED_BG
    row_data = [d["id"], d["name"], d["level"], d["count"],
                d["affected_files"], d["code_snippet"],
                d["fix_code"], d["fix_framework"],
                d["owasp_cwe"], d["priority"]]
    for j, val in enumerate(row_data, 1):
        c = set_cell(ws2, i, j, val, bg=row_bg, wrap=True)
        # 序号居中
        if j == 1:
            c.alignment = Alignment(horizontal="center", vertical="center")
        # 等级着色
        if j == 3:
            lc, fc = LEVEL_COLORS.get(val, ("FFFFFF","000000"))
            c.fill = PatternFill("solid", start_color=lc, fgColor=lc)
            c.font = Font(name="Arial", bold=True, color=fc, size=11)
            c.alignment = Alignment(horizontal="center", vertical="center")
        # 数量居中加粗
        if j == 4:
            c.alignment = Alignment(horizontal="center", vertical="center")
            c.font = Font(name="Arial", bold=True, size=11)
        # 优先级着色
        if j == 10:
            pc = PRIORITY_COLORS.get(val, "FFFFFF")
            c.fill = PatternFill("solid", start_color=pc, fgColor=pc)
            c.font = Font(name="Arial", bold=True, color="FFFFFF", size=11)
            c.alignment = Alignment(horizontal="center", vertical="center",
                                    wrap_text=True)
    ws2.row_dimensions[i].height = 90

# 列宽
col_widths = [6, 22, 10, 8, 32, 40, 40, 38, 26, 16]
for j, w in enumerate(col_widths, 1):
    ws2.column_dimensions[get_column_letter(j)].width = w

ws2.freeze_panes = "A3"
```

## Sheet 3：修复优先级看板

```python
ws3 = wb.create_sheet("修复优先级看板")

ws3.merge_cells("A1:G1")
c = ws3["A1"]
c.value = "修复优先级看板"
c.font = Font(name="Arial", bold=True, size=13, color="FFFFFF")
c.fill = PatternFill("solid", start_color="1F3864", fgColor="1F3864")
c.alignment = Alignment(horizontal="center", vertical="center")
ws3.row_dimensions[1].height = 32

prio_hdrs = ["优先级","缺陷类别","等级","数量","核心修复方向","责任层级","建议完成时限"]
for j, h in enumerate(prio_hdrs, 1):
    set_cell(ws3, 2, j, h, bold=True, bg="2E75B6",
             font_color="FFFFFF", align="center")
ws3.row_dimensions[2].height = 24

# prio_rows: list of (优先级, 类别, 等级, 数量, 修复方向, 责任层级, 时限)
P_BG = {"P0\n立即修复":"C00000","P1\n优先修复":"ED7D31","P2\n分批处理":"70AD47"}
ROW_BG = {"P0\n立即修复":"FCE4E4","P1\n优先修复":"FFF2CC","P2\n分批处理":"EBF5EB"}

for i, row in enumerate(prio_rows, start=3):
    bg_row = ROW_BG.get(row[0], "FFFFFF")
    for j, val in enumerate(row, 1):
        c = set_cell(ws3, i, j, val, bg=bg_row, wrap=True)
        if j == 1:
            pc = P_BG.get(val, "FFFFFF")
            c.fill = PatternFill("solid", start_color=pc, fgColor=pc)
            c.font = Font(name="Arial", bold=True, color="FFFFFF", size=11)
            c.alignment = Alignment(horizontal="center", vertical="center",
                                    wrap_text=True)
        if j == 3:
            lc = {"高危":"C00000","中危":"ED7D31"}.get(val,"FFFFFF")
            c.fill = PatternFill("solid", start_color=lc, fgColor=lc)
            c.font = Font(name="Arial", bold=True, color="FFFFFF", size=11)
            c.alignment = Alignment(horizontal="center", vertical="center")
        if j == 4:
            c.alignment = Alignment(horizontal="center", vertical="center")
            c.font = Font(name="Arial", bold=True, size=11)
        if j == 7:
            c.alignment = Alignment(horizontal="center", vertical="center",
                                    wrap_text=True)
    ws3.row_dimensions[i].height = 44

for j, w in enumerate([14, 22, 10, 8, 44, 16, 16], 1):
    ws3.column_dimensions[get_column_letter(j)].width = w

ws3.freeze_panes = "A3"
```

## 保存与重算

```python
out_path = "/home/claude/output_scan_report.xlsx"
wb.save(out_path)

import subprocess
result = subprocess.run(
    ["python", "/mnt/skills/public/xlsx/scripts/recalc.py", out_path],
    capture_output=True, text=True
)
print(result.stdout)  # 检查 status: success / errors_found

import shutil
shutil.copy(out_path, "/mnt/user-data/outputs/xxx_scan_report.xlsx")
```
