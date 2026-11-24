# 达梦8（DM8）DDL 规范

## 数据类型映射（MySQL → 达梦8）

| MySQL 类型 | 达梦8 类型 | 说明 |
|-----------|-----------|------|
| BIGINT | BIGINT | 主键 ID 推荐使用 |
| INT | INT | 普通整数 |
| VARCHAR(N) | VARCHAR(N) | 变长字符串 |
| TEXT | TEXT / CLOB | 大文本，达梦推荐 CLOB |
| DATETIME | TIMESTAMP | 时间戳 |
| DECIMAL(M,N) | DECIMAL(M,N) | 精确数值 |
| TINYINT | TINYINT / SMALLINT | 达梦8 支持 TINYINT |
| JSON | CLOB | 达梦8 无原生 JSON 类型，用 CLOB 存储 |

## 通用字段模板

```sql
"id"            BIGINT        NOT NULL,
"create_by"     VARCHAR(64)   DEFAULT NULL,
"create_time"   TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
"update_by"     VARCHAR(64)   DEFAULT NULL,
"update_time"   TIMESTAMP     DEFAULT NULL,
"del_flag"      TINYINT       DEFAULT 0,
"remark"        VARCHAR(500)  DEFAULT NULL,
```

## 建表模板

```sql
-- ============================================
-- 表名：t_模块_实体
-- 说明：[表的用途说明]
-- ============================================
CREATE TABLE "模式名"."t_模块_实体" (
    "id"            BIGINT        NOT NULL,
    -- 业务字段
    "字段名"        类型          约束,
    -- 公共字段
    "create_by"     VARCHAR(64)   DEFAULT NULL,
    "create_time"   TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    "update_by"     VARCHAR(64)   DEFAULT NULL,
    "update_time"   TIMESTAMP     DEFAULT NULL,
    "del_flag"      TINYINT       DEFAULT 0,
    "remark"        VARCHAR(500)  DEFAULT NULL,
    PRIMARY KEY ("id")
);

-- 表注释（必须为中文）
COMMENT ON TABLE "模式名"."t_模块_实体" IS '表的中文说明';

-- 字段注释（必须为中文，枚举字段须列出所有可选值）
COMMENT ON COLUMN "模式名"."t_模块_实体"."id" IS '主键ID';
COMMENT ON COLUMN "模式名"."t_模块_实体"."字段名" IS '字段的中文说明';
COMMENT ON COLUMN "模式名"."t_模块_实体"."del_flag" IS '删除标记 0-正常 1-删除';
COMMENT ON COLUMN "模式名"."t_模块_实体"."create_by" IS '创建人';
COMMENT ON COLUMN "模式名"."t_模块_实体"."create_time" IS '创建时间';
COMMENT ON COLUMN "模式名"."t_模块_实体"."update_by" IS '更新人';
COMMENT ON COLUMN "模式名"."t_模块_实体"."update_time" IS '更新时间';
COMMENT ON COLUMN "模式名"."t_模块_实体"."remark" IS '备注';

-- 索引（标注查询场景）
-- 场景：按创建时间倒序查询列表
CREATE INDEX "idx_t_模块_实体_create_time" ON "模式名"."t_模块_实体" ("create_time");
```

## 达梦8 特殊注意事项

- 达梦8 的标识符默认大小写敏感，建议统一使用双引号包裹
- 不支持 MySQL 的 `AUTO_INCREMENT`，主键生成策略需在应用层处理（雪花 ID 等）
- 使用 `COMMENT ON TABLE` 和 `COMMENT ON COLUMN` 语法添加注释（不使用内联 COMMENT）
- 分页语法使用 `LIMIT` 或 `TOP`，与 MySQL 兼容但注意函数差异
- 外键约束视具体场景决定是否使用，通常在应用层维护关联关系
