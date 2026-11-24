# 编码规范检查清单

> 本清单基于SonarQube扫描结果和项目编码规范整理，用于编码前、中、后自检。

## 使用说明

- **编码前**：阅读本清单，了解规范要求
- **编码中**：实时对照，避免产生问题代码
- **编码后**：逐项检查，确保符合规范
- **提交前**：最后一道防线，确保SonarQube扫描通过

---

## 1. Javadoc注释检查

### 1.1 接口方法注释

| 检查项 | 检查方法 | 示例 |
|-------|---------|------|
| 所有public接口方法有Javadoc | 搜索`public interface`，检查每个方法 | `/** ... */` |
| 包含`@param`标签 | 检查参数列表 | `@param req 请求参数` |
| 包含`@return`标签 | 检查返回类型 | `@return 发布结果` |
| 包含`@throws`标签 | 检查异常声明 | `@throws IllegalArgumentException` |
| 注释内容清晰 | 读注释能理解用途 | "手动发布计划" ✓ "执行方法" ✗ |

**快速检查命令**：

```bash
# 查找所有接口文件
find src/ -name "*Service.java" -o -name "*Controller.java" | while read f; do
  echo "检查文件: $f"
  grep -c "/**" "$f" || echo "缺少Javadoc注释"
done
```

### 1.2 实现类方法注释

| 检查项 | 检查方法 | 示例 |
|-------|---------|------|
| public方法有Javadoc | 搜索`public`，检查是否有`/**` | Service实现类 |
| `@param`说明参数含义 | 检查每个参数 | `@param planType 计划类型` |
| `@return`说明返回值 | 检查返回类型 | `@return 配置信息` |

### 1.3 枚举注释

| 检查项 | 检查方法 | 示例 |
|-------|---------|------|
| 枚举类有Javadoc | 检查是否有`/**` | `/** 触发来源枚举 */` |
| 每个枚举值有注释 | 检查每个值上方 | `/** 手动触发 */` |
| 注释说明业务含义 | 检查注释内容 | "手动触发" ✓ "手动" ✗ |

**快速检查命令**：

```bash
# 检查枚举文件
find src/ -name "*Enum.java" | while read f; do
  echo "检查枚举: $f"
  grep -E "^\\s+[A-Z_]+," "$f" | while read line; do
    prev_line=$(grep -B 1 "$line" "$f" | head -1)
    if [[ ! "$prev_line" =~ "/\\*\\*" ]]; then
      echo "缺少注释: $line"
    fi
  done
done
```

---

## 2. DTO字段检查

### 2.1 默认值检查

| 检查项 | 检查方法 | 规则 |
|-------|---------|------|
| DTO字段无默认值 | 搜索`= 0`, `= ""`, `= false` | 不允许 |
| 分页参数无默认值 | 检查`pageNum`, `pageSize` | 不能写`= 1`, `= 10` |
| 使用包装类型 | 检查字段类型 | `Integer`而非`int` |

> 详细修复示例请参见 [sonarqube-fix-guide.md](sonarqube-fix-guide.md) 对应章节。

**快速检查命令**：

```bash
# 检查DTO默认值
find src/ -path "*/dto/*" -name "*.java" -exec grep -H "= " {} \; | grep -E "pageNum|pageSize"
```

---

## 3. 魔法值检查

### 3.1 常量提取

| 检查项 | 检查方法 | 规则 |
|-------|---------|------|
| 无硬编码数值 | 搜索条件判断和赋值语句中的硬编码数值常量 | 超过1次的数字应提取 |
| 使用常量类 | 检查是否有`Constants`类 | 集中管理常量 |
| 常量命名规范 | 全大写+下划线 | `MAX_RETRY_COUNT` |

**需要提取为常量的数值**：

- 超时时间：`2`, `60`, `300`
- 重试次数：`3`, `5`
- 限制数量：`10`, `100`, `1000`
- 比例：`0.5`, `0.9`

**不需要提取的数值**：

- 无明确业务含义的临时变量（需结合上下文判断，SonarQube 仍可能报告，请按实际情况处理）
- 简单运算：`result * 2`, `index + 1`
- 数组索引：`array[0]`

> 详细修复示例请参见 [sonarqube-fix-guide.md](sonarqube-fix-guide.md) 对应章节。

**快速检查命令**：

```bash
# 查找重复出现的数字
grep -rE "\\b[0-9]+\\b" src/ --include="*.java" | \
  grep -oE "\\b[0-9]+\\b" | sort | uniq -c | sort -rn | head -20
```

---

