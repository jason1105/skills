# 漏洞修复模式速查表

每种漏洞类型的标准处理方向，填充到 Excel 和 Widget 时直接参考。

---

## 注入类（高危/中危）

### 命令注入 (OS Command Injection) — CWE-78
- **代码层**：使用 Java NIO `Files.copy/delete` 替代 `Runtime.exec()`；若必须调用命令，改用数组形式 `exec(new String[]{"cmd", arg1, arg2})` + 白名单校验参数
- **框架层**：架构上禁止业务代码直接调用系统命令，封装文件操作工具类
- **扫描层**：Checkmarx/SonarQube 标记已修复路径

### SQL 注入：MyBatis ${}  — CWE-89
- **代码层**：`${item}` 全改为 `#{item}`；动态列名/表名改用服务端枚举白名单
- **框架层**：—
- **扫描层**：CI 正则规则阻断新增 `${}`；全项目 XML 文件批量扫描

### XML 外部实体注入 (XXE) — CWE-611
- **代码层**：DOM4J/SAX 设置 `disallow-doctype-decl=true` + 禁用外部实体特性；POI 升级至 ≥5.2.0
- **框架层**：封装统一安全 XML 解析工具类，禁止业务代码直接 new 解析器
- **扫描层**：—

### 跨站脚本攻击 (XSS) — CWE-79
- **代码层**：文件下载响应头设置 `Content-Disposition: attachment` + `X-Content-Type-Options: nosniff`；输出编码用 OWASP ESAPI
- **框架层**：Spring Security 配置全局 CSP；文件存储目录与 Web 根隔离
- **扫描层**：—

---

## 路径/文件类（中危）

### 路径穿越 (Path Traversal) — CWE-22
- **代码层**：`path.toRealPath()` 规范化后 `startsWith(allowedBase)` 校验；拒绝 `..`、绝对路径、空字节
- **框架层**：封装 `SecurePathUtils.resolve(base, input)`；ArchUnit 禁止直接 `new File(userInput)`
- **扫描层**：SonarQube `java:S2083`；CI 门禁阻断新增

### 上传任意文件 — CWE-434
- **代码层**：校验 Magic Bytes（真实 MIME）；白名单扩展名；UUID 重命名存储；限制最大文件大小
- **框架层**：`multipart.max-file-size` 全局限制；Nginx 禁止上传目录脚本执行；存储目录与 Web 根隔离
- **扫描层**：—

---

## 认证/密码类（中危）

### 硬编码密码 — CWE-259
- **代码层**：移除硬编码；改用 `System.getenv("KEY")` 或 `@Value("${key}")`
- **框架层**：jasypt/Nacos 加密配置；Vault/K8s Secret 管理；生产/开发环境密钥隔离；定期轮换
- **扫描层**：SonarQube `java:S2068`；git-secrets 防止提交

### 不安全的 SSL 证书 — CWE-295
- **代码层**：删除 TrustAll X509TrustManager；改用系统信任库或加载特定 CA
- **框架层**：统一 HTTP 客户端配置，禁止绕过证书校验
- **扫描层**：—

### Cookie 安全问题 — CWE-614
- **代码层**：响应头设置 `Set-Cookie: ...; HttpOnly; Secure; SameSite=Strict`；缩小 Path 范围
- **框架层**：Spring Security 全局 Cookie 配置
- **扫描层**：—

---

## 密码学类（中危）

### 不安全的随机函数 — CWE-338
- **代码层**：前端改用 `window.crypto.getRandomValues()`；后端 Java 使用 `SecureRandom`
- **框架层**：Token/Session 生成统一下沉到认证框架（Spring Security/JWT 库）
- **扫描层**：第三方库（drawio 等）中用于非安全目的的可标记"不是问题"

### 不安全的哈希算法 (MD5/SHA-1) — CWE-327
- **代码层**：密码存储改用 BCrypt/PBKDF2/Argon2；完整性校验改用 SHA-256/SHA-512
- **框架层**：禁止在新代码中引入 MD5/SHA-1 用于安全目的
- **扫描层**：第三方库（drawio 等）中用于版本/缓存 key 的可标记

---

## 错误处理类（中危/信息）

### 泛化的捕获异常 catch(Exception) — CWE-390
- **代码层**：替换为具体异常类型；至少 `log.error("msg", e)` 记录
- **框架层**：`@ControllerAdvice` 全局异常处理器减少业务层 try-catch 需求
- **扫描层**：SonarQube `java:S2221`；CI 门禁阻断新增

### 泛化的抛出异常 throws Exception — CWE-755
- **代码层**：定义业务异常体系（`BizException extends RuntimeException`）；接口声明具体异常
- **框架层**：同上
- **扫描层**：SonarQube `java:S112`

### 空的 catch 代码块 — CWE-390
- **代码层**：要么从异常中恢复，要么重新抛出，要么至少 `log.warn("ignored", e)`；禁止静默吞掉
- **框架层**：—
- **扫描层**：SonarQube `java:S108`

### finally 块中抛出异常 — CWE-460
- **代码层**：finally 块内用 try-catch 包裹清理操作，不允许异常逸出 finally
- **框架层**：—
- **扫描层**：—

---

## 信息泄露类（中危）

### 系统信息泄露（System.out/err/printStackTrace）— CWE-532
- **代码层**：统一改为 `log.error("msg", e)`；生产环境日志级别 WARN/ERROR
- **框架层**：强制使用 SLF4J + Logback/Log4j2；禁止 DEBUG 日志输出敏感字段
- **扫描层**：SonarQube `java:S106`；CI 正则 `grep -r "System.out\|printStackTrace"` 批量清除

### 残留 Debug 代码 — CWE-489
- **代码层**：删除调试代码；如需保留用 `if (log.isDebugEnabled())` 保护
- **框架层**：—
- **扫描层**：同上，全局 grep 一次性清除

---

## 架构/设计类（中危）

### 请求参数自动填充实体 (Mass Assignment) — CWE-915
- **代码层**：`@JsonIgnore` 保护敏感字段；`@JsonView` 限制序列化范围
- **框架层**：Controller 层强制使用独立 DTO；MapStruct 映射到 Entity；ArchUnit 规则禁止 Controller 直接引用 Entity
- **扫描层**：—

### 未检验的循环条件输入 — API4 DoS
- **代码层**：DTO 层 Bean Validation 注解；工具方法加日期/区间上限断言
- **框架层**：Spring `spring-boot-starter-validation` + 全局 `@ControllerAdvice` 参数校验
- **扫描层**：Checkmarx 已通过校验的路径标记 Not Exploitable

---

## 优先级判定规则

| 优先级 | 条件 | 建议时限 |
|--------|------|---------|
| P0 立即修复 | 高危漏洞（RCE/注入/XSS/XXE）| 1 周内 |
| P1 优先修复 | 中危且直接影响数据安全（路径穿越/文件上传/SQL注入/硬编码密码）| 2 周内 |
| P2 分批处理 | 中危代码质量/规范问题（异常处理/信息泄露/随机函数）| 按 Sprint |
| 可标记误报 | 第三方库中非安全目的的使用（drawio 随机数/哈希）| 扫描工具标注 |
