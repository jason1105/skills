# 编码安全规范

本文档整理自代码安全扫描（Checkmarx / CEPRI）的实际检出结果，涵盖 16 类常见代码安全漏洞。
实现阶段编码时**逐条对照**，确保不引入已知漏洞。

---

## 高危漏洞（必须在编码阶段彻底消除）

### 1. 命令注入（OS Command Injection）

**危害**：用户可控参数未经验证直接拼接进系统命令，攻击者可执行任意 OS 命令。

**错误示例**：

```java
// ❌ netId 来自用户请求，未做任何过滤
Runtime.getRuntime().exec("rm -f " + filePath).waitFor();
```

**修复对策**：

- 使用语言原生文件操作 API（如 Java NIO `Files.copy`、`Files.delete`）替代 shell 命令
- 若必须调用 OS 命令，改用数组形式 `exec(new String[]{"cp", src, dst})`，避免 shell 解释
- 白名单严格限制参数格式（如只允许数字/字母/下划线）

### 2. XML 外部实体注入（XXE）

**危害**：解析用户上传的 XML/Excel 文件时未禁用 DTD 和外部实体，可读取服务器敏感文件或发起 SSRF。

**错误示例**：

```java
// ❌ SAXReader 未做任何安全配置
SAXReader saxReader = new SAXReader();
return saxReader.read(new File(filename));
```

**修复对策**：

- 创建解析器时禁用 DTD 和外部实体特性
- 封装统一的安全 XML 解析工具类，禁止业务代码直接 new 解析器
- Apache POI 确认版本 ≥ 5.2.0

### 3. 跨站脚本攻击（存储型 XSS）

**危害**：文件/数据库内容未经编码直接写入 HTTP 响应，攻击者可注入 JS 脚本。

**修复对策**：

- 文件下载设置 `Content-Type: application/octet-stream` + `Content-Disposition: attachment`
- 响应头加 `X-Content-Type-Options: nosniff`
- 上传文件时校验并白名单化文件扩展名
- 输出到页面的数据使用编码处理

---

## 中危漏洞（编码阶段必须规避）

### 4. 未校验的循环条件输入

**危害**：用户输入直接控制循环次数，可构造大量循环导致 DoS。

**错误示例**：

```java
// ❌ 用户输入的列表未经验证直接用于循环
@PostMapping("/queryEconomicAnalysis")
public BaseResp query(@RequestBody EconomicAnalysisReqDTO request) {
    // request 中的列表大小未限制
}
```

**修复对策**：

- 对所有用户输入的集合/范围参数做大小校验（如最大 1000 条）
- 设置循环最大迭代次数兜底

### 5. 路径穿越（Input Path Not Canonicalized）

**危害**：用户可控参数拼入文件路径，通过 `../../` 访问任意文件。

**错误示例**：

```java
// ❌ 请求参数直接用于文件读取
String path = basePath + request.getFilePath();
```

**修复对策**：

- 对所有文件路径使用 `Paths.get(base).resolve(input).normalize()`，然后断言 `startsWith(base)`
- 拒绝含 `..`、绝对路径、空字节的输入
- 封装 `SecurePathUtils.resolve(base, input)` 工具方法，全项目强制使用

### 6. 硬编码密码

**危害**：源码中存在硬编码密码、配置文件明文密码、SSL TrustAll。

**修复对策**：

- 所有密码改为从环境变量或配置中心读取
- 使用 jasypt 或配置中心加密配置，生产环境密钥与开发环境隔离
- 删除 TrustAll 逻辑，改用系统信任库或加载特定 CA 证书
- 注释中残留的明文密码也必须删除（扫描工具会检出）

### 7. SQL 注入（MyBatis `${}` 拼接）

**危害**：MyBatis Mapper 中使用 `${item}` 直接拼接 SQL。

**错误示例**：

```xml
<!-- ❌ ${item} 直接插入 SQL -->
<foreach collection="list" item="item">
    ${item}
</foreach>
```

**修复对策**：

- 所有 `${item}` 改为 `#{item}`
- 动态列名/表名改用服务端枚举白名单映射，不使用用户输入
- CI 中加入正则规则禁止新增 `${}` 动态拼接

