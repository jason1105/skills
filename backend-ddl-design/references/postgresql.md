# PostgreSQL DDL 规范

## 常用数据类型

| 类型 | 说明 | 使用场景 |
|------|------|---------|
| BIGINT / BIGSERIAL | 64 位整数 / 自增 | 主键 ID |
| INTEGER / SERIAL | 32 位整数 / 自增 | 普通整数 |
| SMALLINT | 16 位整数 | 状态码、标记 |
| VARCHAR(N) / TEXT | 字符串 | 文本字段（TEXT 无长度限制） |
| TIMESTAMP / TIMESTAMPTZ | 时间戳 | 业务时间（TIMESTAMPTZ 带时区） |
| NUMERIC(M,N) / DECIMAL | 精确数值 | 金额、精确计算 |
| BOOLEAN | 布尔值 | 是/否类字段（推荐） |
| JSONB | 二进制 JSON | 结构化非关系数据（推荐 JSONB 而非 JSON） |
| UUID | UUID 类型 | 分布式主键可选项 |

## 通用字段模板

```sql
id              BIGINT        NOT NULL,
create_by       VARCHAR(64)   DEFAULT NULL,
create_time     TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
update_by       VARCHAR(64)   DEFAULT NULL,
update_time     TIMESTAMP     DEFAULT NULL,
del_flag        SMALLINT      DEFAULT 0,
remark          VARCHAR(500)  DEFAULT NULL
```

## 建表模板

```sql
-- ============================================
-- 表名：t_模块_实体
-- 说明：[表的用途说明]
-- ============================================
CREATE TABLE t_模块_实体 (
    id              BIGINT        NOT NULL,
    -- 业务字段
    字段名          类型          约束,
    status          SMALLINT      DEFAULT 0,
    -- 公共字段
    create_by       VARCHAR(64)   DEFAULT NULL,
    create_time     TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    update_by       VARCHAR(64)   DEFAULT NULL,
    update_time     TIMESTAMP     DEFAULT NULL,
    del_flag        SMALLINT      DEFAULT 0,
    remark          VARCHAR(500)  DEFAULT NULL,
    PRIMARY KEY (id)
);

-- 表注释（必须为中文）
COMMENT ON TABLE t_模块_实体 IS '表的中文说明';

-- 字段注释（必须为中文，枚举字段须列出所有可选值）
COMMENT ON COLUMN t_模块_实体.id IS '主键ID';
COMMENT ON COLUMN t_模块_实体.字段名 IS '字段的中文说明';
COMMENT ON COLUMN t_模块_实体.status IS '状态 0-草稿 1-发布 2-下架';
COMMENT ON COLUMN t_模块_实体.del_flag IS '删除标记 0-正常 1-删除';
COMMENT ON COLUMN t_模块_实体.create_by IS '创建人';
COMMENT ON COLUMN t_模块_实体.create_time IS '创建时间';
COMMENT ON COLUMN t_模块_实体.update_by IS '更新人';
COMMENT ON COLUMN t_模块_实体.update_time IS '更新时间';
COMMENT ON COLUMN t_模块_实体.remark IS '备注';

-- 索引（标注查询场景）
-- 场景：按创建时间倒序查询列表
CREATE INDEX idx_t_模块_实体_create_time ON t_模块_实体 (create_time);

-- 自动更新 update_time 的触发器
CREATE OR REPLACE FUNCTION set_update_time()
RETURNS TRIGGER AS $$
BEGIN
    NEW.update_time = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_t_模块_实体_update_time
BEFORE UPDATE ON t_模块_实体
FOR EACH ROW EXECUTE FUNCTION set_update_time();
```

## PostgreSQL 特殊注意事项

- 标识符默认转小写存储（除非加双引号），建议统一不使用双引号，全小写命名
- 使用 `COMMENT ON TABLE` 和 `COMMENT ON COLUMN` 语法添加注释（不支持内联 COMMENT）
- 没有 `AUTO_INCREMENT`，使用 `SERIAL` / `BIGSERIAL` 或序列（SEQUENCE），分布式场景推荐应用层生成
- PostgreSQL 没有原生的 `ON UPDATE CURRENT_TIMESTAMP`，需通过触发器实现
- JSONB 优先于 JSON（支持索引、更快查询）
- 分页使用 `LIMIT N OFFSET M`
- 索引类型丰富：B-tree（默认）、Hash、GIN、GiST、BRIN，按场景选择
