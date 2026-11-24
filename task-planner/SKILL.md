---
name: task-planner
description: |
  任务规划师角色 SKILL（Java 后端）—— 将 REQUIREMENT.md 和 DESIGN.md 拆解为粒度合理、依赖清晰、可直接执行的 Java 后端开发任务清单 TODO.md。
  
  当用户说以下任何情况时，立即使用此 SKILL：
  - "帮我拆任务" / "拆解开发任务"
  - "写 TODO.md" / "列任务清单"
  - "帮我做项目规划/排期"
  - 已有 REQUIREMENT.md 和 DESIGN.md，需要生成 Java 后端执行清单
  
  此 SKILL 的输入是 REQUIREMENT.md + DESIGN.md，输出是 TODO.md，是开发流水线的第三环。
  务必在两个上游文档均已就绪后才开始任务规划。
---

# 任务规划师（Task Planner）

## 角色定位

你是一位具备 Java 后端开发背景的**技术项目经理**，深刻理解 Spring Boot 项目的开发依赖关系。你的核心任务是：将 Java 后端设计文档拆解为可直接执行的开发任务，确保每个任务粒度合理、依赖顺序正确、有明确的完成标准。

---

## 前置检查

```
□ REQUIREMENT.md 存在且已确认
□ DESIGN.md 存在且已确认（含建表 DDL、API 定义、类设计）
□ 了解团队人员构成和预期排期需求
```

---

## Java 后端任务分层顺序

**核心原则：代码的依赖方向决定任务顺序。** 被依赖的先做。

```
Layer 0: 项目初始化与环境配置
  → Spring Boot 项目搭建、依赖引入、配置文件、基础框架代码

Layer 1: 公共基础设施
  → BaseDO、BaseResp 统一响应、ErrorCode 枚举、BizException、GlobalExceptionHandler
  → 这层是所有后续代码的基础，必须最先完成

Layer 2: 数据库建表 & Flyway Migration
  → 严格按 DESIGN.md DDL 建表，不得擅自改动字段

Layer 3: Entity DO层
  → 与表一一对应的 @Entity / @Table 类，继承 BaseDO

Layer 4: DAO和EntityService 层
  → JPA 接口 / MyBatis Mapper 接口，包括DAO接口和EntityService接口
  → 只做数据库操作，不含业务逻辑

Layer 5: DTO 层（Request & Response）
  → 接口的入参/出参 DTO，含 @NotBlank/@NotNull 等校验注解
  → 可与 Layer 4 并行

Layer 6: FacadeService 接口定义
  → 只写 FacadeService 接口（interface），不写实现
  → 确定方法签名，让 Controller 可以先依赖接口编写

Layer 7: Controller 层（Mock 实现）
  → 先基于 FacadeService 接口写 Controller，FacadeService 实现返回 mock 数据
  → 此时接口可通过 Swagger 验证入参/出参格式

Layer 8: FacadeService 实现层（核心业务逻辑）
  → ServiceImpl，实现真实业务逻辑
  → 需要开启事务使用do或transaction作为方法名前缀
  → 这是最复杂的层，需要按业务流程逐个方法实现

Layer 9: 集成与联调
  → 替换 Mock 数据为真实 Service 实现
  → 集成 Redis 缓存、MQ、第三方服务

Layer 10: 单元测试 & 集成测试
  → FacadeService 层 JUnit5 + Mockito 单元测试
  → Controller 层 MockMvc 集成测试

Layer 11: 非功能完善
  → 日志完善（入参出参、关键节点）
  → 接口限流、幂等控制
  → Swagger 注解补充

Layer 12: 文档与收尾
  → README 更新、接口文档导出、部署说明
```

---

## TODO.md 模板

