---
name: markdown-lint
description: >
  使用 markdownlint-cli2 检查并修复目录下所有 Markdown 文件的格式问题。
  当用户要求检查 Markdown 格式、lint md 文件、修复 Markdown 格式、运行 markdownlint 时触发。
  父 skill：独立工具，可被其他 skill 调用或直接由用户触发。
---

# Markdown Lint

## 目标

使用 markdownlint-cli2 工具检查并修复目录下所有 Markdown（.md）文件的格式问题，确保文档格式一致性和规范性。

## 产出物充分性要求

**执行完成后必须满足：**

- 所有 Markdown 文件通过 lint 检查（0 errors）
- 自动修复可修复的格式问题
- 生成标准的 `.markdownlint-cli2.jsonc` 配置文件（如不存在）
- 输出清晰的检查结果摘要供用户确认

## 适用场景

- 用户要求检查 Markdown 格式
- 代码提交前的文档格式校验
- 批量修复 Markdown 格式问题
- 新项目初始化 Markdown 规范

## 执行步骤

### Step 1: 检查并安装 markdownlint-cli2

1. 检查是否已安装 markdownlint-cli2：
   ```bash
   npm list -g markdownlint-cli2
   ```

2. 如未安装，执行全局安装：
   ```bash
   npm install -g markdownlint-cli2
   ```

### Step 2: 创建或更新配置文件

1. 检查当前目录是否存在 `.markdownlint-cli2.jsonc` 配置文件

2. 如不存在，创建标准配置文件：
   ```jsonc
   {
     "config": {
       "default": true,
       "MD013": false,
       "MD024": false,
       "MD025": false,
       "MD033": false,
       "MD036": false,
       "MD040": false,
       "MD041": false,
       "MD060": false
     },
     "globs": ["**/*.md"],
     "ignores": ["node_modules", ".git", ".wolf"]
   }
   ```

**配置说明：**
- `MD013/line-length`：禁用行长度限制（技术文档常含长代码）
- `MD024/no-duplicate-heading`：允许重复标题（CHANGELOG 常用相同子标题）
- `MD025/single-title`：允许多个一级标题
- `MD033/no-inline-html`：允许内嵌 HTML
- `MD036/no-emphasis-as-heading`：允许使用强调作为标题
- `MD040/fenced-code-language`：不强制代码块指定语言
- `MD041/first-line-heading`：不强制首行为标题
- `MD060/table-column-style`：禁用表格列风格检查

### Step 3: 运行 lint 检查（无修复）

1. 在目标目录执行：
   ```bash
   markdownlint-cli2 "**/*.md" "#node_modules" "#.git" "#.wolf"
   ```

2. 记录初始错误数量和主要问题类型

### Step 4: 自动修复可修复的问题

1. 执行自动修复：
   ```bash
   markdownlint-cli2 --fix "**/*.md" "#node_modules" "#.git" "#.wolf"
   ```

2. 修复范围包括：
   - 标题前后的空行（MD022）
   - 列表前后的空行（MD032）
   - 代码块前后的空行（MD031）
   - 连续多行空行（MD012）
   - 有序列表前缀格式（MD029）

### Step 5: 再次检查并报告结果

1. 重新运行 lint 检查确认剩余问题：
   ```bash
   markdownlint-cli2 "**/*.md" "#node_modules" "#.git" "#.wolf"
   ```

2. 向用户报告结果：
   - 初始发现的错误数量
   - 自动修复的错误数量
   - 剩余的错误数量（如仍有）
   - 修改的文件列表
   - 新增的配置文件（如创建）

### Step 6: 用户确认

1. 展示变更摘要供用户确认
2. 询问是否提交变更
3. 如需进一步调整配置，根据用户反馈更新

## 常见问题处理

### npm 不可用

如果系统未安装 npm，提示用户先安装 Node.js：
- macOS: `brew install node`
- Linux: 使用对应包管理器安装 nodejs
- Windows: 从官网下载安装

### 配置文件已存在

如果目录已有配置文件，不覆盖原有配置，直接使用现有配置执行检查。

### 权限问题

如遇到文件写入权限问题，提示用户检查文件权限或使用 sudo。

## 验收标准

- ✅ markdownlint-cli2 工具已安装或可用
- ✅ 配置文件 `.markdownlint-cli2.jsonc` 存在（或使用已有配置）
- ✅ 执行 `markdownlint-cli2` 检查结果为 0 errors
- ✅ 所有可自动修复的问题已被修复
- ✅ 用户已确认变更结果

## 关联 skill

- 可被 `backend-dev` 等父 skill 在各阶段结束前调用，做文档格式校验
- 可作为代码提交前的质量门禁步骤
