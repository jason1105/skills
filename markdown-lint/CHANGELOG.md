# markdown-lint 学习日志

## 2026-05-09 v1.12 — 初始创建

### 新增

- 【来源】：用户需求——需要一个可复用的 Markdown 格式检查工具
- 【改进】：创建独立的 markdown-lint skill，包含完整的执行步骤
- 【影响范围】：新增 skill，不影响现有其他 skill

**具体内容：**

- 检查并安装 markdownlint-cli2 工具
- 标准配置文件 `.markdownlint-cli2.jsonc` 生成
- 自动修复可修复的格式问题
- 结果报告和用户确认流程
- 常见问题处理说明

**配置的禁用规则说明：**

- MD013/line-length：技术文档常含长代码，禁用行长度限制
- MD024/no-duplicate-heading：CHANGELOG 等文档常用重复子标题
- MD025/single-title：允许多个 H1 标题
- MD033/no-inline-html：允许内嵌 HTML
- MD036/no-emphasis-as-heading：允许使用强调作为标题
- MD040/fenced-code-language：不强制代码块指定语言
- MD041/first-line-heading：不强制首行为标题
- MD060/table-column-style：禁用表格列风格检查
