---
name: gitlab-mr-workflow
version: 0.2.0
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

| 触发场景 | 加载 |
|---|---|
| 写多行正文 / 含反引号的 issue、MR、note | `references/long-body-writing.md` |
| glab 报任何错，或需要不依赖 glab 的 curl 通道 | `references/troubleshooting-glab.md` |
| 合并前核验可合并性；顺序合并遇 406；批量合并 | `references/pre-merge-checks.md` |
| 合并后验证落地；`glab mr merge` 报错；误合并要撤销 | `references/merge-verification.md` |
| 长期分支合 advanced main；merge-tree 干净但合并后挂测试；改名撞在途 MR | `references/advanced-merge-patterns.md` |
| 处理评审意见；只读评审 MR；行内评论 | `references/review-response-loop.md` |
| 合并后清理本地分支与 worktree | `references/post-merge-cleanup.md` |
| 仓库迁移 / 改名 / 换 group | `references/repo-migration.md` |
| 为独立议题开分支；镜像仓开 PR 前核对基线 | `references/branch-baseline.md` |
| 写 `.gitlab-ci.yml` / Pages / 定时流水线 | `references/ci-pages-quirks.md` |
| 建新仓；首次在新仓提交前核对身份 | `references/repo-init-and-identity.md` |
| 建议题 / 开 MR 前定标题 | `references/title-prefix-code.md` |

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
5. **等用户明确说「可以合并」才合并**——先查 CI（`pipelines?ref=<branch>`）与 `has_conflicts=false`，再走下方合并路径；merge API 404 时用本地 fast-forward + push master（MR 自动翻 merged，见症状表）
6. 删除分支属破坏性操作，会被审批拦截——留给用户指示，不主动删

**堆叠 MR（前置 MR 还开着、后续改动不能等时）**：从前置 MR 的源分支开新分支，MR 的 `target_branch` 指向该源分支而非默认分支——diff 只含后续改动，评审不夹带前置内容；描述写明「依赖：需先合并 !<base>」。开 MR 前用 `git diff --stat <base-branch>...HEAD` 自证只含自己的改动。合并顺序：先合基线 MR；GitLab 13.11 不会自动 retarget，需 `PUT .../merge_requests/<iid> -f target_branch=master` 把堆叠 MR 重指到默认分支后再合并。

**坑（2026-09-12 实测，MR !1 llm-monitor）：push 分支先于 commit → MR 空 diff。** 若分支在改动 commit 之前就 push 过（如中途被审批打断），MR 建出来 diff 为空；补 commit 再 push 同名分支，MR 自动更新到新 sha（GET `/merge_requests/<iid>` 的 sha 变化即确认），无需重建 MR。另外 commit+push+建 MR 不要串成一条长命令——审批闸会拦整条链，拆成单步逐个执行。

**合并检测只在 push 时对 open 状态的 MR 生效（2026-09-12 实测，MR !2/!4 llm-monitor）**：这台 GitLab 13.11 标记 merged 的唯一途径是 push master 时的 post-receive 自动检测（本实例 merge API 全被禁用：`PUT`/`POST .../merge` 均 404/405，与 MR 状态无关）。因此 **push master 前 MR 必须处于 open 状态**——提前 close（或 push 发生在 close 之后）会让 MR 永远停在 closed，事后 reopen + 再 push（no-op 不触发 post-receive）也救不回来，只能 close + 评论注明「以 master 为准」。顺序铁律：merge 本地（`--no-ff` + GitLab 风格 message，见症状表）→ push main → 确认 state=merged → 最后才清理分支。同因果链的坑：**不要照搬上一个"坏 MR"的 close 流程**（MR !4 因照搬 !2 的 close-先于-push 流程而丢了 merged 状态）。

**多轮改动的分支卫生**：同一条分支服务多个议题时，MR 标题/描述要随最新 push 更新（`PUT merge_requests/<iid>`），否则 MR 描述与实际 diff 脱节。描述里的验证勾选清单同样随进度维护：完成一项就 PUT 勾上并附证据指针（目录+日期），别留「执行中」字样过期；发现未勾项先核对既有证据目录（常是已做完忘了更新描述）——补勾+评论收口即可，不查证据别急着重做。