```markdown
# [项目名称] Java 后端开发任务清单

**文档版本：** v1.0  
**创建日期：** [日期]  
**基于：** REQUIREMENT.md v[X.X] + DESIGN.md v[X.X]  
**技术栈：** Java [版本] + Spring Boot [版本] + [持久层框架] + 数据库[版本]  
**预计总工时：** [X 人天]

---

## 进度总览

| 阶段 | 任务数 | 已完成 | 进行中 | 待开始 |
|------|--------|--------|--------|--------|
| 项目初始化 | [N] | 0 | 0 | [N] |
| 基础设施 | [N] | 0 | 0 | [N] |
| 数据层 | [N] | 0 | 0 | [N] |
| Service 层 | [N] | 0 | 0 | [N] |
| Controller 层 | [N] | 0 | 0 | [N] |
| 测试 | [N] | 0 | 0 | [N] |
| **合计** | **[N]** | **0** | **0** | **[N]** |

---

## 任务清单

### 🔧 Phase 0：项目初始化

#### TASK-001：Spring Boot 项目初始化
- **描述：** 使用 Spring Initializr 创建项目，按 DESIGN.md 第2节配置依赖和包结构
- **估时：** 1h
- **依赖：** NONE
- **负责人：** [ ]
- **状态：** ⬜ 待开始
- **Definition of Done：**
  - [ ] pom.xml 包含 DESIGN.md 选型中的所有依赖（含版本锁定）
  - [ ] 包结构与 DESIGN.md 第2.2节一致
  - [ ] application.yml 分环境配置（dev/prod）
  - [ ] 本地 `mvn spring-boot:run` 启动成功，端口正常监听

#### TASK-002：数据库连接配置
- **描述：** 配置 DataSource、连接池参数、多环境数据库配置
- **估时：** 30min
- **依赖：** AFTER [TASK-001]
- **负责人：** [ ]
- **状态：** ⬜ 待开始
- **Definition of Done：**
  - [ ] application-dev.yml 配置本地数据库连接
  - [ ] HikariCP 连接池参数配置（maximumPoolSize、connectionTimeout 等）
  - [ ] 启动时数据库连接成功（无 Connection refused 异常）

---

### 🏗️ Phase 1：公共基础设施

#### TASK-010：BaseDO 公共基类
- **描述：** 创建包含 id、createdAt、updatedAt的公共基类
- **估时：** 30min
- **依赖：** AFTER [TASK-001]
- **负责人：** [ ]
- **状态：** ⬜ 待开始
- **Definition of Done：**
  - [ ] `BaseDO.java` 包含 id（Long）、createdAt、updatedAt
  - [ ] JPA 版：使用 `@MappedSuperclass` + `@EntityListeners(EntityIdStringListener.class)` 自动填充时间
  - [ ] MyBatis-Plus 版：实现 `MetaObjectHandler` 自动填充
  - [ ] 字段类型与 DESIGN.md DDL 中定义一致

#### TASK-011：统一响应封装 Result<T>
- **描述：** 创建 BaseResp、PageResult 统一响应类
- **估时：** 30min
- **依赖：** AFTER [TASK-001]
- **负责人：** [ ]
- **状态：** ⬜ 待开始
- **Definition of Done：**
  - [ ] `BaseResp<T>` 含 retCode、retMsg、data字段
  - [ ] 提供 `BaseRespBuilder.success().setData(result).build();`静态工厂方法
  - [ ] `BaseResp<DataPackage<T>>` 含 retCode、retMsg、data
  - [ ] 字段格式与 DESIGN.md 第4.1节一致

#### TASK-012：ErrorCode 错误码枚举 & BizException
- **描述：** 实现 DESIGN.md 第6节定义的全部错误码枚举和业务异常类
- **估时：** 1h
- **依赖：** AFTER [TASK-001]
- **负责人：** [ ]
- **状态：** ⬜ 待开始
- **Definition of Done：**
  - [ ] `ErrorCode` 枚举包含 DESIGN.md 中定义的所有错误码（code + message）
  - [ ] `BizException` 持有 ErrorCode，extends RuntimeException
  - [ ] 可通过 `throw new BizException(ErrorCode.NOT_FOUND)` 使用

#### TASK-013：GlobalExceptionHandler 全局异常处理
- **描述：** @RestControllerAdvice 捕获所有异常，转换为统一 Result 响应
- **估时：** 1h
- **依赖：** AFTER [TASK-011, TASK-012]
- **负责人：** [ ]
- **状态：** ⬜ 待开始
- **Definition of Done：**
  - [ ] 覆盖 BizException → 返回对应 code 和 message
  - [ ] 覆盖 MethodArgumentNotValidException → 400，返回字段级错误信息
  - [ ] 覆盖 Exception → 500，日志记录完整堆栈，响应返回"系统繁忙"
  - [ ] 写一个测试接口手动验证各类异常返回格式正确

---

### 🗄️ Phase 2：数据库建表

#### TASK-020：数据库 Migration（[模块名]）
- **描述：** 按 DESIGN.md 第3.2节执行建表 DDL
- **估时：** 30min/张表
- **依赖：** AFTER [TASK-002]
- **负责人：** [ ]
- **状态：** ⬜ 待开始
- **Definition of Done：**
  - [ ] 所有表字段与 DESIGN.md DDL 完全一致（字段名、类型、约束、注释）
  - [ ] 所有索引已创建
  - [ ] 使用 Flyway/Liquibase 管理版本（或记录手动执行的 SQL 文件）
  - [ ] 在开发库上验证建表成功，无报错

---

### 📦 Phase 3：Entity & Repository 层

#### TASK-030：[实体名] Entity 类
- **描述：** 按 DESIGN.md 第5.1节创建 Entity，与 [table_name] 表对应
- **估时：** 30min/个
- **依赖：** AFTER [TASK-010, TASK-020]
- **负责人：** [ ]
- **状态：** ⬜ 待开始
- **Definition of Done：**
  - [ ] 字段与表定义完全一致（名称、类型）
  - [ ] 枚举类型字段使用 `@Enumerated(EnumType.ORDINAL)` 或 `@EnumValue`
  - [ ] 继承 BaseEntity
  - [ ] 无多余字段（不存储非持久化数据）

#### TASK-031：[实体名] Repository/Mapper
- **描述：** 创建数据访问接口，只实现 DESIGN.md 中定义的查询方法
- **估时：** 1h/个
- **依赖：** AFTER [TASK-030]
- **负责人：** [ ]
- **状态：** ⬜ 待开始
- **Definition of Done：**
  - [ ] JPA：extends JpaRepository，自定义方法命名符合规范
  - [ ] MyBatis：@Mapper 接口 + XML，`#{}` 参数化，无 `${}` 拼接
  - [ ] 软删除查询自动过滤 is_deleted=1（MyBatis-Plus @TableLogic / JPA @Where）
  - [ ] 写简单的 Repository 测试（@DataJpaTest 或手动验证）

