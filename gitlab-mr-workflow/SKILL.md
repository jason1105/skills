---
name: gitlab-mr-workflow
version: 0.3.0
author: Hermes
description: GitLab 自建 13.11 议题与 MR 全周期：建单、合并、评论、迁移。
metadata:
  hermes:
    tags: [Gitlab, Mr, Issues, Glab]
---

# GitLab 议题与 MR 操作（git.tsintergy.com:8070 / 13.11 / glab 1.100.x）

覆盖议题（issue）与 MR 全生命周期：建单、分支、建 MR、评论、合并、关闭、批量盘点、仓库迁移。本机为自建 GitLab 13.11，大量 API 行为与官方文档不同，以下均为实测口径。依赖 `glab` CLI（`terminal` 工具裸跑）＋ 无 glab 配置时的 git credential token 回退。

本文件只留每次都要用的规则与速查；场景细节在 `references/`，用 `skill_view(name='gitlab-mr-workflow', file_path='references/<文件>')` 按下表触发加载。

## When to Use

- 建/改/关 GitLab 议题，开/合/评 MR，查 CI 状态
- 「建个 issue」「开个 MR」「合了吧」「梳理现有议题」「评审这个 MR」
- 仓库迁移/换 group 后重定向 remote 与 MR
- glab 报错（panic / 空输出 / Unauthenticated / 400 / 404 / @file 落字面量）排障

### 触发加载表（场景 → 文件 → 内容）

| 触发场景 | 加载 | 内容一句话 |
|---|---|---|
| 建议题 / 开 MR 前定标题 | `title-prefix-code.md` | 类别×状态合法组合表、MR type 表、lint 用法 |
| 写多行/含反引号的正文 | `long-body-writing.md` | argv 直传代码、`@file`/`--input` 坑、字段名 |
| glab 报任何错 / 无 glab 配置 | `troubleshooting-glab.md` | 症状速查表、凭据回退、curl 建 MR |
| 合并前核验 / 堆叠 MR / 批量合并 / 「提交推送但不合并」「继续」类指令 | `pre-merge-checks.md` | merge-tree 预检、406 分诊、堆叠与推进纪律 |
| 合并后验证 / `glab mr merge` 报错 / push 与 MR 状态联动 / 误合并撤销 | `merge-verification.md` | API 回读、空 diff 与 merged 翻转机制、revert 三选 |
| merge-tree 干净但合并后挂 / 长期分支合 advanced main / 改名撞在途 MR | `advanced-merge-patterns.md` | 语义冲突、文档血统分叉、冲突块工具用法 |
| 处理评审意见 / 只读评审 / 行内评论 / 多轮改动与方向变更同步 | `review-response-loop.md` | 九步闭环、`+0 -0` 假象、四处记录同步 |
| 合并后清理本地分支与 worktree | `post-merge-cleanup.md` | worktree 先于分支、`-d` vs `-D`、证据纪律 |
| 梳理现有议题 / 关闭已完成议题 / 建后续可开发议题 / 沉淀结论进手册 | `issue-lifecycle.md` | 全量梳理产出形态、关单证据三形态、议题模板 |
| 仓库迁移 / 改名 / 换 group | `repo-migration.md` | 传输 vs 新建、MR 目标分支选择、旧 MR 只关不合 |
| 为独立议题开分支 / 镜像仓 PR 基线核对 / 未提交实现落成 MR | `branch-baseline.md` | 不从冻结分支开、PR 夹带外来提交修法 |
| 写 `.gitlab-ci.yml` / Pages / 定时流水线 | `ci-pages-quirks.md` | 13.11 无 `publish:`、两 job Pages 模式 |
| 建新仓 / 首次在新仓提交 | `repo-init-and-identity.md` | `glab repo create` 路径、作者邮箱核对、锁文件 |

## Prerequisites

