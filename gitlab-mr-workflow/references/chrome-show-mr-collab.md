# chrome-show-issue-and-mr-no: 群聊多角色协作的 MR 流程

适用：该项目群聊（admin/manager/dev/dev2/test/UI）中承担 dev/dev2 实现角色。

## 确定流程（admin 明确要求）
1. 实现完成后**先提交、推送并创建 MR**，不要在本地工作区等 manager 预审（!7 的教训：前置本地 review 导致 GitLab 只留最终结果，过程不可追溯）。
2. review 全程在 MR 落评论留痕：每轮发现（文件:行号、等级、建议）→ 研发修复推送 → manager 复查记录 → 最终结论。
3. manager review，test 独立验收并在 MR 留痕；**合并只能由 admin 明确指令**。
4. 任务分派：dev 主功能连续性，dev2 独立子任务/调研；同文件串行、独立模块并行。
5. **群聊点名必须用 @name**（admin 2026-08-19 纠正：「你要 @ 他们才行」）——纯文本「admin:」不路由；需要某人行动时直接 @名 + 明确任务。
6. **team-wide @-mention discipline**（admin 2026-09-03 再次强调：「你和团队沟通要用 @，这一点记下来」）——动员/通知/点评/派工一律点名到人，不泛指「各位」；这是群聊协作的长期规则，适用于所有角色间沟通，@ 后明确该人该做什么。

## §10.7 权限类 MR 的首次授权手工验收门禁（!9 实证）

issue #8（optional host permissions 收窄）类 MR 合并前，admin 必须亲自做一次约 30 秒的首次授权手工验收——Chrome 原生权限气泡（"Allow this site…"）出于安全限制**无法被任何自动化工具（CDP/Playwright/WebDriver）点击**，这是回退方案 1 的原因，规则见 docs/review-rules.md §10.7。

- **manager 可预做的**：冲突预检（merge-tree）、detached worktree 独立跑 `npm test` 基线、`pkill -9 -f chrome-for-testing` 清残留、把步骤清单 + 留痕要求（截图×2 + commit SHA）落成 MR note。
- **必须 admin 亲自做**：chrome://extensions 手动加载 `src/` → 选项页授权 `http://127.0.0.1:8080` 和 `http://git.tsintergy.com:8070` → 气泡点 Allow → 打开目标页确认 badge 正常、Console 无权限错误 → 截图 + SHA 贴 MR 评论区。
- 验收通过前不得合并；验收后 manager 立即合并并 API 复验 `state=merged` + `merged_at` 非空。

## 实现要点
- 开工前 `git fetch && git checkout -b feature/... origin/main`（main 常有新合并，勿基于本地旧 main 建分支）。
- 提 MR 用 `glab api -X POST projects/<urlencoded>/merge_requests`（glab 1.100.0 的 `--jq` 不支持；issue view 有 panic 用 api 替代）。
- MR 描述需写清：基线已有什么、本次补什么、明确不做什么（范围控制）、验收标准对照。
- Issue 标注「需要先决定/暂不实现」的 UI 项不要自行实现，MR 中注明留待设计确认。
- 测试：node test runner（npm run test），dispatchEvent 返回值不含 propagationStopped 时不做该断言。

## test 角色独立验收额外守则（2026-09-03 实证）
- **报告测试数前先分清「clean 基线」vs「含未提交/stash 草稿」**：本项目曾报「180/180」，实为含 stash@{0} 一份 #22 草稿新增 2 用例的数字；该草稿被 stash 隔离后主工作区 `npm test` 回落 **178/178**。任何「N/N 全绿」引用前，test 须在**当前干净态**独立重跑核对该数字，不能拿「含草稿的一次通过」当冻结基线向上游报。写 180 必须在旁标注「含 stash 草稿」。
- **docs 修订单开工前先确认目标文件真含 issue 所述缺陷**：#23 描述称要修 `docs/edge-smoke-and-badge-css-split.md §4` 的「3a/3b 跨重启持久断言」，但实测该文件章节是 §四/§五、**从无 3a/3b 编号、从无该断言**——真正的 3a/3b+重启清空断言落在 dev2 的 `/tmp` worktree 留痕（untracked 不入正式验收）。不凭空改正式验收依据；把「issue 目标文件与实际断言出处不符」作为发现回报 manager，而非硬造一处删除。正式交付口径（baseline §五 #6 + edge-smoke §四/§五）本就不要求 badge 跨重启持久。
- **含 NUL 字节的中文 docs 易被 `read_file`/`file` 误判为 binary**（本项目多份 `docs/*.md` 因此读不出）——用 `sed -n 'a,bp' file` 或 `iconv` 读文本区段即可，属读文件陷阱非文件损坏。

## 测试坑
- FakeNode 未显式赋值的属性是 undefined；改 aria-label 等文案要同步改既有断言。
- **test:browser 残留进程守则（#8 实证，A/B/A 验证）**：授权手势挂死（`granted:[]`、`clickUntilReady` 30s 超时）的根因 = **多个残留 Chrome for Testing 进程并存的环境干扰**（ChromeDriver headful 会话对扩展权限气泡本可自动批准；1 个僵尸实例不足触发，多个实例并存才挂死）。跑前必查 `ps aux | grep chrome-for-testing`，有残留先 `pkill -9 -f chrome-for-testing`；挂死同法恢复重跑。诊断/实验会遗留 CfT 会话，跑完必须清理。
