# 安全合规参考文档索引

本目录包含后端研发各阶段需要遵循的安全合规知识，拆分为 4 个文档按需加载。

## 文档清单

| 文档 | 内容 | 加载时机 |
|------|------|----------|
| `secure-coding.md` | 16 类代码安全漏洞的错误示例、修复对策、预防机制 | **实现阶段**必读 |
| `security-features.md` | 安全功能要求：认证、授权、审计、加密、会话管理、数据保护 | **详细设计**、**DDL 设计**时读取 |
| `penetration-defense.md` | 12 类渗透漏洞的防护要求和对策 | **详细设计**、**API 设计**时读取 |
| `compliance-testcases.md` | 等保二级/三级测试用例速查表 | **验证阶段**必读 |

## 各阶段加载指引

```
需求分解       → 不加载（不涉及安全实现细节）
详细设计       → security-features.md + penetration-defense.md
DDL 设计       → security-features.md（数据加密/脱敏部分）
API 接口设计   → penetration-defense.md（输入校验/XSS/CSRF 部分）
实现           → secure-coding.md（核心，逐条对照编码）
验证           → compliance-testcases.md + penetration-defense.md
沉淀           → 不加载
```

## 使用方式

1. 执行各阶段 skill 时，先读本索引确定需要加载哪些文档
2. 只加载当前阶段需要的文档，不要全部加载
3. 加载后在执行过程中逐条对照，确保产出物满足安全要求
