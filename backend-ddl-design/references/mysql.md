# MySQL DDL 规范

## 常用数据类型

| 类型 | 说明 | 使用场景 |
|------|------|---------|
| BIGINT | 64 位整数 | 主键 ID（雪花 ID） |
| INT | 32 位整数 | 普通整数 |
| TINYINT | 8 位整数 | 布尔标记、状态码 |
| VARCHAR(N) | 变长字符串 | 普通文本字段 |
| TEXT / LONGTEXT | 大文本 | 超过 65535 字符内容 |
| DATETIME | 时间戳 | 业务时间 |
| TIMESTAMP | 时间戳 | 自动更新的时间字段 |
| DECIMAL(M,N) | 精确数值 | 金额、精确计算 |
| JSON | 原生 JSON | 结构化非关系数据 |

## 字符集和排序规则

- 字符集推荐：`utf8mb4`（支持 emoji 和完整 Unicode）
- 排序规则推荐：`utf8mb4_unicode_ci`（不区分大小写）或 `utf8mb4_bin`（区分大小写）

## 通用字段模板

```sql
`id`            BIGINT        NOT NULL COMMENT '主键ID',
`create_by`     VARCHAR(64)   DEFAULT NULL COMMENT '创建人',
`create_time`   DATETIME      DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
`update_by`     VARCHAR(64)   DEFAULT NULL COMMENT '更新人',
`update_time`   DATETIME      DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
`del_flag`      TINYINT       DEFAULT 0 COMMENT '删除标记 0-正常 1-删除',
`remark`        VARCHAR(500)  DEFAULT NULL COMMENT '备注',
```

## 建表模板

```sql
-- ============================================
-- 表名：t_模块_实体
-- 说明：[表的用途说明]
-- ============================================
CREATE TABLE `t_模块_实体` (
    `id`            BIGINT        NOT NULL COMMENT '主键ID',
    -- 业务字段（注释使用中文，枚举字段列出所有可选值）
    `字段名`        类型          约束     COMMENT '字段的中文说明',
    `status`        TINYINT       DEFAULT 0 COMMENT '状态 0-草稿 1-发布 2-下架',
    -- 公共字段
    `create_by`     VARCHAR(64)   DEFAULT NULL COMMENT '创建人',
    `create_time`   DATETIME      DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_by`     VARCHAR(64)   DEFAULT NULL COMMENT '更新人',
    `update_time`   DATETIME      DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `del_flag`      TINYINT       DEFAULT 0 COMMENT '删除标记 0-正常 1-删除',
    `remark`        VARCHAR(500)  DEFAULT NULL COMMENT '备注',
    PRIMARY KEY (`id`),
    -- 索引（标注查询场景）
    -- 场景：按创建时间倒序查询列表
    INDEX `idx_t_模块_实体_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='表的中文说明';
```

## MySQL 特殊注意事项

- 默认使用 InnoDB 引擎（支持事务、外键）
- VARCHAR 长度限制：行总长度 65535 字节，单字段实际受字符集影响（utf8mb4 下 VARCHAR 最大约 16383）
- DATETIME 与 TIMESTAMP 的区别：TIMESTAMP 受时区影响且范围受限（1970-2038），DATETIME 无时区转换且范围大
- `AUTO_INCREMENT` 可用，但分布式场景推荐雪花 ID
- 使用反引号 `` ` `` 包裹标识符避免与关键字冲突
- 索引前缀长度：VARCHAR 字段建索引时注意长度，超长字段用前缀索引 `INDEX idx_name (col(20))`