## 4. 线程创建检查

### 4.1 线程池使用

| 检查项 | 检查方法 | 规则 |
|-------|---------|------|
| 不使用`new Thread` | 搜索`new Thread` | 禁止 |
| 使用`@Async` | 检查异步方法 | Spring项目 |
| 使用线程池 | 检查`ExecutorService` | 标准方式 |
| 使用`TaskExecutor` | 检查Spring线程池 | Spring项目 |

> 详细修复示例请参见 [sonarqube-fix-guide.md](sonarqube-fix-guide.md) 对应章节。

**快速检查命令**：

```bash
# 检查是否有new Thread
grep -r "new Thread" src/ --include="*.java"
```

---

## 5. 代码风格检查

### 5.1 命名规范

| 检查项 | 规则 | 示例 |
|-------|------|------|
| 类名 | 大驼峰 | `UserService` |
| 方法名 | 小驼峰 | `getUserById` |
| 常量名 | 全大写+下划线 | `MAX_COUNT` |
| 包名 | 全小写 | `com.example.service` |

### 5.2 注释规范

| 检查项 | 规则 | 示例 |
|-------|------|------|
| 行注释 | `//` | `// TODO: 待实现` |
| 块注释 | `/* */` | `/* 业务逻辑说明 */` |
| Javadoc | `/** */` | `/** 方法说明 */` |

### 5.3 格式规范

| 检查项 | 规则 | 工具 |
|-------|------|------|
| 缩进 | 4空格 | IDE格式化 |
| 行宽 | 不超过120字符 | IDE检查 |
| 导入顺序 | java -> javax -> 第三方 -> 本项目 | IDE格式化 |

---

## 6. 安全检查

### 6.1 SQL注入

| 检查项 | 检查方法 | 规则 |
|-------|---------|------|
| 使用预编译语句 | 检查`PreparedStatement` | 禁止字符串拼接SQL |
| 参数化查询 | 检查`?`或`:param` | 不用`${param}` |

### 6.2 敏感信息

| 检查项 | 检查方法 | 规则 |
|-------|---------|------|
| 不记录密码 | 检查日志输出 | 脱敏处理 |
| 不输出敏感信息 | 检查异常信息 | 避免泄露 |

---

## 7. 提交前检查清单

### 7.1 代码检查

- [ ] 所有public方法有Javadoc注释
- [ ] 所有枚举值有注释说明
- [ ] DTO字段无默认值
- [ ] 无魔法值（使用常量）
- [ ] 未使用`new Thread`（使用线程池）
- [ ] 通过IDE代码格式化
- [ ] 无编译警告

### 7.2 测试检查

- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 所有测试用例通过
- [ ] 无被忽略的测试

### 7.3 SonarQube检查

- [ ] 无 CRITICAL 级别问题，MAJOR 级别问题已全部修复或有记录在案的跟踪计划
- [ ] 代码覆盖率达标

---

## 8. 常见错误示例

### 8.1 Javadoc错误

```java
// ❌ 错误：缺少@param
public User getUser(String id) {
    // ...
}

// ❌ 错误：缺少@return
public User getUser(String id) {
    // ...
}

// ✅ 正确
/**
 * 根据ID获取用户
 *
 * @param id 用户ID
 * @return 用户对象
 */
public User getUser(String id) {
    // ...
}
```

### 8.2 魔法值错误

```java
// ❌ 错误：魔法值
if (count > 10) {
    // ...
}

// ✅ 正确：使用常量
if (count > Constants.MAX_COUNT) {
    // ...
}
```

### 8.3 线程创建错误

```java
// ❌ 错误：显式创建线程
new Thread(() -> doSomething()).start();

// ✅ 正确：使用线程池
taskExecutor.execute(() -> doSomething());
```

---

## 9. 工具推荐

### 9.1 IDE插件

- **SonarLint**：实时SonarQube检查
- **CheckStyle**：代码风格检查
- **FindBugs**：Bug检测
- **Alibaba Java Coding Guidelines**：阿里的编码规范

### 9.2 命令行工具

```bash
# Maven编译
mvn clean compile

# 运行测试
mvn test

# SonarQube扫描
mvn sonar:sonar

# 代码格式化
mvn spotless:apply
```

---

## 10. 参考资料

- [SonarQube规则](https://rules.sonarsource.com/java/)
- [阿里巴巴Java开发手册](https://github.com/alibaba/p3c)
- [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html)
- 项目编码规范：`backend-implementation/references/coding-standards.md`
- SonarQube修复指南：`sonarqube-fix-guide.md`