- `glab` 1.100.x（Homebrew）已登录 `git.tsintergy.com:8070`（配置在 `~/Library/Application Support/glab-cli/config.yml`，非 `~/.config/`）
- `GITLAB_HOST=git.tsintergy.com:8070`（glab 默认 host 是 gitlab.com，不设会 Unauthenticated）
- 无 glab 配置时回退：`git credential fill`（host 须逐字 `git.tsintergy.com:8070`）取密码作 `PRIVATE-TOKEN`
- 在 `execute_code` 内跑 glab 用绝对路径 `/opt/homebrew/bin/glab`；自定义 env 必须带 `HOME`

## Quick Reference

```bash
# 议题（正文字段是 description，列表截断须单条 GET）
glab api "projects/<id>/issues?state=opened&per_page=100"          # 列表
glab api "projects/<id>/issues/<iid>"                              # 单条全量
glab api "projects/<id>/issues" -X POST -f title=... -f description=<正文>   # 建（argv 通道）
glab api "projects/<id>/issues/<iid>" -X PUT -f state_event=close  # 关
glab api "projects/<id>/issues/<iid>/notes" -X POST -f body=<正文> # note（字段是 body 不是 description！）
# MR
glab api "projects/<id>/merge_requests/<iid>"                      # 详情（state/sha/has_conflicts）
glab api "projects/<id>/merge_requests/<iid>/changes"              # 改动（13.11 无 /diffs）
glab mr merge <iid> --yes -R <ns>/<repo>                           # 合并（raw API POST 404 时走这条）
glab api "projects/<id>/merge_requests/<iid>" -X PUT -f target_branch=master  # retarget 堆叠 MR
# 冲突深检（git ≥2.38 新语法；旧语法 grep CONFLICT 恒假绿）
git merge-tree --write-tree --name-only origin/main origin/<branch>; echo $?
```

## Verification（合并后必查）

```bash
glab api "projects/<id>/merge_requests/<iid>" > /tmp/mr.json   # --jq 在部分上下文不可用,落文件后 python 解析
python3 -c "import json; d=json.load(open('/tmp/mr.json')); print(d['state'], d['merged_at'])"
# state=="merged" 且 merged_at 非空才算合并落地；否则重试再核
git fetch origin && git log origin/main --oneline -5                # 本地确认前移
```

**合并命令必须真的执行**：把合并命令写进回复文本而不调用 terminal / execute_code，会留下「已合并」的假记录。合并时每条命令都要实际调用工具。合并后报告里的 SHA 以 API 回读为准——曾出现报告的 merge SHA 是编造的，重做后要在议题/MR 评论里更正为真实 SHA。

## 修改流程红线：一律「议题 + MR」（用户指令 2026-09-12，适用于所有 GitLab 仓库）

用户明示「以后所有修改流程改为 议题 + MR」——**不再直接 push master**，即便是自己名下的小项目（如 llm-monitor）。流程：

1. 建议题：`glab api projects/<id>/issues -X POST -f title=... -f description=<正文>`（需求/验收清单/附带发现的 bug，末尾落款 `—— manager`）。用户口述的需求号可能是外部体系（禅道 story 号等），GitLab 仓里不存在同名 issue——先搜确认，搜不到就按本流程自建议题并把外部号写进标题/正文，别反复在 GitLab 里找
2. 从 `origin/master` 开分支：`git checkout -b fix/issue-<n>-<desc> origin/master`。**master 被其他 worktree 占用时 checkout 会报 `already used by worktree`，主仓也可能停在别的长命分支上**——不要动主仓，`git fetch origin master` 后在 scratch 目录 `git worktree add <scratch>/wt-master origin/master` 再从那里开分支干活；scratch worktree 里的未 push 分支会被闲置清理，收尾前必须 push
3. 改码 + 提交 + push 分支
4. 建 MR：`glab api projects/<id>/merge_requests -X POST -f source_branch=... -f target_branch=master -f title=... -f description=<正文>`，描述含改动说明、验证证据、落款。**描述必须写议题关联关键字（用户拍板：合并 MR 时一并关闭关联议题）**——交付完即关的写 `Closes #N`（合并自动关单），只关联不随关的写 `Relates #N`；漏写会导致合并后议题仍 open，只能手动 `PUT issues/<n> -f state_event=close` 补关并留 note 挂 MR 号补关联
5. **等用户明确说「可以合并」才合并**——先查 CI（`pipelines?ref=<branch>`）与 `has_conflicts=false`，通道=`glab mr merge <iid> --yes -R <ns>/<repo>`（raw API POST 404 不影响该 CLI 通道；部分仓复测可用，见症状表 merge 404 行）；`glab mr merge` 本身失败就停下报告，⛔ 绝不本地 merge + push 默认分支
6. 删除分支属破坏性操作，会被审批拦截——留给用户指示，不主动删

