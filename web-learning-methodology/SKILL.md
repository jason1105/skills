---
name: web-learning-methodology
description: 当你需要自主学习一个陌生 Web 应用的运行机制时，使用本 skill。适用场景包括：为某个 Web 应用开发 MCP Server、为 Web 应用构建 API 集成、对陌生 Web 应用进行逆向研究、学习 Web 应用的认证机制或数据结构。只要你面对一个没有文档或文档不完整的 Web 应用，并且需要理解其内部接口，就应该使用本 skill。本 skill 提供从桌面研究到经验沉淀的完整五阶段方法论，并附带可直接复用的经验文档模板。
---

# AI 工具自主学习 Web 应用方法论

你是一个具备浏览器操作能力的 AI Agent。本 skill 为你提供一套系统化的方法，帮助你在没有任何前置文档的情况下，独立理解任意 Web 应用的运行机制，并形成可复用的经验文档。

**请严格按照以下五个阶段的顺序执行，不要跳过任何阶段。**

```
第零步：桌面研究（Desk Research）
    ↓
第一步：建立学习目标
    ↓
第二步：DevTools 系统性抓包
    ↓
第三步：分析规律，建立数据模型
    ↓
第四步：沉淀经验文档
```

---

## 第零步：桌面研究（Desk Research）

> 动手之前，先用信息搜集降低探索成本。别人踩过的坑，你不需要再踩一遍。

**只有在桌面研究无法满足需求时，再进入后续的 DevTools 抓包阶段。**

### 0.1 通读官方帮助文档

优先寻找：
- **开放平台 / 开发者文档**：是否有官方 API？有则优先使用，无需逆向
- **Webhook / 集成说明**：往往揭示数据结构和认证方式
- **SDK 源码**：如果有官方 SDK，其源码是最好的接口参考

### 0.2 在技术社区搜索相关经验

| 平台 | 适合搜索的内容 |
|---|---|
| **GitHub / GitLab** | 已有的开源实现、SDK、MCP Server |
| **Reddit** | 英文社区的真实使用反馈、踩坑经验 |
| **CSDN / 掘金 / 知乎** | 中文技术博客，详细的逆向过程记录 |
| **Stack Overflow** | 具体技术问题的解答 |

搜索模式建议（组合使用，不要只用一个关键词）：
```
site:github.com {应用名} api
{应用名} 接口 抓包 逆向
{应用名} cookie token authentication
{应用名} MCP server
```

### 0.3 桌面研究的决策节点

完成桌面研究后，回答以下三个问题：
- **有没有官方 API？** → 有则优先用，省去逆向工作
- **有没有现成的开源实现？** → 有则直接复用或参考
- **社区有没有已知的坑？** → 提前规避，节省调试时间

---

## 第一步：建立学习目标

在打开 DevTools 之前，明确你要回答的核心问题。**带着问题去探索，而不是漫无目的地点击。**

对任意 Web 应用，需要弄清楚：

1. **认证机制是什么？** Cookie？Bearer Token？OAuth？Session？
2. **核心数据实体是什么？** 它们之间的层级关系是什么？
3. **你需要哪些操作能力？** 列出、读取、搜索、创建……

将这些问题写下来作为 Checklist，每解决一个打一个勾。

---

## 第二步：DevTools 系统性抓包

> 核心目标：把每一个 UI 操作翻译成对应的 HTTP 请求。

### 2.1 开启 Network 面板

1. 打开 Chrome DevTools（`F12`）
2. 切换到 **Network** 标签
3. 勾选 **Preserve log**（防止页面跳转时日志丢失）
4. 勾选 **Disable cache**
5. 筛选器设置为 **Fetch/XHR**，过滤静态资源噪音

### 2.2 逐一执行操作并捕获请求

**每次只执行一个操作，立刻记录。** 不要同时触发多个操作，否则难以区分对应关系。

| 你执行的 UI 操作 | 你要记录的内容 |
|---|---|
| 打开列表页 | 请求 URL、Method、Request Headers、Response Body |
| 点开一条记录 | 同上，注意资源 ID 从哪里来 |
| 滚动加载更多 | 分页参数的规律（offset? cursor? page?） |
| 搜索 | 搜索参数如何传递 |
| 刷新页面 | 认证 Token 是否有变化 |

### 2.3 重点关注的信息

**Request 侧：**
- `Authorization` 或 `Cookie` header 的格式
- URL 中的路径参数（资源 ID 如 `/doc/{docId}/content`）
- Query string 的分页、过滤参数
- Request Body 的 JSON 结构（POST/PUT 请求）

**Response 侧：**
- 列表数据在哪个字段？（`data.list`? `result.items`?）
- 翻页 cursor / token 在哪里？
- 资源 ID 和正文内容分别对应哪个字段？
- 错误码的格式和含义

### 2.4 在 Console 中快速检查存储

```javascript
// 查看 Cookie
document.cookie

// 查看 LocalStorage
Object.keys(localStorage).forEach(k => console.log(k, localStorage.getItem(k)))

// 查看 SessionStorage
Object.keys(sessionStorage).forEach(k => console.log(k, sessionStorage.getItem(k)))
```

---

## 第三步：分析规律，建立数据模型

### 3.1 认证机制分析

在 Console 中逐一去掉 Header 后重放请求，确认哪些字段是必须的：

