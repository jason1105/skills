# 后端编码规范（业内最佳实践基线）

> **本文件是基于业内通用最佳实践整理的基线模板**，技术栈无关。团队应在此基础上根据项目实际情况裁剪、扩展。如团队已有内部规范，**团队规范优先**，本文件作为补充参考。
>
> 执行 `backend-implementation` 时，Step 1 会加载本文件。如需替换规范，将团队规范覆盖本文件内容即可。

---

## 1. 命名规范

### 1.1 通用原则

- **见名知意**：变量、方法、类的名字应清晰表达意图，避免缩写（行业通用缩写如 `id`、`url`、`dto` 除外）
- **避免无意义命名**：`data`、`info`、`temp`、`obj`、`a1` 等模糊名字禁止使用
- **布尔变量**：以 `is`、`has`、`can`、`should` 开头，如 `isActive`、`hasPermission`
- **避免否定命名**：用 `isValid` 而非 `isNotInvalid`

### 1.2 各语言标识符风格

| 语言 | 类/类型 | 方法/函数 | 变量 | 常量 |
|------|---------|----------|------|------|
| Java / Kotlin | PascalCase | camelCase | camelCase | UPPER_SNAKE_CASE |
| Go | PascalCase（导出）/ camelCase（内部）| 同左 | 同左 | 同左 |
| Python | PascalCase | snake_case | snake_case | UPPER_SNAKE_CASE |
| TypeScript | PascalCase | camelCase | camelCase | UPPER_SNAKE_CASE |

### 1.3 业务分层命名

各层对象后缀约定如下，**团队保持统一，不混用**：

| 后缀 | 含义 | 用途 | 示例 |
|------|------|------|------|
| `DO` | DomainEntity，领域实体 | 与数据库表映射的持久层对象 | `OrderDO`、`UserDO` |
| `DTO` | Data Transfer Object | 跨层或跨服务传输（无展示逻辑）| `OrderDTO`、`UserDTO` |
| `VO` | View Object | 响应前端的展示对象（含格式化）| `OrderVO`、`UserVO` |
| `Request` | 请求入参 | HTTP 请求体或方法入参 | `CreateOrderRequest` |
| `Response` | 响应出参 | HTTP 响应体 | `OrderListResponse` |
| `Cmd` / `Query` | 命令 / 查询 | CQRS 风格（按团队约定可选）| `CreateOrderCmd` |

> **不使用** `Entity`、`PO`（Persistence Object）作为后缀。

### 1.4 枚举规范

所有枚举类遵循以下固定写法：

- **类名**：`XxxEnum`，以 `Enum` 结尾
- **实现接口**：`implements TsieEnum`（框架接口，要求实现 `getId()` / `getText()`）
- **字段**：固定两个字段 `Integer id`（数字编码）和 `String text`（中文描述）
- **常量注释**：每个枚举常量上方必须有 Javadoc 注释，说明其业务含义
- **内部转换器**：必须包含 `Convertor` 静态内部类，继承 `TsieEnumTypeConvertor<XxxEnum>`，`getDefault()` 返回 `null`
- **查找方法**：提供 `findById(String id)` 和 `findType(String type)` 两个静态方法，均需做入参非空判断

```java
public enum OrderStateEnum implements TsieEnum {
    /**
     * 待支付
     */
    PENDING(0, "待支付"),
    /**
     * 已完成
     */
    COMPLETED(1, "已完成"),
    /**
     * 已取消
     */
    CANCELLED(2, "已取消");

    private Integer id;
    private String text;

    OrderStateEnum(Integer id, String text) {
        this.id = id;
        this.text = text;
    }

    @Override
    public Integer getId() { return id; }

    @Override
    public String getText() { return text; }

    /** 自定义转换器 **/
    public static class Convertor extends TsieEnumTypeConvertor<OrderStateEnum> {
        @Override
        protected OrderStateEnum getDefault() { return null; }
    }

    public static OrderStateEnum findById(String id) {
        if (id == null) return null;
        return Objects.requireNonNull(Arrays.stream(OrderStateEnum.values())
            .filter(it -> it.getId().equals(Integer.valueOf(id)))
            .findAny().orElse(null));
    }

    public static OrderStateEnum findType(String type) {
        if (StringUtils.isEmpty(type)) return null;
        return Objects.requireNonNull(Arrays.stream(OrderStateEnum.values())
            .filter(it -> it.getText().equals(type))
            .findAny().orElse(null));
    }
}
```

