# 状态图使用指南

语义契约以 `resolve` 返回的 `type_spec_path` 为准（[状态图 1.0.0](../../types/state/1.0.0.md)）。状态迁移不凭空增加返回迁移；状态、迁移事件与条件按来源建模。

## 风格速览

| 编号 | 风格 | 适合 | 资源 |
| --- | --- | --- | --- |
| ST-01 | 经典黑白状态 | 默认；正式文档 | [SPEC](../../styles/state/classic-mono/1.0.0/SPEC.md) · [示例](../../styles/state/classic-mono/1.0.0/example.svg) |
| ST-02 | 浅色卡片状态 | 浅色说明文档、卡片式阅读 | [SPEC](../../styles/state/soft-cards/1.0.0/SPEC.md) · [示例](../../styles/state/soft-cards/1.0.0/example.svg) |

## 使用要点

- 迁移箭头只沿来源中的真实事件方向绘制，不因视觉对称补反向迁移。
- 迁移编号表达事件与条件，不排成消息执行顺序。
