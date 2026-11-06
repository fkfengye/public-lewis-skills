# 拓扑图使用指南

语义契约以 `resolve` 返回的 `type_spec_path` 为准（[拓扑图 1.0.0](../../types/topology/1.0.0.md)）。按来源表达有向或无向关系，节点与连接由实际资料决定。

## 风格速览

| 编号 | 风格 | 视觉要点 | 资源 |
| --- | --- | --- | --- |
| TP-01 | 橙红图标链路 | 橙红图标、灰色箭头、浅色斜纹、上下标注 | [分析](../../styles/topology/icon-chain/1.0.0/reference-analysis.md) · [特征图](../../styles/topology/icon-chain/1.0.0/feature-atlas.svg) · [原图](../../assets/reference-examples/tp-01-original.png) |
| TP-02 | 分层图标集群拓扑 | 入口与网关图标、三列多副本、重复连接、协调回向 | [分析](../../styles/topology/layered-service-clusters/1.0.0/reference-analysis.md) · [特征图](../../styles/topology/layered-service-clusters/1.0.0/feature-atlas.svg) · [原图](../../assets/reference-examples/tp-02-original.png) |

## 使用要点

- 不把原始样例的业务或顺序套入新图；节点数和拓扑结构以实际资料为准。
- 来源中的透明背景应在白底检查，避免误判颜色与描边。
- 有向与无向关系逐条按来源绘制；不确定方向的连接保留为无向，不补箭头。
