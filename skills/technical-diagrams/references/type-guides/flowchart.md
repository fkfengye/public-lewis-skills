# 流程图使用指南

语义契约以 `resolve` 返回的 `type_spec_path` 为准（[流程图 1.0.0](../../types/flowchart/1.0.0.md)）。本指南只补充选型、泳道和节点写法；通用连线与交互规则仍读主技能与 `resolve` 返回的规范。

## 风格速览

| 编号 | 风格 | 适合 | 资源 |
| --- | --- | --- | --- |
| FC-01 | 浅色业务流程 | 默认；单链路、条件分支、无泳道职责图 | [SPEC](../../styles/flowchart/soft-process/1.0.0/SPEC.md) · [示例](../../styles/flowchart/soft-process/1.0.0/example.svg) |
| FC-02 | 经典黑白流程 | 打印、正式文档、低彩度 | [SPEC](../../styles/flowchart/classic-mono/1.0.0/SPEC.md) · [示例](../../styles/flowchart/classic-mono/1.0.0/example.svg) |
| FC-03 | 浅色分区泳道 | 柔和展示职责归属 | [SPEC](../../styles/flowchart/soft-swimlanes/1.0.0/SPEC.md) · [示例](../../styles/flowchart/soft-swimlanes/1.0.0/example.svg) |
| FC-04 | 深色标题泳道 | 更突出系统名与职责说明 | [SPEC](../../styles/flowchart/contrast-swimlanes/1.0.0/SPEC.md) · [示例](../../styles/flowchart/contrast-swimlanes/1.0.0/example.svg) |
| FC-05 | 黑白横向协作流程 | 横向参与方协作、黑白文档 | [分析](../../styles/flowchart/monochrome-horizontal-collaboration/1.0.0/reference-analysis.md) · [示例](../../styles/flowchart/monochrome-horizontal-collaboration/1.0.0/example.svg) |
| FC-06 | 全局深蓝标题泳道 | 跨部门流程、反馈回路 | [分析](../../styles/flowchart/global-header-swimlanes/1.0.0/reference-analysis.md) · [示例](../../styles/flowchart/global-header-swimlanes/1.0.0/example.svg) |
| FC-07 | 手绘设计讨论流程 | 设计讨论、便签与批注 | [SPEC](../../styles/flowchart/handdrawn-design-board/1.0.0/SPEC.md) · [分析](../../styles/architecture/handdrawn-design-board/1.0.0/reference-analysis.md) |
| FC-08 | 手绘运行边界流程 | 运行边界、资源池、处理与反馈 | [原图](../../assets/reference-examples/fc-08-original.png) · [SPEC](../../styles/flowchart/handdrawn-runtime-flow/1.0.0/SPEC.md) · [分析](../../styles/flowchart/handdrawn-runtime-flow/1.0.0/reference-analysis.md) · [示例](../../styles/flowchart/handdrawn-runtime-flow/1.0.0/example.svg) |
| FC-09 | 细线组件交互流程 | 核心组件、外围多路交互和分格面板 | [原图](../../assets/reference-examples/fc-09-original.png) · [SPEC](../../styles/flowchart/thin-line-component-flow/1.0.0/SPEC.md) · [分析](../../styles/flowchart/thin-line-component-flow/1.0.0/reference-analysis.md) · [示例](../../styles/flowchart/thin-line-component-flow/1.0.0/example.svg) |
| FC-10 | 柔色文档处理流程 | 实线系统边界、折角文件、圆柱与对话云 | [原图](../../assets/reference-examples/fc-10-original.jpg) · [SPEC](../../styles/flowchart/pastel-document-pipeline/1.0.0/SPEC.md) · [分析](../../styles/flowchart/pastel-document-pipeline/1.0.0/reference-analysis.md) · [基础示例](../../styles/flowchart/pastel-document-pipeline/1.0.0/example.svg) · [字体展示](../../styles/flowchart/pastel-document-pipeline/1.0.0/typography-example.svg) |

## 泳道选型

泳道是 `flowchart` 的职责布局，不另造图种。新图可选 FC-03、FC-04 或 FC-06；只说“带泳道的流程图”且无已选风格或可恢复元数据时，列出三者供选择。用户明确允许自行决定时说明所选风格；复绘已有图优先恢复其选择，不静默套用 FC-01。未要求泳道的普通流程图默认仍为 FC-01。

## 节点与泳道写法

- 处理节点用一句话概括“谁做什么”，节点内用无序列表逐项说明输入、校验、关键动作、结果或约束；只写来源中实际存在的要点。标题与列表分层，正文左对齐，换行采用悬挂缩进；按真实文字度量扩容。
- 判断节点用明确判断句作标题，列表解释判断依据，出口标清各自条件。菱形按实际形状验收标题、模块标签、每行文字和项目符号的角点，不能只查外接矩形。
- 先为节点记录模块或系统 owner，再按职责设泳道、分区及清晰标题。泳道表示归属，不表示先后阶段或自动增加部署单元；一个处理框涉及多方时按实际动作拆分或注明调用关系。
- 分支属于哪个模块就在该模块内就近布置，不能把拒绝、成功等结果当成系统名。泳道标题等高、顶部对齐；长图通过节点 owner 标签辅助定位，不反复插入标题栏截断连线。

## 特殊风格

- FC-05：实体节点保留来源中的参与方名称，不凭空扩写为动作；独立实虚线、上下分支与外侧绕行见分析。线型语义由来源确定。
- FC-06：全图标题带、白色泳道表头和蓝灰节点；按资料确定归属和分支。
- FC-07：手写字、线内标签留空、便签指向、贴附图标与平行线路均按实际来源确定；注释箭头与业务边分别建模。字体缺失时使用可读后备，不假定英文手写字体涵盖中文。历史 AR-14 仍可解析为旧架构风格。
- FC-08：以虚线运行边界、柔和椭圆池、堆叠资源、外置工作单元和编号流程组合表现；步骤主标签嵌于连线真实间隙，云图采用深浅蓝错层，优先使用 Virgil 和 Xiaolai 手写字体，离线交付嵌入所需字形及许可。叠片数量与颜色不推断实例关系或业务含义。原图经用户授权随技能和预览分发。
- FC-09：白底、米色虚线主体、灰色底带、浅蓝列表、叠片、分格和细线多路交互；组件可直接作为节点。原图粗竖条与交叉线语义不明，共享通道、组件归属及箭头端点均按实际模型确定。原图经用户授权随技能和预览分发。
- FC-10：浅灰实线边界、粉色文档组、绿色圆柱、带尖尾的输入气泡和单层黑边浅紫输出云。新图未指定文字排版时，气泡内斜体文字以文本块居中、块内各行左对齐；标题比普通节点更显著，字号和换行依实际字形测量并留出边界空间。具体比例可参考[字体展示](../../styles/flowchart/pastel-document-pipeline/1.0.0/typography-example.svg)，采用的覆盖须记录在复绘元数据；用户明确指定和已有图的排版元数据优先。已冻结的基础示例和 token 不变。原图字体无法从位图准确识别，中文使用可读后备。文件折角与同一批项目的顺序变化在有来源时保留；节点归属和连线只按实际模型确定。原图经用户授权随技能和预览分发。
