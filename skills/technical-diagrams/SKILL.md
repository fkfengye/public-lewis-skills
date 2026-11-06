---
name: technical-diagrams
description: Use when creating, redrawing, or restyling technical flowcharts (including swimlane flowcharts), sequence diagrams, state diagrams, architecture diagrams, topology diagrams, data flow diagrams, timelines, or entity relationship (ER) diagrams, or when explicitly extending this skill's diagram capabilities from reference images.
---

# 通用技术画图

图种、视觉样式和线条样式独立选择：图种定义业务语义，视觉样式定义配色与排版，线条样式定义连线几何。各规范绑定确定版本；适用于中文技术文档、可编辑 SVG、高清 PNG 和 HTML 内嵌图。每次绘图同时遵循版本化的单向交互规范，它不重选视觉风格或线条样式。

## 快速开始

从技能目录之外的工作目录运行，产物与临时文件统一保存到该目录的 `.data-cache/`。`<技能目录>` 指本文件所在目录的绝对或相对路径，随安装位置变化：

```text
python -B <技能目录>/scripts/catalog.py list --type flowchart
python -B <技能目录>/scripts/catalog.py list --line-styles
python -B <技能目录>/scripts/catalog.py resolve --number FC-01 --line-style 圆角折线
```

自然语言可直接说：`使用 technical-diagrams 绘制流程图，样式浅色业务流程（或 FC-01），线条样式圆角折线，输出 SVG 与 PNG。`

## 选择入口与 AI 行为规则