```javascript
// 复用页面已有登录态，直接 fetch 测试
const resp = await fetch('/api/xxx/list', {
  headers: {
    'Content-Type': 'application/json',
    // 逐步增减 Header，观察是否返回 401/403
  }
});
const data = await resp.json();
console.log(JSON.stringify(data, null, 2));
```

同时确认：
- Token 存储位置：Cookie / LocalStorage / SessionStorage / 内存
- Token 有效期及是否有 refresh 机制
- 获取方式：登录后自动写入，还是需要额外接口换取？

### 3.2 建立数据模型

将观察到的实体和层级关系整理出来，例如：
```
Entity A（顶层）
  └── Entity B（中层，可嵌套）
        └── Entity C（资源）
              └── Content（内容，通常是单独接口）
```

### 3.3 验证你的理解

对每一个接口，在 Console 中手动构造请求验证：
- **成功** → 记录下来，理解正确
- **失败** → 检查缺少哪个 Header 或参数格式不对，继续排查

### 3.4 遇到特殊情况的处理策略

| 情况 | 处理方式 |
|---|---|
| Response Body 是加密的 | 搜索页面 JS 中的 `decrypt`、`deobfuscate`，找到解密函数后在 Console 调用 |
| 内容在 WebSocket 中传输 | 在 Network 面板切换到 **WS** 标签捕获帧 |
| 接口有频率限制 | 记录限制阈值，后续集成时加入请求间隔和重试逻辑 |
| 内容是私有富文本格式 | 优先从 DOM 读取已渲染的纯文本，而非解析私有格式 |

> **最简原则：如果可以从 DOM 读取已渲染的内容，优先这样做。**

---

## 第四步：沉淀经验文档

> 学到的知识必须立刻结构化记录。每验证完一个接口，立刻写入，不要等到全部搞清楚再写。

使用以下模板为当前 Web 应用创建经验文档：

---

### 经验文档模板

```markdown
# [应用名称] API 逆向工程文档

> 创建日期：YYYY-MM-DD
> 适用版本 / 环境：xxx
> 文档状态：草稿 / 验证完成

## 1. 认证机制

- **类型**：Cookie / Bearer Token / 其他
- **关键字段**：`字段名`，存储于 `Cookie / LocalStorage / SessionStorage`
- **有效期**：已知（N 小时）/ 未知
- **Refresh 机制**：有 / 无，Refresh 接口：`POST /api/auth/refresh`
- **获取方式**：登录后自动写入 / 需调用 `接口` 换取

## 2. 基础信息

- **Base URL**：`https://xxx.com`
- **API 路径前缀**：`/api/v2/`
- **响应标准结构**：
  ```json
  { "code": 0, "message": "success", "data": { ... } }
  ```
- **错误码说明**：`401` 未认证，`403` 无权限，`429` 频率超限

## 3. 数据模型

```
Entity A
  └── Entity B（可嵌套）
        └── Entity C
              └── Content
```

各实体关键字段：

| 实体 | ID 字段 | 名称字段 | 其他关键字段 |
|---|---|---|---|
| Entity A | `aId` | `aName` | `role` |
| Entity B | `bId` | `bName` | `parentId` |
| Entity C | `cId` | `title` | `createdAt`、`updatedAt` |

## 4. 核心接口清单

### 4.x [接口名称]

- **Method**：`GET / POST`
- **URL**：`/api/xxx`
- **关键参数**：
  - `param1`：说明（必填 / 选填）
  - `param2`：说明
- **Response 结构**：
  ```json
  {
    "data": {
      "list": [{ "id": "...", "name": "..." }],
      "nextCursor": "..."
    }
  }
  ```

## 5. 可复用的 curl 示例

```bash
# [操作描述]（替换 Cookie 后可直接运行）
curl 'https://xxx.com/api/...' \
  -H 'Cookie: 替换为你的 Cookie'
```

## 6. 已知限制与坑

- 接口 X 有频率限制，建议请求间隔 Nms 以上
- 字段 Y 返回的是私有格式，需要额外处理
- 分页结束标志：`nextCursor` 为空字符串时表示最后一页

## 7. 集成开发建议

基于以上信息，应实现以下能力：

| 能力名称 | 描述 | 对应接口 |
|---|---|---|
| `list_xxx` | 列出所有资源 | 4.1 |
| `read_xxx` | 读取资源内容 | 4.2 |
| `search_xxx` | 搜索资源 | 4.3 |

认证方案：从环境变量读取 Token / Cookie，注入到每个请求的 Header 中。

## 8. 修订记录

| 版本 | 日期 | 变更人 | 变更说明 |
|---|---|---|---|
| v1.0 | [YYYY-MM-DD] | [作者] | 初稿 |
```

---

## 全程遵循的迭代原则

- **最小化假设**：每一个结论都要经过实际请求验证，不要靠猜测
- **增量探索**：先搞定认证，再搞列表，再搞内容读取，不要同时挖多个洞
- **优先复用登录态**：你在 Chrome 里操作，页面 Cookie 已经存在，直接在 Console 中 `fetch` 即可，无需模拟登录
- **实时记录**：每验证完一个接口，立刻写入经验文档
- **遇到加密不要硬磕**：优先从 DOM 读取已渲染内容，其次找页面内解密函数，最后才考虑逆向混淆代码