### 8. 上传任意文件

**危害**：文件上传接口未校验文件类型、大小、内容。

**修复对策**：

- 校验文件 Magic Bytes（真实 MIME），不信任 Content-Type header
- 白名单扩展名
- 限制最大文件大小
- 存储时重命名为随机 UUID，不使用原始文件名
- 存储目录与 Web 根目录隔离

### 9. 请求参数自动填充实体（Mass Assignment）

**危害**：Controller 直接用 JPA Entity 接收请求参数，攻击者可注入非预期字段。

**错误示例**：

```java
// ❌ 直接用持久实体接收请求
@PostMapping("/update")
public Result update(@RequestBody Order order) {
    orderRepository.save(order); // 用户可注入 role、isAdmin 等字段
}
```

**修复对策**：

- Controller 层必须使用独立 DTO 接收请求参数
- 通过 MapStruct 等工具映射到 Entity
- Entity 敏感字段加 `@JsonIgnore`

### 10. 不安全的随机函数

**危害**：使用 `Math.random()` 或 `java.util.Random` 生成 Token/会话标识，可被预测。

**修复对策**：

- 前端使用 `window.crypto.getRandomValues()`
- 后端使用 `SecureRandom` 替代 `Random`
- Token/Session 生成下沉到认证框架统一处理

### 11. 不安全的哈希算法（MD5/SHA-1）

**修复对策**：

- 密码存储使用 BCrypt / PBKDF2 / Argon2
- 数据完整性校验使用 SHA-256 / SHA-512
- 禁止在新代码中引入 MD5/SHA-1 用于安全目的

### 12. Null 引用风险

**修复对策**：

- 使用 `Optional.ofNullable()` 或 `Objects.requireNonNull()`
- 对外部调用返回值、`Map.get()`、集合查询结果统一做判空
- 配置 `@NotNull` / `@Nullable` 注解检查

### 13. 资源未释放（Resource Leak）

**修复对策**：

- 所有 `Closeable` 资源使用 try-with-resources 语法
- 若需兼容老写法，在 finally 块中判空后调用 `close()`

---

## 低危但高频漏洞（编码习惯问题，批量消除）

### 14. 捕获/声明宽泛异常

**修复对策**：

- `catch (Exception e)` 替换为具体异常类型
- 定义业务异常体系（如 `BizException extends RuntimeException`）
- 接口声明具体受检异常，不使用 `throws Exception`
- 异常必须被记录或重新抛出，不能静默吞掉

### 15. 系统信息泄露 + 残留 Debug 代码

**修复对策**：

- 统一使用日志框架（SLF4J + Logback/Log4j2），禁止 `System.out` / `System.err`
- 生产环境日志级别设为 WARN/ERROR
- `e.printStackTrace()` 统一改为 `log.error("msg", e)`
- 禁止 DEBUG 日志输出敏感字段（密码、token、完整路径）

### 16. 空的 catch 代码块 / finally 中抛异常

**修复对策**：

- 空 catch 块至少添加 `log.warn("ignored", e)` 或注释说明原因
- finally 块内操作用 try-catch 包裹，不允许异常逸出 finally

---

## 编码自检清单

编码完成后，对照以下清单逐条确认：

- [ ] 无 `Runtime.exec()` 直接拼接用户输入
- [ ] XML 解析器已禁用 DTD 和外部实体
- [ ] 文件下载已设置 `Content-Disposition: attachment`
- [ ] 所有循环条件来自用户输入的，已限制最大次数
- [ ] 所有文件路径已做规范化校验
- [ ] 无硬编码密码，配置文件密码已加密
- [ ] MyBatis 无 `${}` 拼接（白名单场景除外）
- [ ] 文件上传已校验 Magic Bytes + 白名单扩展名
- [ ] Controller 使用 DTO 接收参数，不直接用 Entity
- [ ] Token/Session 使用安全随机数生成
- [ ] 无 MD5/SHA-1 用于安全目的
- [ ] 外部调用返回值已做判空处理
- [ ] 所有资源使用 try-with-resources
- [ ] 异常捕获为具体类型，无空 catch 块
- [ ] 无 `System.out` / `printStackTrace`
- [ ] 无残留 Debug 代码