**堆叠 MR / 「提交推送但不合并」/ 「继续」类指令**的完整纪律见 `references/pre-merge-checks.md`（前置 MR 还开着、后续改动不能等；或用户限定只提交不合并）。

**提交信息走文件，别用 `-m` 内联（2026-09-13 实测的静默坑）**：`git commit -m "…含双引号/反引号…"` 会让 shell 把消息切成多个 pathspec，git 报 `error: pathspec 'xxx' did not match any file(s) known to git` 且**提交根本没发生**（随后 push 推的还是旧 HEAD）。凡提交信息含引号/反引号/多行，一律 `write_file /tmp/commit_msg.txt` + `git commit -F /tmp/commit_msg.txt`。MR/issue 描述走 `references/long-body-writing.md` 的 argv 通道。

**建新仓、或首次在一个新接手的仓里提交**：先看 `references/repo-init-and-identity.md`（`glab repo create` 可用路径；全局常缺 `user.email` 会让 committer 静默变成 `<用户名>@<主机名>.local`，首个 commit 前核对身份；Office 锁文件别进历史）。

## 议题收尾与标题规范

梳理现有议题、关闭已完成议题、建后续可开发议题、沉淀调查结论进手册——全量流程（产出形态、关单证据三形态、议题正文五段模板）见 `references/issue-lifecycle.md`。

**标题前缀码**（建议题 / 开 MR 前必查）：议题 `[类别][状态?] 摘要`、MR `type(scope): 摘要`；类别 × 状态并非任意组合，合法格与不适用时的改法见 `references/title-prefix-code.md`（用 `skill_view(name='gitlab-mr-workflow', file_path='references/title-prefix-code.md')` 加载）。建单前跑 `python3 scripts/title-lint.py issue|mr "<标题>"`，脚本直接解析该文件的组合表。

**长正文写入**（issue 正文 / MR 描述 / note）：`@file` 展开与 `--input` 在不同 build / 端点 / 会话之间不一致且失败是静默的（CLI 报成功，落库的是字面量 `@/path/body.md`）。可靠通道＝不经 shell，把正文作为单个 argv 元素传给 `glab api`；写后必读回字符数核对。字段名按端点不同：notes 只认 `body`，issue / MR 用 `description`，混用即 400。完整写法、python 通道、env 与 PATH 坑见 `references/long-body-writing.md`。

## Reference（迁移前既有的项目专属 reference）

以下 6 个是历史项目（chrome-show 等）沉淀的专属流程，触发场景见表内首列，一般任务不加载：`chrome-show-mr-collab.md`（群聊 MR-first 协作流程）、`planning-comment-workflow.md`（议题「待规划」转规划评论）、`gitlab-ci-writeback.md`（定时 CI 回写仓状态）、`parallel-impl-shared-checkout.md`（多 agent 并行 MR 共用检出）、`chrome-show-content-harness-quirks.md`（FakeNode 测试 harness 坑）、`regression-test-gate-handoff.md`（门禁条件通过+测试缺口补齐）、`pr-base-divergence-pollution.md`（GitHub 镜像 PR 基线分叉案例）、`badge-css-split-refactor-pattern.md`（大块逐字搬移重构模式）。

- `scripts/resolve_merge_conflicts.py` — 列出合并中全部冲突块（`--list`）并按 JSON 计划逐块解决（`main`/`head`/`both`/`custom`，尾部可 `append`）；计划漏块会响亮报错。配套流程（scope-parity diff、build、push、MR 刷新）见 `references/advanced-merge-patterns.md`。
- `scripts/title-lint.py` — 校验议题 / MR 标题前缀码，合法组合表解析自 `references/title-prefix-code.md`，改表即改规则。