---

## 2. 代码组织

- **单一职责**：一个类只做一件事；类行数超过 300 行时考虑拆分
- **方法简洁**：一个方法只完成一个逻辑步骤；方法超过 50 行时考虑提取
- **圈复杂度 ≤ 10**：if / for / switch 嵌套总数超出时重构
- **单向依赖**：Controller → Service → Repository，禁止反向依赖；跨层直接调用时向上汇报
- **避免魔法值**：数字和字符串字面量必须抽取为命名常量

---

## 3. 注释与文档

### 3.1 何时写注释

- **必须写**：公开 API、复杂算法、业务规则的非显然约束、临时方案（标 `TODO/FIXME`）
- **不写**：能从命名直接读出的事实（如 `// 设置用户名` 紧跟 `setUserName()`）
- **避免**：用注释解释烂代码——重命名或重构才是正解

### 3.2 公开接口文档

| 语言 | 要求 |
|------|------|
| Java | 所有 `public` 类/接口/方法有 Javadoc，含 `@param`、`@return`、`@throws` |
| Go | 所有导出标识符有 godoc 注释，以标识符名开头 |
| Python | 公开函数/类有 docstring（Google 或 NumPy 风格）|
| TypeScript | 导出类型/函数有 JSDoc 或 TSDoc |

### 3.3 TODO / FIXME 规范

```
// TODO(负责人, 2026-06): 补充批量导出接口
// FIXME(负责人, 2026-06): 此处 N+1 查询待优化
```

必须包含**责任人**和**预计处理日期**，否则不允许合入主干。

---

## 4. 异常与错误处理

- **不吞异常**：禁止 `catch (Exception e) {}` 空块，也禁止只打 `e.printStackTrace()`
- **就近处理或显式上抛**：能降级/重试就处理，不能处理就向上抛（带上下文信息）
- **不用异常做流程控制**：正常业务分支不抛异常
- **错误码全局唯一**：推荐格式 `{模块}-{级别}-{编号}`（如 `ORDER-E-001`），可枚举、可文档化
- **用户友好报错**：面向用户的错误信息不含堆栈；原始异常仅打日志
- **边界校验**：所有外部输入（HTTP 参数、消息体、文件）必须校验非空、长度、格式、范围；校验失败抛业务异常，不直接暴露 NPE

---

## 5. 日志规范

### 5.1 级别使用

| 级别 | 场景 |
|------|------|
| `ERROR` | 业务受影响、需人工介入；必须包含完整堆栈 |
| `WARN` | 可恢复异常、降级、即将达到阈值 |
| `INFO` | 关键业务节点（订单创建、支付完成）、服务启停 |
| `DEBUG` | 开发调试；生产环境关闭 |

### 5.2 内容要求

- **必须包含**：时间戳、级别、线程、traceId（如有链路追踪）、关键业务标识（订单号、用户ID）
- **禁止**：明文打印密码、token、手机号、身份证、银行卡（需脱敏后打印）
- **避免**：循环内 INFO 日志、字符串拼接（用占位符）

```java
// ✓ 占位符 + 业务 ID
log.info("订单创建成功 orderId={} userId={}", orderId, userId);
// ✓ 异常作最后参数，框架自动打堆栈
log.error("订单创建失败 orderId={}", orderId, e);

// ✗ 字符串拼接，性能差且丢失结构
log.info("订单创建成功" + orderId);
// ✗ 只打 message，丢失堆栈
log.error("失败: " + e.getMessage());
```

---

## 6. 配置管理

- **不硬编码**：URL、超时、阈值、密钥等全部走配置文件或配置中心
- **环境隔离**：dev / test / staging / prod 配置分离，禁止生产配置混入代码仓库
- **敏感信息加密**：密钥、密码必须走 Vault / KMS 或加密配置，禁止明文进 Git
- **合理默认值**：配置缺失时应有安全的默认值，或立即 fast-fail 并给出明确提示

---

## 7. 单元测试

### 7.1 覆盖范围

- Service 层所有业务方法**必须**有单元测试
- 核心算法、边界条件、异常路径必测
- 行覆盖率 ≥ 70%，分支覆盖率 ≥ 60%（团队可调整）

### 7.2 编写原则

