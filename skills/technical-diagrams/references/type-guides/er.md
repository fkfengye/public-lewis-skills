# ER 图使用指南

语义契约以 `resolve` 返回的 `type_spec_path` 为准（[ER 图 1.0.0](../../types/er/1.0.0.md)）。保留字段端口、引用方向与基数标记；DDL、字段集合、键、引用方向、条件和基数保持原义。

## 风格速览

| 编号 | 风格 | 适合 | 资源 |
| --- | --- | --- | --- |
| ER-01 | 浅色表结构 | 默认；逻辑模型与物理表 | [SPEC](../../styles/er/soft-tables/1.0.0/SPEC.md) · [示例](../../styles/er/soft-tables/1.0.0/example.svg) |
| ER-02 | 经典黑白 ER | 打印、正式文档 | [SPEC](../../styles/er/classic-mono/1.0.0/SPEC.md) · [示例](../../styles/er/classic-mono/1.0.0/example.svg) |
| ER-03 | 多域 DDL 表结构 | 十几个实体的复杂模型；三域分区 + 键 / 字段 / 类型·可空三列 | [分析](../../styles/er/domain-ddl/1.0.0/reference-analysis.md) · [SPEC](../../styles/er/domain-ddl/1.0.0/SPEC.md) · [示例](../../styles/er/domain-ddl/1.0.0/example.svg) |

## 使用要点

- 只根据来源区分逻辑引用与物理 FK，不从线条或示例猜约束与基数。
- 可调整图中字段展示顺序来对齐引用端点，并同步更新复绘模型；不能把端点挪到无关字段。
- 双端鸟爪属于基数，不是双向消息箭头；状态图与 ER 图都不要套用交互编号规则。
- ER-03 是高密度 DDL 详细视图，字号与行高独立冻结，不与 ER-01 混用；域框只表示阅读分组，徽标只用于线旁标签指代实体。通用示例不复用参考图业务数据。绘制时按引用链重排域内行序、把同一字段的多条引用分到表卡左右两侧端口，并在近水平直连上动态避让标签，细则见 SPEC「布局与端口分离」。
