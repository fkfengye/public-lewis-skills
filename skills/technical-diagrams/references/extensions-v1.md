# 扩展与兼容契约 v1

## 不影响旧风格的边界

一个完整编号 `type/style@x.y.z` 绑定 common_spec、semantic_spec、SPEC.md、tokens.json、example.svg 的完整依赖闭包；独立线条选择另外绑定确定版本的线条规范及摘要。调用时只加载解析出的依赖，不自动合并其他风格、新全局 token 或“latest”规范。固定视觉编号不绑定线条外观，最终几何同时由独立线条选择决定。

`catalog.lock.json` 是兼容性基线，不是安全签名。它冻结旧 key 的注册映射、别名、默认值、无版本调用的固定版本，以及既有依赖文件摘要。人工重写基线会绕过此保护，应在评审中禁止。

依赖摘要按 **LF 规范化字节**计算（`\r\n` 统一为 `\n`），与检出平台及 `core.autocrlf` 设置无关：同一内容在 Windows CRLF 与 Linux LF 工作区得到相同摘要，不会因行尾转换被误判为冻结资源被修改。基线迁移只刷新获批入口与已确认资源的文件摘要，`types`、`profiles`、`style_numbers`、别名和默认值逐项保持不变。

`line_styles` 的既有默认值、版本、名称、别名与线条规范摘要同样冻结。追加线条选项不占用视觉编号，也不复制视觉 profile。更改旧选项或规范需显式版本升级和迁移评审；`resolve` 必须验证线条依赖，不能在摘要变化后静默使用。

## 注册表目录与文件格式

```text
registry/
├── index.json                  # 一级索引：图种顺序与共享注册
├── types/
│   └── <图种>.json             # 二级定义：图种元数据 + 风格清单
└── shared/
    ├── line-styles.json        # 独立线条注册
    └── interaction.json        # 单向交互规范注册
```

- 图种顺序由 `registry/index.json` 的 `types` 数组决定；只允许出现 `registry/types/<图种>.json` 中存在的 ID。
- 文件名、`id`、图种目录名与风格目录名必须一致，统一使用小写连字符 ID；版本统一为 `x.y.z`。
- 风格资源路径由约定推导，不在 JSON 中重复存储：`styles/<图种>/<风格>/<版本>/SPEC.md`、`tokens.json`、`example.svg`；图种语义规范为 `types/<图种>/<semantic_version>.md`。
- `tokens.json` 的 `profile` 必须等于完整 key `<图种>/<风格>@<版本>`。
- 图种别名全局唯一；风格 ID、名称、别名在同一图种内按去空格/大小写归一化后唯一；固定编号全局唯一，格式为 `<前缀>-NN`。

`registry/index.json`：

```json
{
  "schema_version": 1,
  "skill_version": "1.9.0",
  "common": { "version": "1.0.0", "spec": "references/common/1.0.0.md" },
  "types": ["flowchart", "sequence", "state", "architecture", "er", "topology", "timeline", "data-flow"],
  "line_styles": "registry/shared/line-styles.json",
  "interaction_standard": "registry/shared/interaction.json"
}
```

`registry/types/<图种>.json`：

```json
{
  "schema_version": 1,
  "id": "state",
  "name": "状态图",
  "aliases": ["状态机"],
  "semantic_version": "1.0.0",
  "number_prefix": "ST",
  "guide": "references/type-guides/state.md",
  "default": "state/classic-mono@1.0.0",
  "style_versions": { "classic-mono": "1.0.0", "soft-cards": "1.0.0" },
  "styles": [
    {
      "id": "classic-mono",
      "version": "1.0.0",
      "number": "ST-01",
      "name": "经典黑白状态",
      "aliases": ["黑白状态"]
    },
    {
      "id": "soft-cards",
      "version": "1.0.0",
      "number": "ST-02",
      "name": "浅色卡片状态",
      "aliases": ["浅色状态"],
      "gallery_layout": "wide"
    }
  ]
}
```

可选字段：风格的 `semantic_version`、`common_version`（默认继承图种）、`layout`（如 `swimlane`）、`gallery_layout`；图种的 `gallery_layout`、`guide`。`guide` 指向该图种的按需指南；缺失时 `resolve` 不返回 `type_guide_path`。

