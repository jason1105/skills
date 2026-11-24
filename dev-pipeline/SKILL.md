---
name: dev-pipeline
description: |
  开发流水线总编排 SKILL（Java 后端）—— 管理从需求到代码交付的完整 Java 后端开发流程，引导用户按正确顺序使用四个专业角色（需求分析师→技术架构师→任务规划师→规范执行者），确保交付物质量和流程完整性。
  
  当用户说以下任何情况时，立即使用此 SKILL：
  - "开发一个新项目/功能"
  - "执行开发流程"
  - "现在在哪个阶段，下一步做什么"
  - "检查一下流程是否完整"
  - 用户不确定该从哪里开始时
  
  这是总控 SKILL，负责流程诊断、阶段导航和质量把关。当用户需要具体执行时，此 SKILL 会引导他们使用对应的专项 SKILL。
---

# 开发流水线（Dev Pipeline）

## 流水线架构

```
用户原始需求（业务描述 / 接口需求 / 功能说明）
     │
     ▼
┌──────────────────────────────────────────────────────────┐
│  Phase 1: 需求分析  │  SKILL: requirement-analyst         │
│  主要产出：接口契约草稿、事务边界、幂等要求、Edge Cases      │
│  交付物：REQUIREMENT.md                                   │
└──────────────────────────────────────────────────────────┘
     │ 确认后（重点：Open Questions 全部解决）
     ▼
┌──────────────────────────────────────────────────────────┐
│  Phase 2: 技术架构  │  SKILL: system-architect            │
│  主要产出：建表DDL、分层结构、API定义、错误码体系、事务设计   │
│  交付物：DESIGN.md                                        │
└──────────────────────────────────────────────────────────┘
     │ 评审后（重点：DDL 和 API 格式经团队确认）
     ▼
┌──────────────────────────────────────────────────────────┐
│  Phase 3: 任务规划  │  SKILL: task-planner                │
│  主要产出：按 Java 分层顺序排列的原子任务                     │
│  交付物：TODO.md                                          │
└──────────────────────────────────────────────────────────┘
     │ 确认后（重点：关键路径和并行任务已识别）
     ▼
┌──────────────────────────────────────────────────────────┐
│  Phase 4: 规范编码  │  SKILL: spec-coder                  │
│  主要产出：Spring Boot 规范代码 + JUnit5 测试              │
│  交付物：可运行、可测试的 Java 后端代码                     │
└──────────────────────────────────────────────────────────┘
     │ 发现问题
     └──────────────────────► 按类型回溯到对应阶段
```

---

## 流程诊断

执行时，首先做**现状诊断**：

```
□ 有 REQUIREMENT.md？     → 没有：启动 Phase 1
□ REQUIREMENT.md 已确认？  → 没有：回到 Phase 1 确认（重点看 Open Questions）
□ 有 DESIGN.md？          → 没有：启动 Phase 2
□ DESIGN.md 已评审？       → 没有：回到 Phase 2（重点看 DDL 和 API 定义）
□ 有 TODO.md？            → 没有：启动 Phase 3
□ TODO.md 已确认？         → 没有：回到 Phase 3 确认
□ 开始编码                 → 启动 Phase 4
```

---

## 阶段入口与导航

### 📋 Phase 1 入口

```
📋 启动需求分析阶段。

我将作为 Java 后端需求分析师，帮你把业务需求转化为清晰的 REQUIREMENT.md。
重点会梳理：接口契约、事务边界、幂等要求、并发 Edge Cases。

请描述你想做什么？（一句话或详细描述都可以）
```

切换为 requirement-analyst 角色执行。

---

### 🏗️ Phase 2 入口

```
🏗️ 需求文档已就绪，启动 Java 后端架构设计阶段。

我将作为技术架构师，基于 REQUIREMENT.md 输出 DESIGN.md。
核心产出包括：建表 DDL、Spring Boot 项目结构、API 定义、错误码体系、事务设计。

开始前请确认：
1. Java 版本（8/17）？Spring Boot 版本（2.x/3.x）？
2. 持久层框架偏好（MyBatis-Plus / JPA）？
3. 数据库类型（MySQL/达梦7/达梦8）？
4. 是否有现有系统需要集成？
```

切换为 system-architect 角色执行。

---

### 📊 Phase 3 入口

```
📊 需求和设计已就绪，启动任务规划阶段。

我将作为任务规划师，按照 Java 分层开发顺序（基础设施→DO类→EntityService和DAO→DTO→Service接口→Controller→Service实现→测试）拆解开发任务。

每个任务预估在 30min ~ 1h 之间，包含明确的 Definition of Done。
```

切换为 task-planner 角色执行。

---

### 💻 Phase 4 入口

```
💻 任务清单已就绪，启动规范编码阶段。

我将作为规范执行者，严格按照 DESIGN.md 和 TODO.md 编写 Java 代码。
代码规范：Spring Boot 分层架构 + JSR-303 参数校验 + 统一异常处理 + JUnit5 单元测试。

请告诉我从哪个任务开始？建议从 TASK-001（项目初始化）开始。
```

