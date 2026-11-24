# jason1105/skills

个人跨 agent skills 主仓（Claude Code / Codex / Grok Build / Cursor / Hermes Agent / 其他经 `~/.agents/skills/` 共享位的 agent）。

本仓**同时是 `~/.agents/skills/` 的工作副本**：本机所有 agent 的全局 skill 都从这里发现；本地改完 `git diff` 直接可见差异，提交推送即分发（`npx skills add jason1105/skills`）。

## 目录速览

### 自有 skill（本仓维护）

| 分类 | skill |
|---|---|
| PRD 工具链 | prd-parser → prd-detail-design → prd-interactive-prototype → prd-review（基准 rules/PRD编写规则.md）；prd-source-baseline |
| 后端流水线 | backend-dev（父）+ backend-api/ddl/detailed-design/implementation/quality-gate/requirement-breakdown/verification/artifact-summary、markdown-lint（镜像备份：上游＝公司仓 devcenter/ai-code/skills，以本仓镜像为准时需回流公司仓） |
| 跨 agent 协作 | cross-agent-skill-ops、calling-hermes、calling-deepseek-harness、calling-opencode、calling-openhands |
| GitLab 接入 | check-gitlab、install-gitlab |
| 汇报与表达 | ste（ASD-STE100）、explaining-for-understanding |
| 文档与方法 | code-scan-report、update-skill、dingding-doc-parse、2red-product-whitepaper、web-learning-methodology、workflow-model-strategy |

### 仅本机安装（不入仓，见 .gitignore）

- 无（四角色流水线已于 2026-11-24 删除，历史见 git log 951787f 前的 commit，废纸篓可恢复）
- find-skills、last30days、majiayu000-backend-design-review、orca-cli（托管勿动）、product-monster-featurelist、product-monster-prd、web-perf、performance-optimization（外来/CLI 管理）

## 约定

- 改 skill → 本仓 commit → push（远端 `jason1105/skills`，旧名 my-skills 同仓重定向）
- 外来 skill 由各自来源更新（`npx skills update`），不手改；魔改过的应 fork 入本仓
- backend 套若在公司仓也有维护，改哪边哪边为准，同步时注明方向