## 新增一种风格

根据参考图新增风格时，先按 `SKILL.md` 加载共用的 `reference-image-completeness.md` 与扩展工作流；普通复刻不触发注册变更。

1. 创建独立目录 `styles/<图种>/<new-id>/1.0.0/`，提供 `SPEC.md`、完整 `tokens.json`、通用 `example.svg`。不直接引用另一个风格的可变 token，也不复用其规范路径。
2. 在该图种的 `registry/types/<图种>.json` 的 `styles` 数组追加条目，并在 `style_versions` 追加该 ID 的固定版本；保留既有 default、旧 pin、类型别名与规范路径。别名在同图种内仍须唯一。
3. 分配新的固定编号并写入条目；不得复用或重绑旧编号。同步在 `references/type-guides/<图种>.md` 的速览表补一行（仅文档，不影响解析）。
4. 执行 `python -B <技能目录>/scripts/catalog.py validate`，旧基线必须仍通过。按新风格绘制/渲染一个示例，并检查长标签、自循环等相关边界。
5. 执行 `python -B <技能目录>/scripts/catalog.py lock --append`。此命令先验证旧基线，再补充新条目，不能掩盖旧文件或解析映射被修改。
6. 刷新风格预览并运行 `python -B -m unittest discover -s <技能目录>/tests`。对旧完整编号再次 resolve，加载文件、token 和默认值应保持一致。

**新增普通风格不需要修改 `SKILL.md`**；只有风格带来新的通用行为约束时才更新主技能，并按入口迁移处理。

## 新增图种

1. 新增 `types/<图种>/1.0.0.md` 语义规范，明确节点/边类型、端口和禁止项。
2. 新增 `registry/types/<图种>.json`，声明 ID、名称、别名、语义版本、编号前缀、默认 key、`style_versions` 与 `styles`；至少包含一个风格条目。
3. 在 `registry/index.json` 的 `types` 数组追加 ID；顺序即列表与预览顺序。
4. 创建 `styles/<图种>/...` 资源；可选新增 `references/type-guides/<图种>.md` 指南并在类型定义中填 `guide`。
5. 运行 `validate`、示例检查和 `lock --append`。`SKILL.md` 的图种索引不逐项枚举，**无需修改主技能**。

## 新增规范版本

- 新语义版本新增 `types/<图种>/2.0.0.md`，不要改 1.0.0；需要采用新语义的风格快照发布新版本，条目显式写 `semantic_version: "2.0.0"`。旧 key 仍读取旧语义文件。
- 新公共规范同理新增 `references/common/2.0.0.md`，由新快照显式引用 `common_version`。不要把新的全局颜色、箭头或默认值注入旧版本。
- 同一风格新增 2.0.0 时保留旧 `style_versions` 固定值；显式 `resolve --version 2.0.0` 才使用新版本。切换既有默认版本是单独迁移操作，需用户明确要求并评审新基线，不当作普通追加扩展。

## 独立线条与交互规范

- 使用独立线条时遵守[线条规范 v1](line-styles-v1.md)：用户明确指定 > 原图元数据 > 固定默认值；旧 `overrides.connectors` 可识别的选择应沿用并归一化记录。
- 交互规范独立绑定 ID、版本、规范和通用示例，不占用视觉编号；每次 `resolve` 返回 `interaction_standard / interaction_standard_version / interaction_spec_path / interaction_example_path`，两份资源均进入依赖摘要。
- 注册/资源不存在、ID 冲突、别名冲突、路径越界、旧 key 重映射均报错，不降级到默认风格。需要注册新风格须用户明确要求；普通参考图复刻用本次任务覆盖参数并记录 metadata，不自动污染共享目录。

## 入口迁移

- 只有改变主技能行为、路由工具或冻结规范时才做入口迁移；普通新增风格/图种不触发。
- 迁移仅刷新获批入口文件（通常是 `SKILL.md`、`scripts/catalog.py`、本文件及对应规范）的基线摘要；既有 types、profiles、style_numbers、资源与摘要逐项保持一致。
- 迁移不改变普通 `lock --append` 的先校验再追加契约；不提供 `--force` 或通用重建基线入口。

历史迁移记录见[变更记录](changelog.md)。