- **AAA 结构**：Arrange（准备数据）→ Act（执行）→ Assert（断言）
- **一个测试一个断言意图**：避免一个测试方法验证多个无关行为
- **独立性**：测试间不共享可变状态，任意顺序可执行
- **速度**：单元测试 ≤ 100 ms；依赖外部服务的归类为集成测试

### 7.3 命名

```
methodName_scenario_expectedResult
Examples:
  createOrder_insufficientStock_throwsBusinessException
  findUser_userExists_returnsUser
  findUser_userNotFound_returnsEmpty
  updateOrder_orderAlreadyCancelled_throwsBusinessException
```

---

## 8. 安全编码

### 8.1 输入验证

- **白名单优于黑名单**：枚举允许值，拒绝其余所有输入
- **防 SQL 注入**：使用参数化查询 / 预编译语句，禁止字符串拼接 SQL
- **防 XSS**：输出到前端的内容做 HTML 转义
- **防路径穿越**：禁止用户输入直接拼文件路径
- **防 SSRF**：禁止用户输入控制后端发起的 URL

### 8.2 认证与授权

- **默认拒绝原则**：接口默认拒绝访问，显式授权才开放
- Token 在统一拦截器 / 过滤器校验，不依赖业务代码自查
- **越权检查**：不仅校验"是否登录"，还要校验"是否有权访问该资源"
- 不在 URL 中传敏感信息，改用 Header 或 Body

### 8.3 数据保护

- 敏感字段加密存储（手机号、身份证、银行卡号）
- 日志和响应中敏感字段脱敏（如 `138****8888`）
- 密码等凭据不进代码仓库，统一走配置中心或环境变量

### 8.4 依赖安全

- 定期扫描三方依赖漏洞（Maven / npm / pip 安全扫描）
- 不使用已知漏洞或已停止维护的库
- 锁定依赖版本（lock 文件），避免不可预期的升级

---

## 9. 性能与并发

### 9.1 数据库

- **禁止 JOIN 查询**：所有查询必须针对单表；多表关联数据在 Service 层通过多次单表查询后在应用层组装，不在 SQL 层做 JOIN
- **避免 N+1**：批量查询替代循环单查，使用 `IN` 批量 + 应用层 Map 聚合的方式替代 JOIN
- **必加索引**：`WHERE`、`ORDER BY` 字段须评估索引；监控慢查询
- **事务最小化**：事务范围仅覆盖必要的写操作；禁止在事务内调用外部 HTTP/RPC
- **分页强制**：列表接口必须分页，禁止全表扫描返回

### 9.2 缓存

- 缓存键规范命名：`{业务}:{对象}:{ID}`（如 `user:profile:1001`）
- 防击穿 / 穿透 / 雪崩：互斥锁、空值缓存、过期时间打散
- 缓存与 DB 一致性：写后失效（Cache-Aside）优于写后更新

### 9.3 并发

- **不显式 `new Thread`**：使用线程池；不同业务使用独立线程池，避免相互影响
- **共享状态必须同步**：static 字段、单例被多线程修改时必须加锁或使用并发容器
- **加锁顺序一致**：多把锁时固定获取顺序，避免死锁
- **超时必设**：所有外部调用（HTTP、RPC、DB 查询）必须配置超时

### 9.4 资源管理

- IO 资源（文件、连接、流）使用 try-with-resources / `defer` / context manager 确保关闭
- 连接池大小需经过压测；DB 连接池建议 ≤ CPU 核数 × 2 + 有效磁盘数

---

## 10. 数据库访问

- **迁移工具版本化**：建表 / 改表通过迁移工具（Flyway、Liquibase、Alembic 等）管理，不在代码中执行 DDL
- **向后兼容迁移**：新增字段允许 NULL 或有默认值；删除字段先停用再删
- **单表查询**：所有 SQL 只查单表，禁止在 SQL 层写 JOIN；多表关联在应用层完成
- **ORM 慎用**：复杂查询建议手写 SQL，避免性能不可控；避免全字段 `SELECT *`
- **事务边界显式标注**：使用 `@Transactional` 或显式 BEGIN / COMMIT，不依赖框架隐式行为

---

## 11. API 设计

### 11.1 URL 命名