**用户明确要求“提交、推送、更新评论但不要合并”时**：先用 `git status --short` 和 `git diff --name-only` 列出范围，只 `git add <目标文件>`，不要用 `git add -A`，以保留未跟踪文件原样；提交后核对 `git show --stat` 与工作树，再 `git push`。随后用 `git ls-remote origin <branch>` 和 GitLab MR GET 同时确认远端 SHA 与 MR `sha` 一致、`state=opened`、`merged_at=null`、`has_conflicts` 状态明确。长评论写入文件并通过可靠的 argv/`-F body=@file` 通道发布，立即回读 note，比较正文（允许存储层去掉末尾换行）并确认署名存在；只有用户明确授权合并时才进入合并流程。

**收到“继续”后不要把可验证事项升级成阻塞**：若修改口径已经确定，直接按既定范围完成验证、提交、推送和留痕；尚未确定的细节应标为风险并继续完成不依赖它的步骤，除非它确实改变写入内容或安全边界。这样可避免把调度判断误报成系统停止，也避免任务停在半完成状态。

**方向被用户否决后必须同步「四处记录」（2026-09-13 用户抓到的真实疏漏）**：当讨论中修复方向改变（实测：先按「降级 thinking」写了 issue 方向 → 用户否决「能力不能阉割」→ 实现改成「回填」），只改实现不够——**issue 正文 / 分支名 / MR 标题与描述 / 仓内文档（处置表、手册）**都要一起改，否则用户读到旧文字会合理质疑「你的修复跟我的要求一致吗」。做法：改分支名（`git branch -m` + push 新分支）、关掉旧 MR 并重开（`glab mr close <iid>` → `glab mr create --source-branch <new> ...`）、`PUT issues/<iid>` 重写描述，最后跑一条自检（`grep -c "<旧表述>"` 应为 0）再回报。

**提交信息走文件，别用 `-m` 内联（2026-09-13 实测的静默坑）**：`git commit -m "…含双引号/反引号…"` 会让 shell 把消息切成多个 pathspec，git 报 `error: pathspec 'xxx' did not match any file(s) known to git` 且**提交根本没发生**（随后 push 推的还是旧 HEAD）。凡提交信息含引号/反引号/多行，一律 `write_file /tmp/commit_msg.txt` + `git commit -F /tmp/commit_msg.txt`。MR/issue 描述走 `references/long-body-writing.md` 的 argv 通道。

**建新仓、或首次在一个新接手的仓里提交**：先看 `references/repo-init-and-identity.md`（`glab repo create` 可用路径；全局常缺 `user.email` 会让 committer 静默变成 `<用户名>@<主机名>.local`，首个 commit 前核对身份；Office 锁文件别进历史）。

## 议题收尾与后续议题（关闭已完成议题 + 建可直接开发的议题）

**全量梳理（admin 要求「梳理现有议题状态」时的产出形态）**：盘点用 `glab api "projects/<id>/issues?state=opened&per_page=100"`（三段拼接吃 page 参数，直接单串带查询参数）；逐条判定前先读 body+notes（列表 body 截断，非正文）。产出=逐条表（#｜标题摘要｜现状｜建议=关闭/派工/留），现状必须指向硬证据而非议题自述：**「[施工]/[缺陷] 类完成没关」最常见的原因是 MR 描述未写 `Closes #N` 且 GitLab 13.11 API 合并不自动关单——用 `git log --oneline --grep='<iid>'` 在仓里反查 MR 号与 merge SHA，API 核实 `state=merged` 即可建议关闭**；「[记录] 类」判内容是否已沉淀进仓内文档（沉淀完即建议关闭留痕）；「疑似过期」类（如 mac 平台问题与平台定性冲突）标注疑点待 admin 裁决，不自行关闭。表格末尾给分类小计（关/留/派工）+拍板点，批量动作等 admin 逐类拍板后执行。

**留痕评论只写已发生的事实，计划与待办单列**——「文档里已有裁决」「方案文档已写好」不等于「事项已完成」，把计划写成完成态就是伪造记录，用户会当场打回。现状类评论固定三段：已发生（附证据指针）/ 未发生待办（编号列出）/ 待决策项去向。

