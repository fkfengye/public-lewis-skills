# 固定风格编号 v1

预览页按图种分组，编号由 `registry/types/<图种>.json` 中每个风格条目的 `number` 显式注册，由 `catalog.py` 汇总为 `style_numbers`，绑定一个含版本的完整 profile key。不得按数组位置、名称或页面排序临时生成编号。

| 类型 | 编号 | 风格 | 固定 profile key |
| --- | --- | --- | --- |
| 流程图 | FC-01 | 浅色业务流程 | flowchart/soft-process@1.0.0 |
| 流程图 | FC-02 | 经典黑白流程 | flowchart/classic-mono@1.0.0 |
| 泳道流程图 | FC-03 | 浅色分区泳道 | flowchart/soft-swimlanes@1.0.0 |
| 泳道流程图 | FC-04 | 深色标题泳道 | flowchart/contrast-swimlanes@1.0.0 |
| 流程图 | FC-05 | 黑白横向协作流程 | flowchart/monochrome-horizontal-collaboration@1.0.0 |
| 流程图 | FC-06 | 全局深蓝标题泳道 | flowchart/global-header-swimlanes@1.0.0 |
| 流程图 | FC-07 | 手绘设计讨论流程 | flowchart/handdrawn-design-board@1.0.0 |
| 流程图 | FC-08 | 手绘运行边界流程 | flowchart/handdrawn-runtime-flow@1.0.0 |
| 流程图 | FC-09 | 细线组件交互流程 | flowchart/thin-line-component-flow@1.0.0 |
| 流程图 | FC-10 | 柔色文档处理流程 | flowchart/pastel-document-pipeline@1.0.0 |
| 时序图 | SQ-01 | 蓝框机构时序 | sequence/institutional-blue@1.0.0 |
| 时序图 | SQ-02 | 经典黑白时序 | sequence/classic-mono@1.0.0 |
| 时序图 | SQ-03 | 蓝绿分阶段时序 | sequence/blue-green-phases@1.0.0 |
| 时序图 | SQ-04 | 浅色折角注释时序 | sequence/pale-folded-notes@1.0.0 |
| 时序图 | SQ-05 | 手绘粉彩分支时序 | sequence/handdrawn-pastel-branches@1.0.0 |
| 状态图 | ST-01 | 经典黑白状态 | state/classic-mono@1.0.0 |
| 状态图 | ST-02 | 浅色卡片状态 | state/soft-cards@1.0.0 |
| 架构图 | AR-01 | 浅色分层架构 | architecture/soft-layered@1.0.0 |
| 架构图 | AR-02 | 精致卡片架构 | architecture/premium-cards@1.0.0 |
| 架构图 | AR-03 | 浅色分层交互 | architecture/layered-interactions@1.0.0 |
| 架构图 | AR-04 | 暖底深绿分区 | architecture/contrast-process-bands@1.0.0 |
| 架构图 | AR-05 | 蓝绿密集分区 | architecture/blue-green-grid@1.0.0 |
| 架构图 | AR-06 | 蓝绿密集细节 | architecture/blue-green-detailed@1.0.0 |
| 架构图 | AR-07 | 蓝粉生态能力矩阵 | architecture/ecosystem-capability-matrix@1.0.0 |
| 架构图 | AR-08 | 跨域分层交互 | architecture/cross-boundary-layers@1.0.0 |
| 架构图 | AR-09 | 三栏分区与反馈闭环 | architecture/three-column-feedback@1.0.0 |
| 架构图 | AR-10 | 蓝紫虚线分区架构 | architecture/dashed-layered-cards@1.0.0 |
| 架构图 | AR-11 | 浅色横向分层矩阵 | architecture/stacked-layer-matrix@1.0.0 |
| 架构图 | AR-12 | 浅蓝图标分层面板 | architecture/blue-layered-icon-panels@1.0.0 |
| 架构图 | AR-13 | 侧栏保障分层矩阵 | architecture/framed-layered-matrix@1.0.0 |
| 架构图（历史兼容） | AR-14 | 手绘设计讨论架构 | architecture/handdrawn-design-board@1.0.0 |
| 架构图 | AR-15 | 双侧生态与能力矩阵 | architecture/dual-ecosystem-capability-band@1.0.0 |
| 数据流图 | DF-01 | 手绘粉彩数据流 | data-flow/pastel-handdrawn@1.0.0 |
| 拓扑图 | TP-01 | 橙红图标链路 | topology/icon-chain@1.0.0 |
| 拓扑图 | TP-02 | 分层图标集群拓扑 | topology/layered-service-clusters@1.0.0 |
| 时间线图 | TL-01 | 彩色里程碑卡片 | timeline/color-milestone-cards@1.0.0 |
| 时间线图 | TL-02 | 多层时期事件时间轴 | timeline/multilane-era-axis@1.0.0 |
| ER 图 | ER-01 | 浅色表结构 | er/soft-tables@1.0.0 |
| ER 图 | ER-02 | 经典黑白 ER | er/classic-mono@1.0.0 |
| ER 图 | ER-03 | 多域 DDL 表结构 | er/domain-ddl@1.0.0 |

## 调用与解析

自然语言：`读取 SKILL.md，使用 SQ-01 风格绘制以下时序图。`

脚本：`python scripts/catalog.py resolve --number SQ-01`，或 `resolve --style SQ-01`。编号大小写不敏感，返回规范化大写编号。未填写图种时由完整 key 推导；另给图种或版本时必须与编号一致。未知编号不回退。编号和另一个 style 参数不可同时提供。

生成 metadata 时同时记录 `number` 和完整 `key`，以完整 key 作为规范与 token 的来源。既有通过图种、风格名或完整 key 的调用保持可用。

## 新增编号

先按[扩展与兼容规范](extensions-v1.md)创建新风格或新版本，再在该图种定义文件的风格条目写入未使用过的 `number`。前缀沿用 FC / SQ / ST / AR / ER / TP / TL / DF，同组从现有最大序号继续分配；新图种在类型定义中声明未使用的前缀。一种风格的每个新版本分配新号，旧号永久绑定旧 key，不删除、不改绑、不复用、不压缩空缺。

生成预览前每个风格版本都须有唯一编号。新增映射后执行 `validate`、`lock --append` 和 `gallery --output assets/style-gallery.html`。编号映射被锁文件冻结；普通扩展不得重写基线。历史入口迁移见[变更记录](changelog.md)。
