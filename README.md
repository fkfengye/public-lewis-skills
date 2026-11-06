# public-lewis-skills

可复用的 AI Agent 技能集合，遵循 [Agent Skills](https://agentskills.io) 开放标准：每个技能是一个包含 `SKILL.md` 的目录，可被 Claude Code、Cursor、Codex、Gemini CLI、Trae、GitHub Copilot 等支持该标准的 agent 加载。

## 技能列表

| 技能 | 说明 |
| --- | --- |
| [technical-diagrams](skills/technical-diagrams/) | 通用技术画图：流程图、时序图、状态图、架构图、拓扑图、数据流图、时间线和 ER 图；40 个固定风格编号，图种、视觉样式与线条样式独立选择；输出可编辑 SVG、PNG 或离线 HTML |

## 安装

### 方式一：skills CLI（支持多 agent）

```bash
# 安装指定技能，自动识别本机已安装的 agent
npx skills add fkfengye/public-lewis-skills --skill technical-diagrams

# 安装到指定 agent
npx skills add fkfengye/public-lewis-skills --skill technical-diagrams -a claude-code -a cursor

# 安装全部技能到全部已检测到的 agent
npx skills add fkfengye/public-lewis-skills --all --agent '*'
```

安装后技能会位于 `~/.agents/skills/<技能名>`，并按各 agent 约定软链到对应目录。

### 方式二：手动克隆

```bash
git clone https://github.com/fkfengye/public-lewis-skills.git
```

然后把 `skills/<技能名>/` 复制到所用 agent 的技能目录，例如：

| Agent | 全局技能目录 |
| --- | --- |
| Claude Code | `~/.claude/skills/` |
| Cursor | `~/.cursor/skills/` |
| Codex | `~/.codex/skills/` |
| Trae / TraeWork | `~/.trae-cn/skills/` |

项目内使用可放到项目下的 `.agents/skills/` 或对应 agent 的项目技能目录。

### 方式三：TraeWork 上传技能

把 `skills/technical-diagrams/` 打包为 `SKILL.md` 位于压缩包根目录的 zip，然后在 TraeWork「插件市场 → 技能 → 上传技能」中选择该文件。

## 使用

安装后直接用自然语言描述任务，agent 会按 `SKILL.md` 的描述判断是否加载。也可以显式调用，例如：

```text
使用 technical-diagrams 绘制订单处理流程，
样式 FC-08，线条样式圆角折线，输出可编辑 SVG。
```

未安装时，也可以直接让 agent 读取仓库中的 `skills/<技能名>/SKILL.md` 并执行。

## 目录结构

```text
skills/
└── technical-diagrams/
    ├── SKILL.md          # 技能入口与执行规则
    ├── README.md         # 使用者说明
    ├── scripts/          # catalog.py（风格路由与校验）、render_svg.mjs（渲染与几何检查）
    ├── registry/         # 两级注册表：图种索引 + 图种定义 + 线条/交互规范
    ├── types/            # 各图种的语义规范
    ├── styles/           # 固定风格快照：SPEC、tokens、示例、分析
    ├── references/       # 按需加载的公共规范与图种指南
    ├── assets/           # 风格画廊与授权原图
    └── tests/            # 注册表、风格与依赖一致性测试
```

## 环境要求

- Python 3.9+（`catalog.py` 仅用标准库）
- Node.js 20+ 与 Playwright/Chromium：仅导出 PNG 时需要

## 许可

本仓库以 [Apache License 2.0](LICENSE) 发布。

部分示例嵌入第三方字体，许可见对应风格目录下的 `FONT-LICENSE.md`。`skills/technical-diagrams/assets/reference-examples/` 中的参考原图由使用者授权用于本技能展示，其来源与授权范围见各风格目录下的分析文件；Apache License 2.0 不自动覆盖这些原图，如需再分发请单独确认。