- **路径风格**：统一业务前缀（通过常量配置，如 `AppConfigConstants.MAPPING_PREFIX`），路径各段使用 **camelCase**，不使用中划线或下划线
- **资源描述**：用名词描述资源，如 `/{prefix}/powerDecomposition`、`/{prefix}/section`、`/{prefix}/planPublish`
- **操作描述**：在资源路径后追加动词短语，如 `/{prefix}/year/getSystemData`、`/{prefix}/planPublish/log/list`
- **无版本号**：当前项目不使用 URL 版本号

```
/{prefix}/{resource}                     ← 资源根路径
/{prefix}/{resource}/{action}            ← 带操作的路径
/{prefix}/{resource}/{subResource}/list  ← 子资源列表
```

### 11.2 HTTP 方法

**所有接口只允许使用 `GET` 或 `POST`，禁止使用 `PUT`、`DELETE`、`PATCH` 及其他 HTTP 方法。**

| 方法 | 使用场景 | 入参方式 |
|------|---------|---------|
| `GET` | 简单查询，参数少且非敏感 | `@RequestParam` |
| `POST` | 创建、更新、删除、列表查询（含分页/筛选）| `@RequestBody` |

### 11.3 统一响应结构

使用框架提供的 `BaseResp<T>`：

```java
// 成功
return BaseRespBuilder.success().setData(data).build();

// 失败（业务异常）
throw new BusinessException("具体错误信息");
// 或
return BaseRespBuilder.fail("具体错误信息").build();
```

响应体结构（由框架自动填充）：

```json
{
  "success": true,
  "code": "200",
  "msg": "success",
  "data": { ... }
}
```

### 11.4 分页

- **请求参数**：`pageNum`（页码，从 **1** 开始）+ `pageSize`（每页条数）
- **响应包装**：`DataPackage<T>`（由框架提供，含 `total` 和数据列表）

```java
// ReqDTO 示例
@Schema(description = "页码，从1开始")
private Integer pageNum;

@Schema(description = "每页条数")
private Integer pageSize;
```

### 11.5 DTO 命名

| 场景 | 后缀 | 示例 |
|------|------|------|
| 请求入参（Request Body）| `ReqDTO` | `OrderQueryReqDTO`、`AlgoStartReqDTO` |
| 响应出参 | `ResDTO` | `OrderDetailResDTO` |
| 通用传输 | `DTO` | `AlgoStartDTO` |

### 11.6 Swagger / OpenAPI

所有 Controller 和接口方法**必须**有 Swagger 注解：

```java
@Tag(name = "计划发布", description = "计划发布相关接口")
@RestController
public class PlanPublishController {

    @Operation(summary = "查询发布日志列表")
    @PostMapping("/{prefix}/planPublish/log/list")
    public BaseResp<DataPackage<PublishLogDO>> listLog(
            @RequestBody PublishLogQueryReqDTO req) { ... }
}
```

### 11.7 文件接口

```java
// 上传：MultipartFile 通过 @RequestPart 接收
@PostMapping("/{prefix}/file/upload")
public BaseResp<String> upload(
        @RequestPart("file") MultipartFile file,
        @RequestParam String time) { ... }

// 下载：直接操作 HttpServletResponse，返回 void
@GetMapping("/{prefix}/file/download")
public void download(@RequestParam String fileId,
                     HttpServletResponse response) { ... }
```

---

## 12. 代码审查 Checklist

提交 MR / PR 前**自查**，审查者**对照**检查：

- [ ] 命名清晰、见名知意，无拼写错误
- [ ] 无遗留 TODO / FIXME（或已加责任人和日期）
- [ ] 异常分支已覆盖，无吞异常
- [ ] 日志级别合理，无明文敏感信息
- [ ] 无硬编码配置项（URL、密钥、阈值）
- [ ] 单元测试已添加且本地通过
- [ ] 边界场景已考虑（null、空列表、并发、超时、最大值）
- [ ] 无明显性能问题（N+1、大事务、循环 IO、全表扫描）
- [ ] 安全风险已评估（注入、越权、敏感数据、依赖漏洞）
- [ ] 接口文档 / 注释已同步更新

---

## 13. 团队定制区

> 请团队在此补充项目特有规范，例如：
>
> - 框架使用约定（Spring Boot 注解风格、MyBatis Plus 使用规范等）
> - 业务领域术语对照表
> - 内部工具库 / 公共服务使用要求
> - 代码所有权（CODEOWNERS）与评审人规则
> - 其他项目特有约定

```
（待团队补充）
```