1. **图种以 `registry/index.json` 的 `types` 索引为准**，每个图种的定义文件是 `registry/types/<图种>.json`。已有资料能确定图种时不重复询问；不要按目录名猜版本或扫描全部图种。
2. **视觉样式**支持完整名称、ID、别名、固定编号和完整 profile key。先用 `list --type <图种>` 或[风格预览](assets/style-gallery.html)查看；编号用 `resolve --number ST-01` 或 `--style ST-01`，其他形式用 `resolve --type <图种> --style <名称或ID> --version <版本>`，或 `--style state/classic-mono@1.0.0`。编号固定绑定原风格版本。
3. **线条样式**独立用 `--line-style <ID或中文名称>` 选择，不占用 FC/SQ/ST/AR/ER/TP/TL/DF 编号：`orthogonal` 直角折线（默认）、`rounded-orthogonal` 圆角折线、`curved` 直连曲线；同一视觉样式可组合三种线条。
4. 视觉与线条遵循 **本次明确指定 > 当前图元数据 > 注册表固定默认值**。旧图只有 `overrides.connectors` 时，沿用可识别的线条选择并归一化记录；无法识别时用默认值并说明。未知编号、名称、版本或图种冲突必须报错，不静默回退。
5. **按需加载**：读取 `resolve` 返回的 `common_path`、`type_spec_path`、`type_guide_path`、`spec_path`、`tokens_path`、`line_spec_path`、`interaction_spec_path` 及本主文件明确要求的条件参考，查看 `example_path` 与 `interaction_example_path`。`type_guide_path` 只属于当前图种（`references/type-guides/<图种>.md`），其中包含该图种的风格速览、原图/分析链接与专属规则；不要加载其他图种的指南或风格规范。每次绘图另读[通用布局验收](references/html-integration-v1.md#通用布局验收所有图种)；编辑 HTML 时同时读取该文件的交付与代码块条款。
6. **直连优先**：端口共线且无障碍时直接连接；只有避让节点、文字、端口或分组边界确有需要时才增加转折。圆角折线使用真实 `Q`/`A` 路径，常规半径 `18`，短段收缩；外侧汇流拐角圆角化，内部 T 形汇流保持连续。非共线端口采用直连曲线时优先平滑 `C` 路径。几何细则读取 `line_spec_path`。
7. **语义优先于外观**：各图种的端口、方向、基数、时间尺度等约束以 `type_spec_path` 为准；线条和视觉不得改变同步/异步、关系方向或时间精度。含基数语义的关系线，**线旁标签必须同时给出关系名与基数比例**（如 `1 : 0..*`），不得只把基数集中放进图例或注记卡；未知基数写「基数待确认」。
8. **每根有向交互线只保留一个方向箭头**：请求与返回分别布线、分离端口；请求用实线，返回或确认用独立虚线。Webhook、结果提交和业务回调即使向上，仍是实线独立请求，其处理确认另画虚线。状态迁移不凭空加返回；ER 双端鸟爪属于基数，不能当双向消息箭头删除。
9. **先定归属与对齐网格**：下游机构、银行、第三方系统不因被平台调用就归入平台内部；按真实边界独立成板块。同层系统外框统一宽度与对齐基线，同类模块统一尺寸和端口间距，复杂内容按需扩高或分图。
10. **量化布线，按「最小弯折数 → 最短路径 → 最少交叉数」取舍**：在语义、端口、不穿字/节点、箭头与标签留白等硬约束成立的前提下，逐边比较可行端口、邻接位置与 ER 字段展示行，先取弯折数 `B` 最小，`B` 相同时取路径长度 `L` 最短，仍相同时取全图交叉数 `C` 最少，并记录更优替代方案的比较结果。减少交叉不得以增加弯折或路径长度为代价；剩余交叉一律用真实 `A/Q` 圆弧桥并标明「跨线不连接」，桥不改变所选线条样式，真实 T 形汇流保持连续，不能用遮罩掩盖穿字。指标定义与验收见 `line_spec_path`。
11. **完整逻辑编号**：架构交互、时序消息和流程步骤覆盖请求、受理、处理、结果与确认；返回各有编号，替代分支用 A/B 或子编号，独立旁路另标。异步序号表示逻辑/因果关系，不承诺全局到达先后；不将状态、ER 关系或时间线事件强排成消息执行顺序。
12. **参考图细节与验收**：普通参考图分析、复刻和扩展均读取[参考图完整性验收](references/reference-image-completeness.md)。先看全图和密集局部，逐项记录可辨认的形态、层次、文字、线条与关系；以「原图观察 → 输出位置 → 覆盖状态 → 核查依据」对照验收，缺漏先补齐；无法辨认、无法实现或用户要求简化的内容如实标记。不能因存在同类元素或自动检查通过就声称视觉特征完整。
13. **扩展与原图授权**：仅在用户要求把参考图分析结果持久加入本技能、扩展或完善图种/风格/线条能力时，另读[参考图扩展工作流](references/reference-image-extension-workflow.md)。用户未明确选择时，主动询问每张原图是否保存到技能、是否在预览中展示；说明保存的图片会随技能目录和生成的预览一起分发。本公开仓库默认不分发参考原图。已有明确同意或拒绝无需重复询问，按各自范围执行。未获明确授权不得保存或展示原图，等待答复期间继续可独立完成的分析与通用示例。普通一次性分析或复刻不加载扩展工作流，也不修改技能文件。
14. **HTML 默认独立完整交付**：将 SVG、样式、脚本及复绘模型全部内嵌到一个可离线打开的完整文件；模型放 SVG metadata 或内嵌 JSON。除非用户明确要求多文件，不额外输出 SVG、PNG、diagram.json 或 assets 目录；页面内下载按钮不等于预先交付附属文件。用户要求原地修改时写回指定文件，保留可恢复副本。含 SQL 等代码块时独立设置块级容器，隔离行内 code 样式。

注册表是可用图种、视觉样式、线条样式、交互规范、编号与默认值的唯一入口。普通绘图不修改注册表或技能文件；新增/变更注册走扩展规范。

## 执行与交付

- 提取节点/参与者/状态或实体与字段、边、条件、分组、约束、同步异步与来源依据，先写业务模型，再布局。修改样式时保留原模型；原图与正文矛盾须明确列出，不用美化更改业务规则。
- 按选定视觉样式的 token、排版规范与独立线条规范绘制。Mermaid 可用于草稿；精确复刻和连线控制优先使用显式 SVG 几何。
- 中文字号、标签行数和真实字体度量决定节点尺寸与行距；长标签换行或扩容，阶段条、alt/opt 标题和自循环占独立空间。
- 渲染检查全图与重点区域，核对真实形状内的文字、节点净间距、标题留白、端点出入方向、标签与路线、可直连替代路径及业务模型；端点节点也要检查。线条必须容纳箭头和条件标签。现有渲染脚本未覆盖节点相碰、端点方向或最短路径比较，应另查模型/SVG 或人工核看并如实记录覆盖范围。
- 保存复绘模型：固定视觉编号（若有）、完整 profile key、`semantic_version`、模型、独立 `line_style`（`id/version/source`）、`interaction_standard`（`id/version`）、`overrides.connectors` 实际覆盖项，以及 `dependencies` 中含线条与交互规范及示例的 SHA256。HTML 内嵌该模型；仅用户明确要求多文件时才附 `<图名>.diagram.json`。

## 工具与运行边界

- `validate` 检查注册、依赖、别名与冻结基线；依赖摘要按 LF 规范化字节计算，不受 `core.autocrlf` 行尾转换影响。`gallery` 刷新预览；`render_svg.mjs` 渲染 PNG 并做几何检查（`--help` 查看参数）。
- 脚本不安装依赖或修改权限。环境提供依赖查询工具时先获取 Node/Python/Playwright 路径；缺少浏览器渲染能力时保留源文件，并如实说明未完成的视觉验证。
- 临时脚本、缓存和验证产物统一放工作目录的 `.data-cache/`，不得写入技能目录。

## 使用位置

本目录可整体移动，内部资源路径相对技能目录解析。未安装时可直接让代理“读取此 SKILL.md 并执行”，这不等于技能已出现在选择器中。若需要 `$technical-diagrams` 发现式调用，由用户指定安装范围后安装到当前 Codex 支持的技能目录；不要因保存技能擅自修改全局配置。

## 何时阅读

| 何时阅读 | 文档 |
| --- | --- |
| 每次绘图或复绘，确定连线几何、图种限制、元数据与验收 | `resolve` 的 `line_spec_path`，当前为[线条规范 v1](references/line-styles-v1.md) |
| 每次绘图或复绘，处理单向交互、独立返回、系统边界、对齐、跨线与逻辑编号 | `resolve` 的 `interaction_spec_path`，当前为[交互规范 1.0.0](references/interaction-standards/1.0.0.md)；查看 `interaction_example_path` |
| 使用当前图种的专属规则、风格速览与原图/分析链接 | `resolve` 的 `type_guide_path`，即 `references/type-guides/<图种>.md` |
| 使用、解释或扩展固定视觉编号 | [固定编号规范](references/style-numbering-v1.md) |
| 每次绘图检查布局、端口与直连替代；编辑 HTML 时另验收单文件、代码块与导出 | [HTML 集成规范 v1](references/html-integration-v1.md) |
| 普通参考图分析、复刻和扩展，逐项记录细节、覆盖状态及验收依据 | [参考图完整性验收](references/reference-image-completeness.md) |
| 用户要求根据参考图新增或完善画图能力；普通绘图不读取 | [参考图扩展工作流](references/reference-image-extension-workflow.md) |
| 用户授权新增或变更图种、样式、线条注册及规范版本 | [扩展与兼容规范](references/extensions-v1.md) |