**调查结论沉淀进手册（「把现象和修法沉淀到运维手册」类指令）**：

1. 取全量证据再动笔：单条 GET 议题（正文字段是 `description`，不是 `body`）+ **全部 notes**（`.../notes?per_page=100&sort=asc`）+ 仓内 verification/harness 的 README——定案结论几乎总在最后的 note 里，议题正文往往还是立案时的旧口径。
2. 定位手册里承载**旧口径**的所有位置：用症状关键词 grep 全 docs/，把每处「待定位/治标/见 #N 跟踪」找全——只改主小节、不改引用处，手册会自相矛盾（排障节、checklist、相邻节注常各留一份旧话）。
3. 沉淀内容固定形状：现象特征（含判别性细节，如截断位置浮动带）→ 根因（哪一跳、为什么静默）→ 修法（可直接抄的配置块）→ 为什么临时手段只治标 → 现场核查线索 → 复现 harness 的仓内路径。
4. MR 描述写 `Closes #N` 走 CLI 合并自动关单（见下）；note 在合并前发。
5. tsie-tunnel 双 remote 惯例：origin（开发仓）合并后向只读镜像 tsie 快进 `git push tsie origin/master:master`（只推分支不带 tag），回读两仓 master 一致才算收尾。

**关闭已完成议题**（管理员「检查议题，完成的可关闭，并为后续提议题」时的固定顺序）：

1. 先 `glab api "projects/<id>/issues?per_page=100&scope=all"` 全量盘点——已完成但忘关的议题会留在 opened，只数 opened 会漏。
2. 每个待关议题先取证据，证据形态按交付类型二选一：代码/修复类看**关联 MR `state=merged` 且 `merged_at` 非空**；文档/基线类看**交付物已在 origin/master**（`git cat-file -e origin/master:<路径>`，或归档目录在档）——文档交付常无独立 MR 或 MR 早已合并，文件在档即证据。第三种形态：**议题跟踪的使命是「完成评估/实现并交评审」而实现停在 feature 分支评审中**——按使命完成关闭（note 写明分支名、评审 MR 号与「评审打回可重开」），不因「代码未并 master」机械保留；反之，议题声明「保持 open 的主跟踪件」（如实施计划跟踪）无论多旧都不关。多步骤议题逐步验证：每步各自的 MR `state=merged` 加外部动作落地证据（本机软链已建、对侧仓 commit 在档、项目 `archived:true`）逐项回读，总控 MR 合并不代表分步全完成。**标题与实际不符时不关**：议题声明的修订可能从未落盘（目标文件仍停在旧版本或「待评审」态）——按现行文件版本判定，不按议题自述；议题正文里的旧拍板可能已被后续裁决取代，回填前先对照现行基线口径（写清谁被谁取代），别照抄旧结论。同时看议题自身 `state`/`closed_at`：已被提前关闭就跳过 close 调用，但证据评论照发——留痕与关单是两件事。
3. 关前发一条**证据评论**（MR iid + merge commit，或 master 上的交付物路径 + 验证结论 + 落款），再 `PUT issues/<iid> -f state_event=close`，最后 re-GET 确认 `state=closed`。**自动关单按合并通道分两种**：走 `glab mr merge`（CLI 合并通道）时，MR 描述里的 `Closes #N` **会生效、议题随合并自动关闭**（实测回读 `state=closed`；仍必须 re-GET 议题确认，别默认关键字一定生效）；本地 push 触发 post-receive 把 MR 自动翻 merged 时，`Closes #N` **不触发**（实测 push 后 MR 已 merged、issue 仍 opened，需手动 `PUT issues/<iid> -f state_event=close`）。证据评论同时是关闭理由的留痕；靠 `Closes #N` 自动关单时，note 要在**合并前**发——合并后议题即关闭，再补 note 读起来像事后记账。

