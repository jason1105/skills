# Java 后端开发流水线 —— 跨角色共享规范

本文档被五个角色 SKILL 共同引用，定义整个流水线的共享约定。

---

## 1. 文档交付物规范

| 文档 | 创建阶段 | 负责角色 | 关键约束                  |
|------|---------|---------|-----------------------|
| REQUIREMENT.md | Phase 1 | requirement-analyst | 禁止包含 Java 类名、注解等技术细节  |
| DESIGN.md | Phase 2 | system-architect | DDL 必须完整，含字段注释和索引     |
| TODO.md | Phase 3 | task-planner | 单任务不超过 1 小时，基础设施任务最先  |
| Java 代码 | Phase 4 | spec-coder | 命名、结构与 DESIGN.md 严格一致 |

---

## 2. 统一响应格式

```json
{
  "retCode": "T200",
  "retMsg": "操作成功",
  "data": { }
}
```

**分页响应：**
```json
{
  "retCode": "T200",
  "retMsg": "操作成功",
  "data": {
    "datas": [],
    "rowCount": 221,
    "numPerPage": 20,
    "pageNum": 1,
    "totalPage": 12
  }
}
```

---

## 3. 通用错误码规范

| 错误码 | HTTP Status | 触发场景 |
|--------|------------|---------|
| PARAM_INVALID | 400 | @Valid 校验不通过 |
| NOT_FOUND | 404 | 数据库查询无结果 |
| FORBIDDEN | 403 | Spring Security 越权 |
| CONCURRENT_CONFLICT | 409 | 乐观锁版本冲突 |
| EXTERNAL_TIMEOUT | 502 | 第三方服务超时 |
| SYSTEM_ERROR | 500 | 未预期异常 |

业务错误码：`[模块大写]_[原因大写]`，例：`ORDER_STOCK_INSUFFICIENT`

---

## 4. 分页请求约定

**入参：**
- `pageNum`：当前页码，从 1 开始，默认 1
- `numPerPage`：每页数量，默认 20，最大 100

**Spring 用法：**
```java
TsiePageRequest pageable = TsiePageRequest.of(request.getPage() - 1, request.getPageSize());
```

---

## 5. Java 分层开发顺序（依赖方向）

```
BaseEntity / Result / ErrorCode / GlobalExceptionHandler
         ↓
    建表 Migration
         ↓
       Entity
         ↓
  EntityService和DAO
         ↓
        DTO
         ↓
    Service 接口
         ↓
    Controller（依赖接口）
         ↓
   Service 实现（业务逻辑）
         ↓
    集成（Redis/MQ/第三方）
         ↓
     单元测试 / 集成测试
```

---

## 6. 变更影响矩阵

| 变更文档 | 需要重新评估 |
|---------|------------|
| REQUIREMENT.md | DESIGN.md + TODO.md + 已有代码 |
| DESIGN.md（DDL 变动） | 新增 Migration + Entity + EntityService和DAO + 相关测试 |
| DESIGN.md（API 变动） | DTO + Controller + 相关测试 |
| TODO.md | 任务优先级和排期 |

---

## 7. 任务状态机

```
⬜ 待开始 → 🔄 进行中 → ✅ 已完成
               ↓
           🚫 阻塞中（注明原因和阻塞方）
               ↓
           🔄 继续（阻塞解除后）
```

---

## 8. Git Commit 规范

详细规范见：
`references/git-commit.md`