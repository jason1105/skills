# prd-interactive-prototype · 运维备忘

随 SKILL.md 主规范外移的仓库运维细节。主规范只保留交付要求，本文件承载操作细节。

## 全仓唯一原型的 MR 纪律

- 原型入库走 MR 后，回复必须带**分支名＋HEAD 短 sha**——用户常拿旧 commit 的文件验收新特性，白报一轮缺陷〔事故〕实测两次
- 任务 MR 开着时用户随时可能点合并：**推后续 commit 前先查 MR state**（`glab api projects/<id>/merge_requests/<iid>` 看 state），发现已 merged 就同分支重开 follow-up MR（diff 对 master 自动只剩合并点之后的新 commit，描述 Refs 原议题）——否则新 commit 挂在已合并 MR 的认知里，交付汇报漏一件
- 多个 skill 共用此纪律：合并一律经 MR/GitLab 侧执行，禁止本地 merge+push 默认分支

## 三件套定位与写入

- 用户会移动目录（说「我移动到了这里」给的可能是新基准文档路径）。用 `mdfind -name`/`find` 按文件名全盘搜确认三件套现址；同名前缀三件应同目录（MD↔HTML 相对链接依赖同目录）
- 找到后 `read_file` 全量再改——`write_file` 有 stale 保护，没读过就整写会被拒，这是提示先读，不是绕过的信号

## master 主仓被 worktree 占用

`git checkout master` 报 "already used by worktree" 时：`git worktree add <scratch>/wt-master origin/master` 开独立工作树，在其上建分支干活，push 后开 MR。scratch worktree 不会被自动清理，含未合并改动时提醒用户勿删。

## 原型 HTML 批量文本手术

- python 字符串替换做批量改动时，定向 replace 与兜底插入两条路径可能都命中造成重复插入——**每次插入后 `grep -c` 验证目标片段出现次数**
- 改完先过**语法门**：抽出 `<script>…</script>` 块写临时文件跑 `node --check`。JS 单引号串内 `\'` 在 python 源码须写 `\\'`，写成 `''` 即语法错——整页脚本中断，症状是 `S is not defined`/STORIES undefined，node --check 秒级定位而浏览器里才显形
- 语法门过后必跑浏览器回归（卡片行数／定位链双向／视图渲染），不要只看文件写成功

## skill 正本与装回

- 正本：`~/.agents/skills/prd-interactive-prototype/`（skills 仓 git 管理，remote github jason1105/skills）
- 旧路径 ~/MyProjects/lvwei/ai/skills 已废
- 装回：`npx skills add <仓库> -g --skill prd-interactive-prototype`
- `skill_manage` 对 CLI 软链 skill 报 not found 属正常（skill_view 仍可读）——直接改正本仓，勿在安装层重建