**后续议题正文模板**（管理员要求「工程师根据议题和文档直接开发」时的可执行标准）：标题按「标题前缀码」带前缀；正文五段——①背景（现状 + 依赖一句话）；②文档与代码引用（仓内文档路径 + 章节/行号 + 代码文件）；③实施范围（每项写「现状 → 改法」，含文件与行号锚点）；④禁止事项（不改什么、不引入什么，git 红线）；⑤验收条件（编译工具链 pin、测试数基线、禁项扫描、基线失败集对齐）+ 参考。按依赖切分：无前置的收尾议题现在可开工；接真议题把前置列成表（任务卡号 + 承载能力）并注明「前置到位后拆子议题」。建完 re-GET 比对字符数（存储层吃掉结尾换行，`desc.rstrip() == local.rstrip()` 判等）。

**标题前缀码**（建议题 / 开 MR 前必查）：议题 `[类别][状态?] 摘要`、MR `type(scope): 摘要`；类别 × 状态并非任意组合，合法格与不适用时的改法见 `references/title-prefix-code.md`（用 `skill_view(name='gitlab-mr-workflow', file_path='references/title-prefix-code.md')` 加载）。建单前跑 `python3 scripts/title-lint.py issue|mr "<标题>"`，脚本直接解析该文件的组合表。

**长正文写入**（issue 正文 / MR 描述 / note）：`@file` 展开与 `--input` 在不同 build / 端点 / 会话之间不一致且失败是静默的（CLI 报成功，落库的是字面量 `@/path/body.md`）。可靠通道＝不经 shell，把正文作为单个 argv 元素传给 `glab api`；写后必读回字符数核对。字段名按端点不同：notes 只认 `body`，issue / MR 用 `description`，混用即 400。完整写法、python 通道、env 与 PATH 坑见 `references/long-body-writing.md`。

## Reference

