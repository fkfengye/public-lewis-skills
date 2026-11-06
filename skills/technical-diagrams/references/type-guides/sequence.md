# 时序图使用指南

语义契约以 `resolve` 返回的 `type_spec_path` 为准（[时序图 1.0.0](../../types/sequence/1.0.0.md)）。普通消息保持水平与时间顺序，线条选项只影响自调用或必要绕行。

## 风格速览

| 编号 | 风格 | 适合 | 资源 |
| --- | --- | --- | --- |
| SQ-01 | 蓝框机构时序 | 默认；多方请求/响应 | [SPEC](../../styles/sequence/institutional-blue/1.0.0/SPEC.md) · [示例](../../styles/sequence/institutional-blue/1.0.0/example.svg) |
| SQ-02 | 经典黑白时序 | 打印、正式文档 | [SPEC](../../styles/sequence/classic-mono/1.0.0/SPEC.md) · [示例](../../styles/sequence/classic-mono/1.0.0/example.svg) |
| SQ-03 | 蓝绿分阶段时序 | 需要阶段标题带 | [SPEC](../../styles/sequence/blue-green-phases/1.0.0/SPEC.md) · [示例](../../styles/sequence/blue-green-phases/1.0.0/example.svg) |
| SQ-04 | 浅色折角注释时序 | 需要折角注释、自调用细节 | [分析](../../styles/sequence/pale-folded-notes/1.0.0/reference-analysis.md) · [示例](../../styles/sequence/pale-folded-notes/1.0.0/example.svg) |
| SQ-05 | 手绘粉彩分支时序 | 人形参与者、粉彩激活条和互斥分支 | [规范](../../styles/sequence/handdrawn-pastel-branches/1.0.0/SPEC.md) · [分析](../../styles/sequence/handdrawn-pastel-branches/1.0.0/reference-analysis.md) · [示例](../../styles/sequence/handdrawn-pastel-branches/1.0.0/example.svg) |

## 使用要点

- 参与者可用蓝绿卡片区分，阶段使用独立标题带；请求、响应方向和阶段内容均依实际模型绘制。
- 保持生命线、点线返回、独立实线回调和圆角自调用的区别；SQ-04 的折角注释不得被当作业务节点。
- 阶段条、alt/opt 标题和自循环占独立空间，不能挤占消息行。
- SQ-05 显式使用时序语义 1.1.0：消息标签可以放在水平线的真实间隙内；手写标题、黄色参与者、粉色激活条和浅青 `alt` 片段按模型组合。
