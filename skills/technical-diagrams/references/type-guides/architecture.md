# 架构图使用指南

语义契约以 `resolve` 返回的 `type_spec_path` 为准（[架构图 1.0.0](../../types/architecture/1.0.0.md)）。分区、层与连线数量由用户资料决定；示例业务不得直接套入新图。

## 风格速览

| 编号 | 风格 | 视觉要点 | 资源 |
| --- | --- | --- | --- |
| AR-01 | 浅色分层架构 | 默认；浅色分层与模块依赖 | [SPEC](../../styles/architecture/soft-layered/1.0.0/SPEC.md) · [示例](../../styles/architecture/soft-layered/1.0.0/example.svg) |
| AR-02 | 精致卡片架构 | 卡片化模块、精致留白 | [SPEC](../../styles/architecture/premium-cards/1.0.0/SPEC.md) · [示例](../../styles/architecture/premium-cards/1.0.0/example.svg) |
| AR-03 | 浅色分层交互 | 交互信息密度最高；示例为通用构造内容 | [SPEC](../../styles/architecture/layered-interactions/1.0.0/SPEC.md) · [示例](../../styles/architecture/layered-interactions/1.0.0/example.svg) |
| AR-04 | 暖底深绿分区 | 深绿重点区、浅色辅助区、标签组合、判断与记录侧栏 | [分析](../../styles/architecture/contrast-process-bands/1.0.0/reference-analysis.md) · [特征图](../../styles/architecture/contrast-process-bands/1.0.0/feature-atlas.svg) · [原图](../../assets/reference-examples/ar-04-original.png) |
| AR-05 | 蓝绿密集分区 | 并列与嵌套分区、模块多时横排 | [示例](../../styles/architecture/blue-green-grid/1.0.0/example.svg) |
| AR-06 | 蓝绿密集细节 | 多级色块、点线边框、强调组件、多种线条层级 | [示例](../../styles/architecture/blue-green-detailed/1.0.0/example.svg) · [原图](../../assets/reference-examples/ar-06-original.png) |
| AR-07 | 蓝粉生态能力矩阵 | 浅蓝生态区、粉色主体、可选支撑区 | [分析](../../styles/architecture/ecosystem-capability-matrix/1.0.0/reference-analysis.md) · [原图](../../assets/reference-examples/ar-07-original.webp) |
| AR-08 | 跨域分层交互 | 跨域分层、椭圆节点、编号连线 | [分析](../../styles/architecture/cross-boundary-layers/1.0.0/reference-analysis.md) · [特征图](../../styles/architecture/cross-boundary-layers/1.0.0/feature-atlas.svg) · [原图](../../assets/reference-examples/ar-08-original.png) |
| AR-09 | 三栏分区与反馈闭环 | 外侧虚线区、中部大圆角核心、彩色配对、底部反馈 | [分析](../../styles/architecture/three-column-feedback/1.0.0/reference-analysis.md) · [原图](../../assets/reference-examples/ar-09-original.png) |
| AR-10 | 蓝紫虚线分区架构 | 侧栏、上横下双区、虚线边界、彩色描边卡 | [分析](../../styles/architecture/dashed-layered-cards/1.0.0/reference-analysis.md) · [原图](../../assets/reference-examples/ar-10-original.png) |
| AR-11 | 浅色横向分层矩阵 | 水平色带、两种层名位置、圆角容器、直角小格 | [分析](../../styles/architecture/stacked-layer-matrix/1.0.0/reference-analysis.md) · [原图](../../assets/reference-examples/ar-11-original.png) |
| AR-12 | 浅蓝图标分层面板 | 竖排层名、图文卡、嵌套矩阵、带字上行箭头 | [分析](../../styles/architecture/blue-layered-icon-panels/1.0.0/reference-analysis.md) · [原图](../../assets/reference-examples/ar-12-original.png) |
| AR-13 | 侧栏保障分层矩阵 | 顶部标题、三面保障带、留白间隔、服务矩阵、存储圆柱 | [分析](../../styles/architecture/framed-layered-matrix/1.0.0/reference-analysis.md) · [原图](../../assets/reference-examples/ar-13-original.png) |
| AR-14 | 手绘设计讨论架构 | 历史兼容；新图优先 FC-07 | [分析](../../styles/architecture/handdrawn-design-board/1.0.0/reference-analysis.md) · [特征图](../../styles/architecture/handdrawn-design-board/1.0.0/feature-atlas.svg) · [原图](../../assets/reference-examples/ar-14-original.png) |
| AR-15 | 双侧生态与能力矩阵 | 左右图标组、顶部双通道、中央重点卡、六组嵌套能力 | [分析](../../styles/architecture/dual-ecosystem-capability-band/1.0.0/reference-analysis.md) · [原图](../../assets/reference-examples/ar-15-original.png) |

## 选择要点

- 先按真实职责决定层、域、分区数量，再选风格；不能为凑满模板增加组件。
- AR-04、AR-07、AR-08、AR-09、AR-10、AR-11、AR-12、AR-13、AR-14、AR-15 有原图分析，仅作视觉参考，不覆盖固定版本规范，也不把原图业务套入新图。
- AR-04 特征图补充展示顶部来源卡、深绿节点、紫色标签带、不同执行器卡、反向流程、判断分支、消息组合、记录圆柱和多种回路；数量、内容与关系仅用于示例，不是新图的必备组件。独立通用特征图不复用原图业务与品牌；用户已授权的原图通过单独入口展示。旧版冻结 SPEC 中对预览包含原图的笼统限制应与此授权范围区分，不能借此将原图业务当作通用样例。
- AR-04 特征图使用圆角折线：共线处直连，必要转角采用真实曲线，短段收缩半径，跨线弧桥保留。圆角只属于该展示图的独立线条选择；新图仍按用户指定、已有元数据和固定默认值的优先级选择线条，不改变 AR-04 的固定默认值。
- AR-08 复刻原图时逐项保留分层、域边界、组和节点组合、颜色、图标、线型、箭头及编号；无法辨认的关系标注待确认，不推断未说明的线型含义或重复编号顺序。
- AR-09 的中心卡片与反馈关系只按来源连接；局部反馈曲线以实际需要为准，其他线条仍独立选择。
- AR-10 的分区归属及线色语义以来源为准，非连接的跨线必须消歧；示例线条不限制实际线条选择。
- AR-11、AR-12、AR-13 不凭层级位置或邻接关系补造组件调用。
- AR-14 / FC-07 的注释箭头与业务边分别建模；字体缺失时使用可读后备，不假定英文手写字体涵盖中文。
