---
name: cross-agent-skill-ops
version: "1.0.0"
author: lvwei
license: MIT
description: Use when 建跨 agent 共享 skill、误说 plugin、或 skill 找不到时。
metadata:
  hermes:
    tags: [skills, multi-agent, plugin, symlink]
    related_skills: [hermes-agent]
---

# 跨 agent skill 布局与维护

## When to Use

- 用户要求某 skill「适用于 cc/codex/grok/cursor」或「做成 plugin 提供多个 skill」
- skill_manage 报 `Skill not found` 但此前见过它（正本已迁、软链断开）
- 同一 skill 需要在多个 agent 间保持单一代码源
- 做 skills 管理/迁移/分发方案（盘点归属、定哪些入仓）

## 盘点归属的取证方法（判断「自有 vs 外装」不能只看安装标记）

`.bd-meta.json`/skill-lock 类安装标记只证明「从某处安装过」，不证明「别人写的」。给 skill 定归属（迁个人仓/留安装层/归公司仓）时逐层取证：

1. **读 meta 的 path 字段**拿到源仓目录名，再 `mdfind -name <源仓名>` 或 `search_files(target='files')` 找本机源仓
2. **查源仓 git**：`git log --format='%an %ae'` 看作者是不是用户本人；`git log --all --oneline -- <skill>/` 查全历史（注意分支——skill 可能被挪到独立 feature 分支而非删除，`git branch -a` 全看）
3. **三目录存在性比对**（~/.agents / ~/.claude / 源仓）：先 `-d` 测存在性再 diff——不要对不存在的路径跑 `diff -rq | wc -l`，报错行被计数后「差异 0」会被误读成「两侧一致」（实踩：把「两边都没有」当成「内容相同」得出了错误归属结论）
4. **内容侧写**：grep SKILL.md 里的 github/gitlab/agentskill.sh 源链接、agent 工具名痕迹（`.Codex` vs `claude` 路径写法能暴露哪个 agent 的变体）、作者字段
5. **mtime 批次**：多个 skill 同一分钟 mtime ＝ 一次批量安装/迁移操作，可用来归批

典型判定：同一 skill 在公司仓有 commit 且作者是用户 ＝ 自研公司资产（上游真相源在公司仓，个人仓只做备份镜像）；公司仓全历史零 commit 且只存在于个人目录 ＝ 纯个人自研；SKILL.md 有第三方 repo 链接 ＝ 社区外装。同 skill 在 ~/.claude 与 ~/.agents 双份且差异仅为工具名适配（`~/.claude/skills/` ↔ `~/.Codex/skills/`）＝ 旧的「每 agent 一份拷贝」分发模式残留，收仓时统一为 open 标准写法（不硬编码 agent 专属路径）后废弃拷贝。

## skills 分发三层架构（用户已定）

源码层（开发+版本）→ 安装层（使用）→ 接入层（发现）。用户仓库：`~/MyProjects/lvwei/ai/skills`，远端 `github.com/jason1105/skills`，结构 `<skill-name>/SKILL.md` 平铺。

- **核心原则：仓库是唯一真相源，安装目录是生成物**。自有 skill 一律在仓库改，`npx skills add <本地仓路径> -g --skill <name>` 本地装回实测，满意后 commit+push+tag；不手改 `~/.agents/skills/` 里的已安装副本（update 会覆盖，手改即造分叉）
- **`npx skills` CLI**（vercel-labs/skills）：`find` 找、`add owner/repo[@tag] [--skill n] [-a agent]` 装（会检测本机 agent 供勾选）、`list`/`check`/`update`/`remove` 管、`use` 试用不装；cc/codex/cursor/hermes-agent/grok 全在官方支持列表（Hermes 全局位就是 `~/.hermes/skills/`）
- **项目级 vs 全局**：团队 skill 放 `<project>/.agents/skills/`（随 git 分发不走 CLI）；个人的放全局。两条通道不混
- **内外双仓**：公司专属 skill（tsin/gzjy 系）只进内网 GitLab；个人通用 skill GitHub 为上游。「个人写、公司用」的 skill 可经用户明示豁免后以备份镜像身份进个人仓（标注公司仓为上游真相源）
- **分发阈值**：用过 2 次以上、version ≥1.0、无本机绝对路径硬编码才发布
- **外部 skill 的本地魔改会被 update 冲掉**——魔改过的 fork 成自有仓再装
- 详细方案文档：`blogs/Tools/skills 管理方案.md`（含迁移清单判定表）

## 核心事实（先核实再引用）

各 agent 的 plugin 机制互不互通：cc 走 plugin marketplace、codex 走 `[plugins."]` 配置、grok 是 bundled plugins——plugin 是**工具/hook 扩展**（如 ~/.hermes/plugins/ 下 plugin.yaml 那种），不是 skill 的打包形态。用户说「一个 plugin 提供两个 skill」时，落地等价物是**同一目录下的姊妹 skill**：装一次、两个能力、互相引用。skill 是唯一跨 cc/codex/grok/cursor/hermes 的复用载体。

skill 发现机制（实测）：grok 原生扫 `~/.agents/`、`~/.grok/`、`~/.claude/`、`~/.cursor/` 四目录；cc 读 `~/.claude/skills/`；codex 读 `~/.codex/skills/`；Hermes 读 `~/.hermes/skills/<category>/<name>/`（唯一带 category 子目录）。`~/.agents/skills/` 是跨 agent 共享标准位（open SKILL.md 格式各家通用）。

## 布局与维护流程（repo-first 新常态）

1. **正本＝仓库** `~/MyProjects/lvwei/ai/skills/<name>/`（平铺无 category；frontmatter 用 open 标准 name+description，Hermes 专属 metadata.hermes 等扩展字段无害保留）。`~/.agents/skills/` 里属于自己的条目已是 CLI 装的生成物，不再手放正本。
2. **改自有 skill**：仓库改 → `npx skills add ~/MyProjects/lvwei/ai/skills -g --skill <name>` 装回实测 → commit/push；机器间同步 `npx skills update -g`。
3. **跨 agent 分发**：`npx skills add <repo> -g` 勾选 agent。实测接入形态：cc/grok/hermes 得各自目录软链；**codex/cursor 走 ~/.agents 共享位、不建独立目录**——验证 cursor 别去 ls ~/.cursor/skills（空是正常），查 ~/.agents/skills/。
4. **仅本地临时接入**（不入仓）才手工软链：`ln -s ../../.agents/skills/<name> ~/.claude/skills/<name>`；Hermes 带 category 时 `ln -s ../../../.agents/skills/<name> ~/.hermes/skills/<category>/<name>`。
5. **skill 间引用写纯文本**——related_skills 元数据是 Hermes 专属，别依赖它传跨 agent 语义。
6. **skill_manage 管不到 CLI 装的软链 skill**（报 not found 但 skill_view 可读）：这是注册表边界不是 skill 丢失；直接改仓库正本再重装，别在 ~/.hermes 下重建造成双正本。

## 坑

- **rm 目录后立即 ln 可能没删干净**：Finder 占用等原因，软链会建进残留目录内部（目录里出现同名链）。ln 前 `readlink` 验证目标不存在，建完 `readlink` + `diff -q` 确认指向正本。
- **skill_manage 的 not found ≠ skill 不存在**：它只管 active profile 的 skills 树（~/.hermes/skills），正本在 ~/.agents 且 Hermes 链未挂时报 not found——先 ls 软链，别重建 skill 造成双正本。
- **Hermes 系统技能树刷新有延迟**：新建/改链后当前会话的 skills_list 可能仍看不到，下个会话才出现；当前会话要用就直接读正本路径执行。
