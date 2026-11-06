# 技能文件结构与协作

本文说明 `technical-diagrams` 的文件分层、各目录职责，以及一次绘图从选择到交付时各文件如何协作。它是结构说明，不替代任何规范；具体规则仍以对应规范文件为准。

## 一、分层总览

```text
technical-diagrams/
├── SKILL.md                          # 入口层：AI 行为规则与调用方式
├── README.md                         # 人读说明
├── agents/openai.yaml                # 平台发现描述
│
├── registry/                         # 索引层：唯一事实源
│   ├── index.json                    # 一级索引：图种清单 + 共享注册路径
│   ├── types/<图种>.json              # 二级索引：该图种全部风格/编号/默认值/指南
│   └── shared/
│       ├── line-styles.json          # 线条样式注册
│       └── interaction.json          # 交互规范注册
│
├── styles/<图种>/<风格>/<版本>/        # 定义层：一个风格一个自包含目录
│   ├── SPEC.md                       # 视觉与排版规则
│   ├── tokens.json                   # 颜色/字体/尺寸等设计变量
│   ├── example.svg                   # 标准示例（内嵌复绘模型与依赖哈希）
│   ├── reference-analysis.md         # 可选：该风格的原图视觉分析
│   └── feature-atlas.svg             # 可选：该风格的特征展示图
│
├── types/<图种>/<语义版本>.md          # 定义层：该图种的业务语义约束
│
├── references/                       # 规范与按需指南
│   ├── common/1.0.0.md               # 全图种公共约定
│   ├── interaction-standards/1.0.0.md、1.0.0.svg
│   ├── line-styles-v1.md             # 三种线条的几何细则
│   ├── html-integration-v1.md        # HTML 交付与布局验收
│   ├── style-numbering-v1.md         # 固定编号规则
│   ├── extensions-v1.md              # 注册表格式与扩展流程
│   ├── reference-image-completeness.md # 参考图分析、复刻与扩展的共用验收
│   ├── reference-image-extension-workflow.md
│   ├── changelog.md                  # 历史迁移记录
│   └── type-guides/<图种>.md          # 按需加载的图种使用指南
│
├── scripts/
│   ├── catalog.py                    # 注册表读取/校验/解析/画廊
│   └── render_svg.mjs                # SVG → PNG + 几何检查
├── assets/
│   ├── gallery-shell.html            # 画廊模板
│   └── style-gallery.html            # 生成产物
├── tests/                            # 注册与逐风格回归测试
└── catalog.lock.json                 # 冻结基线
```

分层职责：

- **入口层**只保留"怎么调用、必须遵守什么"，不枚举具体风格。
- **索引层**回答"有哪些图种、风格、编号、默认值"，是运行时唯一事实源。
- **定义层**存放每个风格、每个图种的独立定义，彼此隔离、可单独演进。
- **规范层**存放跨图种的通用规则与按图种加载的指南。
- **工具层**负责解析、校验、渲染和预览生成，不承载业务内容。

归属原则：只有跨图种共用的规范、指南和索引放在 `references/`；只属于某个风格的原图、视觉分析与特征展示图，一律随该风格放入 `styles/<图种>/<风格>/<版本>/`，不进入 `references/`。

## 二、目录与文件职责

| 路径 | 作用 | 主要消费者 |
| --- | --- | --- |
| [SKILL.md](../SKILL.md) | 技能入口：图种/风格/线条选择方式、必须遵守的渲染规则、何时读哪份文档 | AI 代理 |
| [README.md](../README.md) | 人类可读的安装、用法、字段说明、图种指南索引 | 人 |
| [agents/openai.yaml](../agents/openai.yaml) | 外部平台发现技能的元数据，与运行逻辑无关 | 平台 |
| [registry/index.json](../registry/index.json) | 一级索引：图种列表、公共规范版本、共享注册位置 | `catalog.py` |
| `registry/types/<图种>.json` | 二级索引：单个图种的风格、编号、别名、默认值、`guide` 路径 | `catalog.py` |
| `registry/shared/*.json` | 线条样式与交互规范的注册，独立于图种 | `catalog.py` |
| `styles/<图种>/<风格>/<版本>/` | 一套可复用视觉方案：规则、设计变量、标准示例；授权的原图分析 `reference-analysis.md` 与特征展示图 `feature-atlas.svg` 只属于该风格，也放在同一目录 | AI 绘图、画廊 |
| `types/<图种>/<版本>.md` | **业务语义**：该图种允许的节点、边、方向、基数等 | AI 绘图 |
| `references/type-guides/<图种>.md` | **使用指南**：风格速览、原图/分析链接、该图种专属经验规则 | AI 绘图（按需） |
| `references/*.md` | 跨图种规范：公共约定、线条、交互、HTML、编号、扩展流程 | AI 绘图、扩展时 |
| [scripts/catalog.py](../scripts/catalog.py) | 组合注册表、解析风格、校验冻结基线、生成 lock 与画廊 | CLI、AI、测试 |
| [scripts/render_svg.mjs](../scripts/render_svg.mjs) | 用 Playwright 渲染 PNG，并检查越界、文字重叠、连线遮挡等 | CLI、验证 |
| [assets/style-gallery.html](../assets/style-gallery.html) | 全风格预览页，由 `gallery` 命令生成 | 人 |
| `tests/` | 注册表隔离、版本固定、逐风格 SVG 结构回归；`scenarios.md` 为人工验收场景 | 开发者 |
| [catalog.lock.json](../catalog.lock.json) | 冻结旧 profile、编号、默认值和依赖哈希，防止无意改动 | `validate` |