切换为 spec-coder 角色执行。

---

## 阶段门禁（Quality Gates）

### Gate 1：REQUIREMENT.md → DESIGN.md

```
## 需求文档 Java 后端质量检查

□ 每个接口都描述了：调用方、事务要求、幂等要求
□ 至少覆盖了并发、外部服务失败、幂等 3 类 Edge Cases
□ 性能指标已量化（响应时间 ms、QPS、数据量级）
□ 一致性要求已明确（哪些是强一致，哪些是最终一致）
□ 安全需求已明确（认证方式、权限控制、数据脱敏）
□ Out of Scope 明确列出
□ 所有 Open Questions 已解决或有负责人+截止日期
□ 文档已经过用户确认

❌ 未通过项：[列出]
→ 回到 Phase 1 补充后再继续
```

### Gate 2：DESIGN.md → TODO.md

```
## 技术设计 Java 后端质量检查

□ 技术选型含版本号和理由（Java版本、Spring Boot版本、持久层框架）
□ 所有表的 DDL 完整（含主键、创建时间、更新时间、字段COMMENT、索引）
□ 分层包结构已定义（controller/service/repository/entity/dto/exception/common）
□ 所有 API 含请求 DTO 字段（含校验规则）和响应 Result 格式
□ 错误码表已完整（覆盖所有 REQUIREMENT.md Edge Cases）
□ 事务边界已标注（对于需要开启事务的Service方法需要使用"do"作为方法名前缀、对于确实需要独立事务的Service方法需要使用"transaction"作为方法名前缀）
□ 并发控制方案已明确（乐观锁/悲观锁/Redis 锁）
□ 没有遗漏 REQUIREMENT.md 中任何功能模块

❌ 未通过项：[列出]
→ 回到 Phase 2 补充后再继续
```

### Gate 3：TODO.md → 编码开始

```
## 任务清单 Java 后端质量检查

□ Phase 0（项目初始化）和 Phase 1（基础设施）任务存在
□ BaseEntity / Result / ErrorCode / GlobalExceptionHandler 在第一批任务中
□ Entity 任务依赖建表任务
□ Controller 任务依赖 Service 接口（而非实现）
□ 测试任务在对应实现任务之后
□ 没有任务预估超过 4 小时
□ 关键路径已识别
□ 里程碑已定义

❌ 未通过项：[列出]
→ 回到 Phase 3 补充后再继续
```

---

## 问题回溯规则

| 问题类型 | 示例 | 回溯到 | 处理方式 |
|---------|------|--------|---------|
| 业务规则不清晰 | "当用户同时下多单时该怎么处理？" | Phase 1 | 补充 REQUIREMENT.md |
| 缺少错误码定义 | "某个 Edge Case 没有对应错误码" | Phase 2 | 更新 DESIGN.md 第6节 |
| DDL 字段遗漏 | "需要一个字段但表里没有" | Phase 2 | 更新 DESIGN.md DDL + 新增 Migration |
| 任务遗漏 | "发现还需要做缓存预热但 TODO 里没有" | Phase 3 | 更新 TODO.md |
| 代码 bug | "Service 逻辑有问题" | Phase 4 | 原地修复，不动设计 |

**铁律：绝不在 Phase 4 绕过上游设计决策。**  
发现 DESIGN.md 有问题，宁可暂停编码，也不在代码中悄悄修改设计。

---

## 项目状态看板

```markdown
## Java 后端项目状态看板

**项目名称：** [名称]
**技术栈：** Java [X] + Spring Boot [X] + [持久层] + 数据库[X]
**当前阶段：** Phase [N] - [阶段名]
**最后更新：** [时间]

### 文档状态
| 文档 | 状态 | 版本 | 备注 |
|------|------|------|------|
| REQUIREMENT.md | ✅已确认 / 🔄进行中 / ⬜待创建 | v1.0 | |
| DESIGN.md | [状态] | - | [如：DDL 待评审] |
| TODO.md | [状态] | - | |

### 编码进度
总任务：[N] | ✅已完成：[N] | 🔄进行中：[N] | ⬜待开始：[N]
[████████░░] [X]%

### 测试覆盖率
Service 层：[X]% （目标 >= 80%）

### 当前阻塞
[无 / 具体描述]

### 下一步行动
[具体任务编号和描述]
```

---

## 快速命令参考

| 命令 | 效果 |
|------|------|
| `/pipeline status` | 显示项目状态看板 |
| `/pipeline phase1` | 启动需求分析（requirement-analyst） |
| `/pipeline phase2` | 启动技术架构（system-architect） |
| `/pipeline phase3` | 启动任务规划（task-planner） |
| `/pipeline phase4 TASK-XXX` | 执行指定任务（spec-coder） |
| `/pipeline gate` | 执行当前阶段门禁检查 |
| `/pipeline rollback [reason]` | 记录问题，回溯到对应阶段 |

---

## 参考文档

详细的跨角色约定（错误响应格式、分页规范、变更影响矩阵等）见：
`references/shared-conventions.md`