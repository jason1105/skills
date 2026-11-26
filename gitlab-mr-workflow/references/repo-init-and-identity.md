# 新仓初始化与提交身份

> 从 SKILL.md 拆出，内容为实测口径原样搬运。触发：建新仓；首次在新接手的仓提交前核对提交身份与临时文件。

**新仓初始化路径（本次验证可用）**：`glab repo create <name> --private -d "<desc>"`（该 build **没有**
`--source/--push` 旗标）→ `git remote add origin http://git.tsintergy.com:8070/<ns>/<repo>.git` →
`git push -u origin main`。无 CI 的裸仓合并 MR 不会卡 pipeline（`glab mr merge <iid> --yes` 输出
`! No pipeline running on <branch>` 后照样 `✓ Merged!`），但**合并仍需用户明示**，合并后 `git fetch`
+ `git pull --ff-only` 让本地跟上 MR 的 merge commit。

**首次在新接手的仓提交前，先核对提交身份与临时文件**：
- 全局配置常只有 user.name 没有 user.email——git 会静默把 committer 补成 `<用户名>@<主机名>.local`，与仓内既有提交的公司邮箱身份不一致。首个 commit 前先 `git log -1 --format='%an <%ae>'` 看既有身份；不一致时，push 前 `git config user.name/user.email`（仓级）+ `git commit --amend --reset-author --no-edit` 修正——push 之后再改就要 force-push（红线）。连续多笔一起修：设好仓级身份后 `git rebase --exec "git commit --amend --reset-author --no-edit" HEAD~N` 一次重铸最近 N 笔的作者身份。
- docs/ 里含 Office 文档（.docx/.xlsx）时，`git add` 逐个点名目标文件，别整目录添加：`~$xxx.docx` 是 Word/WPS 的打开锁文件，混进历史就赖着不掉。
