# 数据提取指南

## Checkmarx 报告（英文，如浙江项目）

### 元信息定位
```bash
# 扫描概况在报告开头
grep -A 20 "Project Name\|Scan Start\|Lines Of Code" /tmp/report.txt | head -30
```

关键字段：
- `Project Name` — 项目名
- `Scan Start` — 扫描日期
- `Lines Of Code Scanned` — 代码行数
- `Files Scanned` — 文件数
- `Checkmarx Version` — 工具版本
- `Density` — 缺陷密度（格式：`6/10000`）

### 等级统计
```bash
grep -A 10 "Results Distribution By Status\|New Issues" /tmp/report.txt
```
字段：`High / Medium / Low / Information / Total`

### 漏洞分类列表
```bash
grep -A 5 "Result Summary" /tmp/report.txt | grep -v "^$"
```
每行格式：`漏洞类型名称    数量    严重程度`

### 单条漏洞详情
```bash
# 找到具体章节
grep -n "Query Path:\|Code Snippet\|Severity.*Medium\|File Name" /tmp/report.txt | head -40
# 然后用 sed -n 'START,ENDp' 读取完整片段
```

---

## CEPRI 报告（中文，如湖南项目）

### 水印处理
CEPRI 报告 PDF 含旋转水印文字："心有限数据中" 等字符，提取时忽略以下单字片段：
`心`、`有`、`限`、`数`、`据`、`中` （单独成行的）

### 元信息定位
```bash
sed -n '/1\.1 源代码信息/,/第.*页/p' /tmp/report.txt | head -20
```
字段：创建者、检测开始/结束时间、检测语言、检测模板、文件数、源代码行数

### 等级统计
```bash
sed -n '/1\.2 等级统计/,/第.*页/p' /tmp/report.txt | head -15
```
格式：
```
等级    数量    所占 %
高危     10      0.42
中危   2347     99.58
低危      0        0
缺陷总数          2357
缺陷密度          0.88‰
```

### 分类统计表
```bash
sed -n '/1\.3 分类统计/,/1\.4/p' /tmp/report.txt
```
格式：`一级分类  二级分类  高危数量  中危数量  低危数量  合计`

获取章节列表：
```bash
grep -n "^2\.[0-9]\+\.[0-9]\+" /tmp/report.txt
```
每节格式：`2.x.y  一级分类：xxx  二级分类：yyy  数量：N`

### 单条缺陷详情
```bash
# 定位章节
grep -n "2\.2\.6\|2\.1\.1" /tmp/report.txt

# 读取章节内容（从开始到下一章节）
sed -n 'STARTp,ENDp' /tmp/report.txt
```

关注：
- `数量：N` — 出现次数
- `**例[0-9]**` 或 `爆发行代码：` — 问题代码
- `修复建议：` — 修复方案
- `缺陷[0-9]【审计状态：高/中】` — 具体实例（含文件名、行号）

---

## 通用数据结构

提取完成后，在内存中组织为以下结构再生成报告：

```python
scan_info = {
    "project": "项目名",
    "date": "扫描日期",
    "tool": "工具名称",
    "language": "Java",
    "files": 5934,
    "loc": 2664950,
    "density": "0.88‰",
}

severity_counts = {
    "high": 10,
    "medium": 2347,
    "low": 0,
    "total": 2357,
}

# 漏洞列表，每项对应 Excel 一行
defects = [
    {
        "id": 1,
        "name": "命令注入\n(OS Command Injection)",
        "level": "高危",        # 高危 / 中危 / 低危
        "count": 5,
        "affected_files": "PowerModelServiceImpl.java\nL200, L232",
        "code_snippet": "Runtime.exec(\"rm -f \" + netId)",
        "fix_code": "使用 Files.deleteIfExists(path)；\n正则校验 netId 格式",
        "fix_framework": "封装 SecurePathUtils；ArchUnit 规则",
        "owasp_cwe": "CWE-78\nOWASP A3:2021 Injection",
        "priority": "P0 立即修复",   # P0 / P1 / P2
    },
    # ...
]
```