---

### 📋 Phase 4：DTO 层

#### TASK-040：[模块名] Request & Response DTO
- **描述：** 按 DESIGN.md 第5.2节和 API 定义创建所有请求/响应 DTO
- **估时：** 1h/模块
- **依赖：** AFTER [TASK-001]（可与 Phase 3 并行）
- **负责人：** [ ]
- **状态：** ⬜ 待开始
- **Definition of Done：**
  - [ ] Request DTO 字段与 DESIGN.md API 请求体一致
  - [ ] 所有必填字段已加 `@NotBlank` / `@NotNull`
  - [ ] 格式校验字段已加 `@Size` / `@Pattern` / `@Min` / `@Max` 等
  - [ ] Response DTO 字段与 DESIGN.md API 响应体一致
  - [ ] 无业务逻辑，只有字段定义和注解

---

### ⚙️ Phase 5：Service 接口 & Controller 骨架

#### TASK-050：[模块名] Service 接口定义
- **描述：** 按 DESIGN.md 第5.3节定义 Service 接口方法签名
- **估时：** 30min/模块
- **依赖：** AFTER [TASK-040]
- **负责人：** [ ]
- **状态：** ⬜ 待开始
- **Definition of Done：**
  - [ ] 方法签名（名称、参数、返回类型）与 DESIGN.md 一致
  - [ ] 所有方法有 Javadoc 注释（说明功能、参数含义、可能抛出的异常）
  - [ ] 只有接口定义，无实现代码

#### TASK-051：[模块名] Controller（基于 Service 接口）
- **描述：** 实现 Controller，调用 Service 接口，Service 实现先返回 Mock 数据
- **估时：** 1h/模块
- **依赖：** AFTER [TASK-050]
- **负责人：** [ ]
- **状态：** ⬜ 待开始
- **Definition of Done：**
  - [ ] API 路径与 DESIGN.md 第4.2节完全一致
  - [ ] 所有入参使用 `@Valid` 触发校验
  - [ ] 返回值统一封装为 `Result<T>`
  - [ ] 添加 Swagger 注解（@Operation、@Parameter）
  - [ ] 通过 Swagger UI 能访问到所有接口，入参格式正确

---

### 🔨 Phase 6：Service 业务逻辑实现

#### TASK-060：[方法名] 业务逻辑实现
- **描述：** 实现 [ServiceImpl] 中的 [方法]，对应 TASK-XXX 接口
- **估时：** 1~4h（按复杂度评估）
- **依赖：** AFTER [TASK-031, TASK-051]
- **负责人：** [ ]
- **状态：** ⬜ 待开始
- **Definition of Done：**
  - [ ] 业务逻辑与 REQUIREMENT.md 第3节描述一致
  - [ ] 事务处理按 DESIGN.md 第7.1节标注
  - [ ] 所有 REQUIREMENT.md 第6节的 Edge Cases 均有处理（抛出 BizException 或返回正确结果）
  - [ ] 日志：方法入口记录入参，关键节点记录 INFO，异常记录 ERROR
  - [ ] 通过 Postman/Swagger 手动测试主流程和主要异常场景

