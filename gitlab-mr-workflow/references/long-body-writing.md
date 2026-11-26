# 长正文写入

> 从 SKILL.md 拆出，内容为实测口径原样搬运。触发：写多行或含反引号的 issue 正文 / MR 描述 / note。

## 长正文写入（issue 正文 / MR 描述 / note）：argv 直传，别赌 `@file`

`@file` 展开（`-f` vs `-F` 大小写）与 `--input` 在不同 build / 端点 / 会话之间**并不一致，而且失败是静默的**：CLI 报成功，落库的却是字面量 `@/path/body.md`（2026-09-21 实测 issue #2 正文；2026-08-21 也栽过 note）。可靠通道 = **不经 shell，把正文作为单个 argv 元素传给 `glab api`**：

```python
import json, subprocess
# 正文里可能有反引号 / $() / 引号 —— 走 argv 就完全不会被 shell 解释
body = open("/abs/path/body.md", encoding="utf-8").read()
r = subprocess.run(
    ["glab", "api", "projects/<ns>%2F<repo>/issues/2", "-X", "PUT", "-f", "description=" + body],
    cwd=repo, capture_output=True, text=True)
print(len(json.loads(r.stdout)["description"]))   # 必须 == len(body)
```

- 同类写法通用：建 issue（`.../issues -X POST -f title=... -f description=<body>`）、改 MR 描述（`.../merge_requests/<iid> -X PUT -f description=<body>`）、发 note（`.../notes -X POST -f body=<body>`）。短单行值（title、labels、state_event）用 `-f key=value` 直传即可。`-f "description=@/tmp/x.md"`（小写 -f + @file）在 terminal 通道对 issue/MR 的 **create** 端点另有多次成功实例（长中文 markdown 完整落库）——可用，但与 argv 通道同样必须回读字符数核对后才算数；**update/notes 端点仍以 argv 为准**（@file 在这些端点有静默落字面量的实测）。
- `--input <json-file>` 走 `PUT merge_requests/<iid>` 直接 400 `... are missing, at least one parameter must be provided`——该 build 不把 JSON 文件当请求体发；shell 展开通道 `-f "description=$(cat /tmp/d.md)"` 实测能落长中文描述，写后照例回读核对。
- **字段名按端点不同，混用即 HTTP 400**：notes 端点只认 `body`（`.../issues/<iid>/notes -f body=...`）；issue 创建/更新与 MR 描述用 `description`。把 `description` 传给 notes 端点会 400——先想清目标端点的字段名再拼 `-f`（2026-09-24 实踩，五连发全部 400）。
- **execute_code 内核 PATH 不含 `/opt/homebrew/bin`**：`subprocess.run(["glab", ...])` 直接报 `FileNotFoundError`（不是认证问题）——换绝对路径 `/opt/homebrew/bin/glab` 即可在 execute_code 里跑通全部 issue/MR/note 读写；terminal 里照常裸 `glab`。
- **给 glab 子进程传自定义 `env=` 时必须带上 `HOME`**——glab 靠 HOME 定位配置目录，被剥掉的 env 会让它尝试 `mkdir /Library/Application Support/glab-cli` → `permission denied`（exit 2），表象像认证故障实则不是。最小安全 env：`{"GITLAB_HOST": "git.tsintergy.com:8070", "HOME": "/Users/<user>", "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"}`。
- 顺带核对：`PUT merge_requests/<iid>` 的响应带 `sha` —— push 分支后它应等于新 HEAD（MR 自动跟到新提交）。描述与 `sha` 一起核对，避免 MR 描述写的是旧事实（长命 MR 的常见漂移；本次 MR !3 描述仍写着"仅 1 个文件"，实际 5 个）。
- **写后必读**：重新 GET 并比对**字符数**（不是字节数）——中文 markdown 3375 字节 ≈ 3374 字符。回来是 `@path` 或被截断，立刻用同样的 argv 方式 PUT 修正，别留着。
- **临时 payload 文件要收干净**：若本轮被限定"文件操作只能在授权工作区"（非 owner 请求者的约束），把正文文件放仓根 dotfile（如 `<repo>/.sdk-issue-body.md`），**在同一条命令里 `rm -f`**，再用 `git status --porcelain` 证明工作树干净后才汇报——否则临时文件会被读成"你改了仓"。