- `references/title-prefix-code.md` — 议题 / MR 标题前缀码：类别 × 状态合法组合表、不适用组合的改法、MR type 表、`scripts/title-lint.py` 用法。
- `references/long-body-writing.md` — 长正文写入：argv 直传代码、`@file` / `--input` 各端点表现、字段名、execute_code 内 PATH / HOME 要求、写后核对、临时文件收尾。
- `references/troubleshooting-glab.md` — glab 症状速查表（Unauthenticated / panic / 空输出 / 400 / 404 / 406 / 414 / 正文损坏 / `--jq` / `-o` / 上传 / `--hostname` / 项目路径编码）＋ git credential-store token 回退 ＋ 不依赖 glab 的 curl 建 MR 通道。
- `references/pre-merge-checks.md` — 合并前预检（merge-tree 新旧语法、`has_conflicts` 过期、sha 须 40 位、合并前洗掉两处关单关键字）、顺序合并 406 分诊、批量合并摸底与排序。
- `references/merge-verification.md` — 合并后验证（API 回读、remote 指错仓的判别、编造 SHA 的更正）、MR 存在性核验（push ≠ 建 MR）、detached worktree 复验与失败归因、误合并的 revert / reset / keep+rebase 三选。
- `references/advanced-merge-patterns.md` — 语义冲突（文件级干净但合并后挂）、modify/delete 与生产代码被删变体、长期分支合 advanced main 的「整块 vs 空＝搬移」、文档血统分叉、改名撞在途 MR 的按块分流，及 `scripts/resolve_merge_conflicts.py` 的用法。
- `references/review-response-loop.md` — 评审意见处理九步闭环、只读评审（`/changes` 的 `+0 -0` 假象、并行 MR 同文件）、行内评论命令、Java 注释 `\\u` 与 XML 代理项过滤两个编码坑。
- `references/post-merge-cleanup.md` — 合并后清理：worktree 先于分支、`-d` vs `-D`、批量清扫已合并 worktree 的证据纪律、删除已关闭 MR 分支的核验。
- `references/repo-migration.md` — 仓库迁移 / 改名：判「传输」还是「新建」、量清新旧 main 关系、MR 目标分支按 diff 选、重指 remote 并保留旧地址、旧 MR 只关不合。
- `references/branch-baseline.md` — 独立议题的分支基线（不得从冻结特性分支开）、按分支报测试数、声称合并后从 main 开分支前的核对、GitHub 镜像仓 PR 夹带外来提交的修法。
- `references/ci-pages-quirks.md` — 13.11 无 `publish:` 关键字、runner tag 须存在、可用的两 job Pages 模式、定时流水线与 masked 变量的 API 写法、私有项目 Pages 302 属正常。
- `references/repo-init-and-identity.md` — `glab repo create` 路径（该 build 无 `--source/--push`）、无 CI 裸仓合并不卡 pipeline、首个 commit 前核对作者邮箱、Office 锁文件别入历史。
- `references/chrome-show-mr-collab.md` — the chrome-show-issue-and-mr-no group-chat collaboration flow: admin-mandated MR-first review process (never pre-review in the local workspace), role split (manager reviews, test independently accepts, only admin merges), plus that project's testing pitfalls.
- `references/planning-comment-workflow.md` — turn an issue's "待规划" state into a reviewable planning comment on GitLab (survey codebase → module-boundary table → phased steps → publish via glab `-f` note, clean up temp files).
- `references/gitlab-ci-writeback.md` — how a scheduled CI job persists state back into the repo (history.json etc.) on GitLab 13.11: reuse the glab PAT as a masked CI var (CI_JOB_TOKEN can't push protected branches), the `[skip ci]` loop-prevention mechanism AND its footgun (a `[skip ci]` string anywhere in a *feature* commit message silently skips the whole pipeline), force-push is rejected on protected branches, the YAML colon/bracket gotcha that splits `script:` items (use a block scalar `|`), `ci/lint` API validation, and manual pipeline trigger + artifact verification.
- `references/parallel-impl-shared-checkout.md` — when multiple agents implement parallel MR lines (e.g. dev/dev2 in the group-chat flow): one writer per checkout, how to detect a foreign writer's WIP mid-edit (patch "modified since read" + syntax errors in untouched regions), why function-level non-overlap is NOT sufficient, and how to recover (stop, audit, escalate, replay after the other side lands). Includes the render-skip guard pitfall (enumerate all callers before skipping a render side effect).
- `references/chrome-show-content-harness-quirks.md` — that repo's content.test.js FakeNode harness: stale getBadge references after any re-render, missing DOM APIs (no `.closest()`), the instrumented-copy debugging pattern (copy INSIDE tests/ or relative requires break), the persisted-preference trap (`persistSearchState` silently drops new fields — use `configStore.save`), and the panel-owned filter state pattern (`navigation.<field>` + `Owned` flag surviving `resetNavigation`).
- `references/regression-test-gate-handoff.md` — when a gate review conditionally passes an MR with a "test gap" blocker: work in the branch's existing temp worktree (git branch -vv shows it), add tests-only commits to the SAME MR branch, write one test per guard using the harness recipes (deferred fetch + signal.aborted assertion, DOM node reference-equality for no-rerender proofs, resize→sync for unchanged-URL triggers), and MANDATORY mutation-check (remove each guard → a test must flip not ok → restore → green) with results reported in the MR note before @reviewer.
- `references/pr-base-divergence-pollution.md` — 完整案例：GitHub 镜像仓本地 main 分叉导致 PR 吸收外来提交的定位与 `git rebase --onto` 修复。
- `references/badge-css-split-refactor-pattern.md` — 大块逐字搬移（如 720 行 `BADGE_CSS` 模板串拆成独立文件）的做法：用 Python 按精确标记切片而非大 `old_string` 的 patch、新文件镜像同级 UMD 并接入全部加载链与顺序断言测试、纯重构 MR 的零行为变化证据链，以及落 MR 时遇到的 API 注意事项（从 `origin/main` 开分支、POST 响应即权威）。
- `scripts/resolve_merge_conflicts.py` — list every conflict block in a merge-in-progress (`--list`) and resolve them from a JSON plan with per-block rules (`main` / `head` / `both` / `custom`, optional end-of-file `append`); fails loudly if the plan misses a block. Surrounding workflow (scope-parity diff, build, push, MR refresh) in `references/advanced-merge-patterns.md`.
- `scripts/title-lint.py` — 校验议题 / MR 标题前缀码，合法组合表解析自 `references/title-prefix-code.md`，改表即改规则。
