# 仓库迁移 / 改名

> 从 SKILL.md 拆出，内容为实测口径原样搬运。触发：仓库迁移、改名、换 group 后重定向 remote 与 MR。

## 仓库迁移/改名后重定向 remote 与 MR（verified 2026-09-21, tsie-airs-backend 迁 group）

项目路径变了（换 group / 新建项目），本地 clone 仍指向旧项目、旧 MR 仍挂着。按此顺序处理：

1. **先判「传输」还是「新建」**——新旧两个路径都查一次：`glab api "projects/<ns>%2F<repo>"`。GitLab *transfer* 会让旧路径重定向；若新旧**同时**解析出两个不同 id、且新项目 `created_at` 是最近的，那是**新建项目**（有人从本地 clone push 过去的），不是搬运。
2. **动 MR 之前先量清内容关系**——新项目 `main` 常是别人本地滞后 main 推上去的：
   ```bash
   git fetch <newremote> --prune
   git log --oneline -5 <newremote>/main                      # 看它停在哪
   git merge-base --is-ancestor <old-main-sha> <newremote>/main && echo "新 main 落后" || echo "分叉"
   git rev-list --count <newremote>/main..<old-remote>/main   # 落后多少提交
   git log --oneline <newremote>/dev-branch..<old-remote>/main # 只是 merge 提交，还是真有内容缺失
   ```
   同时看新项目 `default_branch`：**新建项目 push 时 GitLab 常把「第一个被 push 的分支」设为默认分支**（本例是开发分支 `feature/wangxq`，不是 `main`）——那是产物不是意图，别据此推断评审流向。
3. **MR 目标分支要用「量出来的 diff」选，不要按习惯选**：GitLab 的 MR diff 基于 `merge-base(target, source)`，目标分支直接决定这个 MR 看起来干净还是夹带。候选目标逐个跑 `git diff --stat <candidate-target>...<branch>`，挑差异**恰好等于你自己改动集**的那个（本例：target=当前开发线 → 5 文件；target=滞后 main → 69 文件，把别人 24 个提交的内容一起带进来）。若诚实基线在开发分支上，就指向它，并在 MR 描述里**写明原因 + 「要改指回 main 只需一句确认」**——一个文档 MR 突然多出 69 个文件，评审一眼就否。
4. **重指 remote 且保留旧地址**：`git remote rename origin oldorigin` → `git remote rename <newremote> origin` → `git push -u origin <branch>` → `git ls-remote origin <branch>` 必须等于本地 HEAD。（rename origin 会把分支 upstream 改写成 `oldorigin/...`；`push -u` 在新 remote 上重新建立跟踪。）
5. **在新项目重建 MR**：用「长正文写入」的 argv 写法（别赌 `@file`）。建完**必须**用 `glab api "projects/<newid>/merge_requests/<iid>/changes"` 数 `changes[]` 长度——那是 GitLab 自己的 diff，才是「无夹带」的权威证据，本地 `git diff` 不算。
6. **旧 MR 只关闭 + 留指向，绝不合并**：先 POST note（「仓库已迁移 → 新仓 MR !N，同分支同 sha」），再 `PUT .../merge_requests/<iid> -f state_event=close`，然后复验 `state=closed` 且 `merged_at=null`。不要留两个 opened MR。
7. **汇报时给 owner 一行补救**：把「新仓 main 落后 N 提交 + 我把目标定在 X + 要改指 main 只要一句确认」一起说清。新项目通常 0 issue：旧 issue 号不要在新仓引用，是否重建 issue 让 owner 拍板——不擅自重建。

**描述长度校验的细节**：GitLab 存 description 时会吃掉**一个结尾换行**，所以文件以 `\n` 结尾时 `len(description) == len(file) - 1` 属正常；用 `desc.rstrip() == local.rstrip()` 比较，别为了差 1 个字符重写正文。
