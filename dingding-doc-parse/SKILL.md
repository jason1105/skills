---
name: dingding-doc-parse
description: >
  解析钉钉在线文档（alidocs.dingtalk.com）的完整内容，包括正文文字和文档中的图片。
  当用户提供钉钉文档链接、要求提取文档内容、解析文档图片、或分析钉钉文档时，使用本 skill。
  同样适用于：提取文档中的图片链接、解析图片内容、获取文档结构化信息。
---

# 钉钉文档解析 Skill

本 skill 指导如何完整解析钉钉在线文档，包括文字内容和图片内容。

## 工作流程总览

```
1. 读取文档 → 2. 提取图片链接 → 3. 下载图片 → 4. 用 Read 工具解析图片内容 → 5. 汇总输出
```

---

## Step 1：读取文档

使用 `mcp__dingding-doc__read_document` 工具读取文档：

```
mcp__dingding-doc__read_document(url="https://alidocs.dingtalk.com/i/nodes/xxx...")
```

- 如果返回二维码登录提示（isError=true），告知用户扫码，等待约 30 秒后重试
- 文档内容以 Markdown 格式返回，图片以 `![图片](url)` 形式嵌入

---

## Step 2：提取图片链接

从返回的 Markdown 中提取所有图片链接，格式为：

```
![图片](https://alidocs2-zjk-cdn.dingtalk.com/res/.../img/xxx.png?Expires=...&Signature=...&auth_key=...)
```

**注意**：
- 图片链接带有签名参数（Expires、OSSAccessKeyId、Signature、auth_key），有时效性
- 需在有效期内（Expires 时间戳前）完成下载和解析

---

## Step 3：下载图片

使用 `curl` 将图片下载到本地临时目录：

```bash
curl -s -o /tmp/doc_img_1.png "完整图片URL（含签名参数）"
file /tmp/doc_img_1.png   # 验证下载成功
ls -lh /tmp/doc_img_1.png
```

如需批量下载多张图片：

```bash
curl -s -o /tmp/doc_img_1.png "url1"
curl -s -o /tmp/doc_img_2.png "url2"
# ...
```

---

## Step 4：用 Read 工具解析图片

直接使用 Read 工具读取本地图片文件，Claude 会自动识别并描述图片内容：

```
Read(file_path="/tmp/doc_img_1.png")
```

**关键点**：
- 不需要调用外部 API，不需要 ANTHROPIC_API_KEY
- Claude（当前对话）本身支持图片识别，直接 Read 即可
- 可并行读取多张图片以提高效率

---

## Step 5：汇总输出

将文字内容与每张图片的解析结果按文档原始顺序组合输出，格式参考：

```
## 文档标题

### 章节一
[文字内容...]

**图片1**：[图片描述，包含图中所有文字、图表结构、数据等]

### 章节二
...
```

---

## 注意事项

1. **图片时效性**：钉钉图片 CDN 链接有过期时间，需尽快下载，不要在汇总阶段才下载
2. **并行处理**：多张图片可并行下载、并行 Read，提高效率
3. **图片数量**：若图片很多（>10张），可先解析关键图片，或询问用户需要解析哪些
4. **登录状态**：文档读取依赖用户已登录钉钉，若提示扫码则等待用户操作后重试