## 三、一次绘图的协作链路

### 1. 解析风格

```text
catalog.py resolve --number FC-03
   │
   ├─ 读 registry/index.json            → 图种清单 + 共享注册路径
   ├─ 读 registry/types/flowchart.json  → 定位 soft-swimlanes@1.0.0
   ├─ 读 registry/shared/line-styles.json、interaction.json
   └─ 组合并校验文件存在
   ↓
返回一组确定路径，AI 只读这些文件
```

`resolve` 返回的主要字段：

| 字段 | 指向 |
| --- | --- |
| `common_path` | 公共规范 |
| `type_spec_path` | 图种语义规范 |
| `type_guide_path` | 当前图种的指南 |
| `spec_path`、`tokens_path` | 风格规则与设计变量 |
| `example_path` | 该风格标准示例 |
| `line_spec_path` | 线条几何规范 |
| `interaction_spec_path`、`interaction_example_path` | 交互规范与示例 |
| `dependency_hashes` | 各入口文件的 SHA256 |

**按需加载**体现在这里：只返回当前图种的指南，其他图种的 `references/type-guides/*.md` 与风格规范不会进入上下文。`type_guide_path` 不进入 `dependency_hashes`，因此更新图种指南不会让旧 SVG 的依赖校验失效。

当任务提供参考图用于分析、复刻或扩展时，按 `SKILL.md` 另读 `reference-image-completeness.md`；仅持久扩展技能时再读 `reference-image-extension-workflow.md`。这两份条件参考不改变 `resolve` 的图种与风格依赖闭包。

### 2. 绘图与元数据闭环

```text
按返回路径读规范 → 生成 SVG / HTML
   ↓
SVG metadata 写入：
  profile key、semantic_version、model、
  line_style(id/version/source)、interaction_standard、
  overrides.connectors、dependencies(各文件哈希)
   ↓
render_svg.mjs 渲染 PNG + 几何检查
   ↓
validate 校验注册完整性与冻结基线
```

`dependencies` 的作用是防止"规范被悄悄改动而旧图结果漂移"：任何影响出图结果的入口文件变化，都会让旧图元数据哈希对不上，测试随即报错。

### 3. 预览与测试

- `catalog.py gallery` 读取注册表并嵌入各 `example.svg`，生成 `assets/style-gallery.html`。
- `tests/test_catalog.py` 验证注册表结构、版本固定与图种隔离；每个风格另有独立测试，检查 SVG 的节点、连线、metadata 与画廊卡片。
- `tests/scenarios.md` 是行为验收清单，覆盖泳道选型、单向箭头、ER 基数、HTML 代码块等真实使用场景。

## 四、三层索引的区别

| 文件 | 回答的问题 |
| --- | --- |
| `registry/index.json` | 支持哪些图种？公共规范与共享注册在哪？ |
| `registry/types/<图种>.json` | 该图种有哪些风格、编号、默认风格和指南？ |
| `catalog.lock.json` | 过去已对外承诺的 key、编号、默认值和哈希是什么？ |

前两者是**当前可用集合**，lock 是**历史承诺快照**。新增可以，改动已冻结项会被 `validate` 拒绝；需要变更时新增版本并走 `lock --append`。

## 五、新增内容时的触点

| 场景 | 需要修改 | 不需要修改 |
| --- | --- | --- |
| 新增一个风格 | 对应 `registry/types/<图种>.json` 的 `styles[]` 与 `style_versions`；新建 `styles/<图种>/<风格>/<版本>/`；更新该图种指南与 README；执行 `lock --append` | SKILL.md、`catalog.py` |
| 新增一个图种 | 新建 `registry/types/<图种>.json`、`types/<图种>/<版本>.md`、`references/type-guides/<图种>.md`、风格目录；在 `registry/index.json` 的 `types` 增加一项 | SKILL.md |
| 修改已冻结风格 | 不允许直接改；新增版本并登记新编号 | 旧版本目录、旧 lock 条目 |

目录与命名约定：

- 图种 id 与目录名统一 `kebab-case`，风格 id 与目录名一致。
- 资源路径由约定推导（`styles/<图种>/<风格>/<版本>/`、`types/<图种>/<版本>.md`），不在 JSON 中重复保存。
- 固定编号前缀为 `FC`、`SQ`、`ST`、`AR`、`ER`、`TP`、`TL`、`DF`，全局唯一，新版本分配新编号。

## 六、两个容易混淆的点

1. **`types/<图种>/<版本>.md` 与 `references/type-guides/<图种>.md` 不同**：前者是"该图种在业务上允许什么"（语义约束），后者是"怎么用该图种画得好"（风格速览、经验规则、链接）。
2. **`styles/.../example.svg` 不只是示例**：它同时是画廊素材与元数据样板，`dependencies` 哈希与它互相绑定，不能随意替换内容。

## 七、维护约定

- 结构发生变化（新增目录、改变索引格式、调整加载边界）时，同步更新本文与 [extensions-v1.md](extensions-v1.md)。
- 普通绘图不修改注册表、规范或本文件；只有用户明确要求扩展能力时才走 [参考图扩展工作流](reference-image-extension-workflow.md)。
- 本地 `scripts/node_modules/` 仅用于渲染验证，已被 `.gitignore` 排除，不属于技能交付内容。
