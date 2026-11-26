# 评审意见处理闭环

> 从 SKILL.md 拆出，内容为实测口径原样搬运。触发：处理评审意见、只读评审 MR、写行内评论。

## Responding to review comments on your own MR（评审意见处理闭环）

Admin 指令「看下 MR 的评审结果，需要修改的改完回复评论」时的固定流程：

1. 拉全量评论：`GET projects/<id>/merge_requests/<iid>/notes?per_page=100&sort=desc&order_by=created_at`，只处理 `system=false` 的人写 note——system note 是状态流水，不是评审。
2. **逐条对照源码核实再动手**：工作树常停在别的分支——用 `git show <branch>:<path>` 直接读分支上的文件、`git show <mr-sha> --stat` 看改动范围，不必先切分支。评审断言可能滞后于事实：合并前检查项若已有落地证据（验证目录、实验记录、既有评论），以证据指针回复即可，不重做。
3. 分诊三类：改（代码/测试/注释）；不改（评审自述「可选/这次不改也行」的，说明保留理由）；已满足（附证据位置）。
4. 在 MR 源分支落改：动手前 `git branch --show-current` 确认停在本分支——多 MR 并行时工作树常停在另一条分支，grep 目标文件报 `No such file or directory` 就是停错分支的信号（文件在别的分支上）。tracked 树干净时直接 `git checkout <branch>` 切过去（untracked 证据目录不受影响），commit + push——MR 的 `sha` 自动跟到新提交，push 后 `merge_status` 短暂 `checking` 属正常重算。工作树有未提交 tracked 改动则用临时 worktree，勿把两摊改动混进一个提交。
5. **一条 note 逐点回复全部意见**：每条标处理结果 + 落改 commit + 验证数字（测试 x/y），群聊惯例末尾署名（名字+角色）；发完回读 note 核对。评审「可以合并」≠ 合并授权——仍等用户拍板。
6. **验证者报「通过」后抽样核证，不照单全收**：核对证据目录真实存在且关键文件齐全（行级证据、MR 状态 API 回读、surefire XML、SHA256 清单），抽查 1-2 条行级断言与源码一致即可收口，不必重跑全套；证据对不上就打回复验，别让自述替证据。
7. **警惕无人派工、无人汇报的「先落地返工」**：system note 不是评审内容，但其中的「added N commit」暴露返工 commit 已推上分支——可能没有任何人向你汇报过。此类 commit 不得当「已处理」直接回复评审：先 `git fetch` 对齐 sha、`git reflog`（时间戳）确认提交来源与操作时间线，再独立核验——diff 逐条对照评审建议（改法/注释/测试三点都对上）+ 亲自重跑受影响模块测试；回复里引用自己跑出的验证数字，不转述来历不明 commit 的自述。
8. **非阻塞建议被采纳也走完整闭环**：评审标「可选/顺手改」的建议一旦决定采纳，规格与必修项相同——落码 commit + push + 回帖引用 commit 与验证结果，别只回帖不改码；差别仅在小改动不必再派独立复验，Manager 抽查 diff 即可。
9. **跨 MR 指引别钉死 commit sha**：文档指路「install/checkout 某前置 MR 的代码」时写 MR 号或「合入后即默认分支」，不写具体 sha——前置 MR 后续返工会换 sha，钉死的旧 sha 是带缺陷的版本，照做的人拿到坏代码且无从察觉。改完 `grep -rn <旧sha> <docs 目录>` 自查残留；同口径的姊妹措辞（如「用 master 构建」在合入后会同样过期）一并改成按「含/不含某 MR」表述。

**Java 源文件里注释写 `\u` 字面量会编译失败**：javac 在词法分析前就展开 unicode 转义，注释/javadoc 不豁免（报 `illegal unicode escape`）——在注释里描述转义序列时写 `uxxxx` 或去掉反斜杠，别照抄 `\u4E92` 这种写法。

**按单个 UTF-16 code unit 过滤 XML 合法字符会误杀成对代理项**：代理项区 `0xD800-0xDFFF` 落在 `[#x20-#xD7FF]` 与 `[#xE000-#xFFFD]` 两段合法区间的空档，逐 code unit 判定时不止孤立代理项被剥——**成对代理项（补充平面字符，CJK 扩展 B/emoji）也整对丢失**（如标题里的 𠮷/😀 被静默删掉）。循环里先成对识别：`Character.isHighSurrogate(ch) && i + 1 < s.length() && Character.isLowSurrogate(s.charAt(i + 1))` → 整对放行并跳过低位；孤立代理项才走剥除分支。测试须含成对代理项保留断言 + 标准 XML 解析器良构校验，既有孤立代理项用例也补良构校验。

## Read-only MR review: trust the source branch, not the changes API

Reviewing an MR (before/without merging) from the manager side:

- **`glab api .../merge_requests/<iid>/changes` can report `+0 -0` for files that actually have content** (GitLab 13.11 display quirk, verified 2026-09-28: two newly-added test files showed `+0 -0` while `git show origin/<branch>:<path> | wc -l` returned 841 / 436 lines). Never conclude "file is empty / unchanged" from the changes listing alone — verify each suspect file with `git show origin/<branch>:<path> | wc -l`, and measure the real scope with `git diff --stat <merge-base> origin/<branch>`.
- **Parallel MRs on the same target branch**: two MRs that both modify file F — the one merged first forces the other to rebase (bidirectional change = "changed in both" in merge-tree). Two MRs ADDING the SAME new file merge cleanly only when the content is IDENTICAL — verify with `diff <(git show A:path) <(git show B:path)` (→ IDENTICAL); differing content = add/add conflict. When reviewing a queue of MRs on one branch, check each one's merge-base against the current target head and call out the ones cut before a prior merge — those will conflict even though each MR alone reads `has_conflicts=false`.
- Post review comments as MR notes (body channel per 长正文写入 above); structure each note 结论 + 通过项 + 问题清单（按严重度 P1/P2，附位置与依据）+ 处置建议 + 落款，并明确「只读 review、暂缓合并」当存在阻塞项时。

## Inline review comments

Use positional args for file/line anchored notes:
```bash
glab mr note create <mr_iid> --file <path> --line <new_line>   # or --old-line
glab mr note create <mr_iid> --reply <discussion_id> -m "..."
```
Verify the note landed by fetching the MR notes via API (note IDs come back in the response).