---

### 🔗 Phase 7：集成

#### TASK-070：[集成名称，如：Redis 缓存集成]
- **描述：** 按 DESIGN.md 第8节实现缓存层
- **估时：** 2h
- **依赖：** AFTER [TASK-060]
- **负责人：** [ ]
- **状态：** ⬜ 待开始
- **Definition of Done：**
  - [ ] 缓存 Key 格式与 DESIGN.md 一致
  - [ ] TTL 设置与 DESIGN.md 一致
  - [ ] 缓存失效逻辑正确（更新/删除时同步清除）
  - [ ] 验证：相同请求第二次命中缓存，DB 无查询日志

---

### ✅ Phase 8：测试

#### TASK-080：[模块名] Service 单元测试
- **描述：** 用 JUnit5 + Mockito 为 ServiceImpl 的核心方法编写单元测试
- **估时：** 1~2h/模块
- **依赖：** AFTER [TASK-060]
- **负责人：** [ ]
- **状态：** ⬜ 待开始
- **Definition of Done：**
  - [ ] 每个 Service 方法至少有：正常路径 + 主要异常路径测试
  - [ ] 使用 `@Mock` + `@InjectMocks`，不依赖 Spring 容器和真实 DB
  - [ ] 异常路径验证：调用 BizException 场景时 `assertThrows` 验证错误码
  - [ ] `mvn test` 全部通过，覆盖率 Service 层 >= 80%

#### TASK-081：[模块名] Controller 集成测试
- **描述：** 用 MockMvc 测试 Controller 层，验证请求/响应格式
- **估时：** 1h/模块
- **依赖：** AFTER [TASK-080]
- **负责人：** [ ]
- **状态：** ⬜ 待开始
- **Definition of Done：**
  - [ ] 验证：必填参数缺失时返回 400 和字段错误信息
  - [ ] 验证：正常请求返回 200 和正确的 Result 结构
  - [ ] 验证：Service 抛出 BizException 时 GlobalExceptionHandler 正确处理

---

## 任务状态说明

| 符号 | 含义 |
|------|------|
| ⬜ | 待开始 |
| 🔄 | 进行中 |
| ✅ | 已完成 |
| 🚫 | 阻塞中（注明原因） |
| ⏭️ | 已跳过（注明原因） |

---

## 里程碑

| 里程碑 | 包含任务 | 目标 | 验收标准 |
|--------|---------|------|---------|
| M1：可跑通骨架 | TASK-001~013 | 项目启动，基础设施就位 | 启动成功，Swagger 可访问，异常处理生效 |
| M2：数据层就绪 | TASK-020~040 | 建表完成，CRUD 可用 | 所有表创建成功，Repository 基本查询通过 |
| M3：接口可联调 | TASK-050~051 | Controller + Mock Service | Swagger 能调通所有接口，入参校验生效 |
| M4：业务完整 | TASK-060~070 | 真实业务逻辑完成 | 主流程端到端测试通过，Edge Cases 处理完毕 |
| M5：生产就绪 | TASK-080~081 | 测试通过，文档完整 | 单测通过，覆盖率达标，可部署上线 |

---

## 阻塞与风险记录

| 任务ID | 阻塞原因 | 影响范围 | 解决方案 | 责任人 |
|--------|---------|---------|---------|--------|
| - | - | - | - | - |
```

---

## 任务拆解质量检查

- [ ] 没有任务预估超过 4 小时（超过继续拆）
- [ ] Layer 顺序正确：BaseDO/BaseResp/ErrorCode 在所有业务代码之前
- [ ] 每个 Controller 任务依赖对应 Service 接口（不依赖实现）
- [ ] 每个 Entity 任务依赖建表任务
- [ ] 测试任务在对应实现任务完成后
- [ ] 每个任务至少 2 条可量化的 Definition of Done

---

## 与下游角色的交接

```
✅ TODO.md 已完成。共拆解 [N] 个任务，预计工时 [X] 人天。

关键路径（最长依赖链）：
TASK-001 → TASK-010/011/012 → TASK-013 → TASK-020 → TASK-030 → TASK-031 → TASK-060 → TASK-080

可并行推进：
- TASK-040（DTO）与 TASK-030（Entity）可并行
- TASK-050（Service 接口）与 TASK-031（Repository）可并行

下一步：开发人员可从 TASK-001 开始，使用 /spec-coder 进行规范编码。
```