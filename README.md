# 简历制作 Skill（resume-maker）

面向中文求职的 Agent Skill：用一份可更新的**事实基线**串起整条求职链路。
结构是**四条产物线 + 两个台账**：

| 层 | 内容 | 产出 |
|---|---|---|
| 方向线 | ① 方向选择（基石）：基于通用简历模板与个人信息，定下方向与岗位、城市、企业、薪资，并给出岗位关键词与 JD 检索技巧 | `方向报告.md`、`求职档案.md`、每个方向的`方向结论.md`与`检索词与城市公司.md` |
| 简历线 | ⓪ 通用简历模板 → ② 方向简历与项目设计 → ③ 按 JD 定制 | `通用简历模板.docx`、方向画像、差距分析、`当前版-<简称>.docx`→`目标版-<简称>.docx`、项目设计方案、投递简历`<城市>-<公司>-<岗位>-<日期>.docx`＋匹配分析 |
| 岗位线 | 按 ① 的检索清单分方向大量收集 JD（检索、MCP、用户截图；目标企业官网与招聘平台），建样本库与投递候选池（① 之后、② 之前） | `JD样本-<轮次或日期>.md`、跨方向结论（写入 `投递/本周投递清单.md` 附录） |
| 面试线 | ④ 面试准备、模拟面试、面后复盘 | `面试准备.md` |
| 事实台账 | 06 主张—证据账本，横跨所有产出 | `career-claim-ledger.json` |
| 投递台账 | ⑤ 投递记录，横跨 ③ 之后所有环节 | `投递记录.md` |

整体顺序：**⓪ 通用简历模板 → ① 方向选择 → 岗位线收集 JD → ② → ③ → ④ → ⑤**。① 是基石：在模板的事实之上定下方向与岗位、城市、企业、薪资，并写出岗位关键词与 JD 检索技巧，后面的 JD 收集、项目设计、方向简历都从它的文档起步。

简历线先建起点，再分两步：**⓪ 通用简历模板 → ② 方向简历（项目设计 → 当前版 → 目标版） → ③ 按具体 JD 定制**。
⓪ 由你提供自己的简历，直接作为或优化后作为`通用简历模板.docx`；框架可沿用你的简历、选素材库母版，或在此基础上继续优化。
之后所有方向简历和 JD 定制稿都从这份模板派生。赶时间可以把简历直接作为模板，确认后进 ③。

岗位线在 ① 与 ② 之间：**方向定了就先分方向大量收集 JD**（联网检索、MCP 与浏览器工具、用户截图；来源是目标城市的目标企业官网和招聘平台）。
这批 JD 一次收集两处使用：② 靠综合它们来归纳方向画像、设计项目、写方向简历；③ 从中挑岗位定制。

适用于校招与社招、任意专业与行业；不绑定特定模型、平台或专有工具，只依赖宿主提供的对话、
文件读写、浏览器/搜索与文档能力。

## 与「简历润色提示词」的区别

- **状态可续**：`求职档案.md` 是唯一状态源，任何环节先读 `## 状态` 再动手，跨会话不会从零开始。
- **事实优先**：公司、职位、学校、时间、技能、成果均来自用户材料或已确认证据；强主张（主导、0→1、核心作者）才建立证据账本。
- **JD 不能反向污染经历**：JD 职责只用于定方向和选岗位，不得改写成已完成经历；无出处的技术栈与数字整段删除，而不是改小一点。
- **标注由用户决定去留**：`【未完成】`、`【进行中】`、`【待实测】`、`【计划学习】` 等标注不会自动消失，也不会被改写成已完成的事实；交付时一次性列出仍带标注的条目。
- **找岗是可复用调研**：一次检索产出能在两周内照着投的候选池（含届别、学历等硬门槛判定），而不是一堆读完就忘的链接。
- **同一份数据出多格式**：`resume-data.json` → HTML / DOCX / PDF / LaTeX 由脚本渲染，避免多格式各写一遍导致事实不一致。
- **脚本可自检**：数据结构校验、交付前质检、全链路 e2e 都有可执行断言，不靠目视。
- **不做外发动作**：不自动填招聘网站、不上传附件、不投递、不发消息。

## 何时使用

| 你的情况 | 会得到 |
|---|---|
| 不知道找什么工作，或想比较方向 | 方向报告与本方向的岗位画像 |
| 方向已定，要一份能长期迭代的方向简历 | 项目设计方案 + `当前版-<简称>.docx`（放进项目）+ `目标版-<简称>.docx`（综合 JD 逐模块优化） |
| 方向定了但手上没有具体 JD，想找一批能投的岗位 | 检索词分档、可投性判定与候选池 |
| 拿到某家公司的具体 JD | 按城市、公司、岗位、日期命名的投递简历 + 逐条匹配分析 |
| 收到面试、想模拟追问 | 面试准备清单与追问预案 |
| 投了几家，想管理进度和复盘 | `投递记录.md` 与转化分析 |

## 安装

把整个目录放进宿主约定的 skills 目录即可，目录名保持 `resume-maker-skill`，
宿主读取 `SKILL.md` 前置元数据中的 `name: resume-maker` 作为入口：

- 个人级：如 `~/.claude/skills/resume-maker-skill/`；
- 项目级：如项目的 `.opencode/skills/`、`.claude/skills/`。

具体路径以你所使用宿主的文档为准。本仓库不包含打包产物（`.skill` 单文件），需要时自行打包。

## 触发方式

- 输入 `/resume-maker` 或 `$resume-maker`；
- 或直接说「使用简历制作 skill」「帮我改简历」「按这个 JD 定制」「帮我找一批能投的岗位」；
- 不确定下一步时，说「使用简历制作」，会从总览开始路由。

## 工作流与产物

| 环节 | 入口 | 主要产出 |
|---|---|---|
| 总览 | [references/00-求职总览.md](references/00-求职总览.md) | 状态盘点、下一步建议 |
| ① 方向选择（基石） | [references/01-方向选择.md](references/01-方向选择.md) | `方向报告.md`、`求职档案.md`、`方向结论.md`、`检索词与城市公司.md` |
| ② 方向简历 | [references/02-方向简历.md](references/02-方向简历.md) | `方向画像.md`、`差距分析.md`、`当前版-<简称>.docx`、`目标版-<简称>.docx`、`项目设计方案.md` |
| 岗位线 | [references/08-JD检索与候选池.md](references/08-JD检索与候选池.md) | `JD样本-<日期>.md`、跨方向缺口 ROI |
| ③ JD 定制 | [references/03-JD定制.md](references/03-JD定制.md) | `<城市>-<公司>-<岗位>-<日期>.docx`、`匹配分析.md` |
| ④ 面试准备 | [references/04-面试准备.md](references/04-面试准备.md) | `面试准备.md` |
| ⑤ 投递记录 | [references/05-投递记录.md](references/05-投递记录.md) | `投递记录.md`、`本周投递清单.md` |
| 证据账本 | [references/06-证据账本.md](references/06-证据账本.md) | `career-claim-ledger.json` |
| 成稿与质检 | [references/07-简历输出与质检.md](references/07-简历输出与质检.md) | Word/HTML/PDF/LaTeX 与验收记录（含反向污染审计） |

岗位线、② 与 ③ 的分工：**岗位线按方向大量收集 JD；② 综合这批 JD 定目标、规划项目；③ 按具体 JD 定制**。

### 用户目录契约

```
求职/
├── 求职档案.md                      # 唯一状态源：背景、偏好、状态、文件清单、更新记录
├── 通用简历模板.docx                 # ⓪ 唯一底本：用户简历直接用或优化而来，含【岗位】占位符
├── 通用简历模板.json                 # 可选：选素材库框架时的结构化事实源
├── 历史/                            # 通用简历模板的旧版
├── 方向报告.md                      # ① 全部候选方向的调研与对比
├── career-claim-ledger.json         # 可选：主张—证据账本
├── 现状盘点与收敛建议.md             # 可选：多版本诊断
├── 投递/                            # 全局台账
│   ├── 投递记录.md                  # ⑤ 每家公司的投递、进展与结果
│   └── 本周投递清单.md              # 待投队列；末尾附录承载跨方向结论
└── 方向/
    └── <方向名>/                    # 一个方向一个目录；一次只推进一个当前方向
        ├── 方向结论.md              # ① 基石：岗位、典型要求、城市、企业、薪资、优势短板
        ├── 检索词与城市公司.md      # ① 基石：岗位词与技术词分档、查询组合、企业池、检索技巧
        ├── JD样本-<轮次或日期>.md   # 岗位线：收集概况＋全部 JD＋高频要求统计，多轮追加
        ├── JD截图/                  # 用户发来的 JD 截图原图
        ├── 方向画像.md              # ② 由 JD 样本归纳
        ├── 差距分析.md              # ② 含项目候选与选择记录
        ├── 项目/
        │   └── <项目名>/
        │       ├── 项目设计方案.md  # ② 用户选定后才生成
        │       └── …               # 用户做项目时的证据：代码链接、测试记录、截图
        ├── 简历/
        │   ├── 当前版-<简称>.docx   # ② 模板副本＋【岗位】＋项目增添或替换
        │   ├── 目标版-<简称>.docx   # ② 在当前版上综合 JD 逐模块优化，行动目标
        │   ├── 目标版修改说明.md    # 可选：修改说明、高频要求覆盖表、行动清单
        │   └── 历史/                # 当前版与目标版的旧版
        └── 投递/
            └── <公司>-<岗位>/       # 一家公司一个岗位一个目录
                ├── JD.md            # ③ 用户贴出的 JD 原文
                ├── 匹配分析.md      # ③ 匹配度、改动说明、沟通材料
                ├── <城市>-<公司>-<岗位>-<日期>.docx   # ③ 投递简历，如 上海-某某科技-推理部署实习-20261115.docx
                └── 面试准备.md      # ④ 含训练记录
```

两条容易混的规则：**同名两层**——顶层 `投递/` 只放全局台账，公司级定制稿在 `方向/<方向名>/投递/` 下；
**项目挂主方向**——一个项目可支撑多个方向，但方案与证据只在主方向存一份。方向简称（如 `d1 AI推理部署`）在档案里登记一次，简历文件名必须带它。

## 仓库结构

```
SKILL.md                      # 技能入口：路由表、状态契约与共用规则
references/                   # 九个文件（00–08），按环节分别读取
assets/
  asu-resume/template.html    # ASu 单栏高密度模板（母版）
  templates-html/             # 4 个壳文件，每个对应一种版式（对照见 assets/模板索引.md）
  latex-resume/               # 3 套 LaTeX 母版（ASu / 紧凑 / 学术）
  frame/                      # 共享 CSS、工具栏与内联编辑器
  icons/ logos/               # 图标与公司 Logo
  resume-data.schema.json     # resume-data.json 的 JSON Schema
  resume-data-template.json   # 数据结构模板（全为虚构示例）
  career-claim-ledger-template.json
  个人信息收集表.md            # 没有简历时，一次性问全所需信息
  求职档案模板.md              # 求职档案（唯一状态源）模板
  模板索引.md                  # 4 个壳与可叠加版式类的对照
  asu-resume-template.html     # ASu 构建自检基准（--check 使用）
  application-tracker.html     # 投递记录可视化面板
fixtures/                     # 自检样例：example 正例、draft 负例
scripts/                      # 构建、导出、转换、质检与自检脚本
agents/                       # 宿主适配清单（doubao / openai）
```

## 数据驱动管线

```
resume-data.json ──build-html.mjs─────────► HTML（自包含，可编辑）
                 ├─build-docx.py──────────► DOCX（默认交付）
                 ├─export-resume-pdf.mjs──► PDF
                 └─build-latex-resume.mjs─► .tex（可选）
```

通用简历模板沿用你的简历框架时，直接在模板副本上改、保留原版式，不走这条管线；
模板选素材库框架时，用 `通用简历模板.json`（`resume-data.json` 格式）作为唯一事实源，派生稿由它渲染。

| 脚本 | 用途 | 依赖 |
|---|---|---|
| `scripts/build-html.mjs` | `resume-data.json` → 自包含 HTML（按 `--variant` 选壳） | Node 18+，零 npm |
| `scripts/build-docx.py` | `resume-data.json` → 单栏 A4 DOCX | Python + `python-docx` |
| `scripts/build-asu-resume.mjs` | ASu 模板构建；`--check` 校验自检基准 | Node 18+ |
| `scripts/inline-template.mjs` | 壳 HTML → 自包含 HTML；`--all` 批量构建全部壳 | Node 18+ |
| `scripts/export-resume-pdf.mjs` | HTML → PDF（CDP，纸张以 CSS `@page` 为准） | Node 22+，本机 Edge/Chrome |
| `scripts/build-latex-resume.mjs` | `resume-data.json` → `.tex` | Node 18+；不需要 LaTeX 编译器 |
| `scripts/html-to-docx.ps1` | 自包含 HTML → DOCX | Windows + 桌面版 Word |
| `scripts/validate_resume_data.py` | 结构、枚举、日期顺序与示例数据校验 | Python + `jsonschema` |
| `scripts/qa_resume.py` | 交付前质检：示例数据、标注、联系方式、页数 | Python；页数需 LibreOffice 或 `pdfinfo` |
| `scripts/validate_claim_ledger.py` | 证据账本校验 | Python 标准库 |
| `scripts/test-application-tracker.mjs` | 投递面板脚本单测（`node:test`） | Node |
| `scripts/e2e-check.sh` | 全链路自检（维护者改完 `references/`、`assets/`、`scripts/` 后跑） | bash + node + python3 + `python-docx` + `jsonschema` |

常用命令：

```bash
node scripts/build-html.mjs fixtures/resume-data.example.json out/resume.html --variant black
python3 scripts/build-docx.py fixtures/resume-data.example.json out/resume.docx
python3 scripts/validate_resume_data.py fixtures/resume-data.example.json
python3 scripts/qa_resume.py out/resume.docx --max-pages 2
node scripts/export-resume-pdf.mjs out/resume.html --out out/resume.pdf
bash scripts/e2e-check.sh
```

`fixtures/resume-data.draft.json` 是负例（含标注、示例数据与日期倒序），用来确认校验脚本真的会报错。

## 模板

- `assets/templates-html/` 4 个壳文件：`variant-black`（默认、ATS、国企）、`variant-blue-line`（校招）、`variant-centered`（经历少、设计内容岗）、`variant-english`（外企、英文简历）；
- `assets/frame/base.css` 另有 sidebar、two-column、timeline、cards 等 16 个可叠加版式类，用户明确要求时在 `<body>` 追加即可；
- `assets/asu-resume/template.html` 是独立的高密度单栏模板，适合项目与实习很多的技术岗；
- Word 默认由 `build-docx.py` 生成固定单栏样式，**不套用 HTML 模板**；HTML 模板只用于用户明确要 HTML 或设计型 PDF 时。

## 设计原则

1. **不编造**：公司、职位、学校、时间、职责、技能、项目、证书、论文、指标、开源贡献都不得虚构。
2. **反向污染零容忍**：JD 职责不等于个人经历；技术栈与量化数字必须能指向一个与 JD 无关的真实出处，指向不了就整段删。
3. **区分贡献**：团队成果、个人动作、AI 辅助、平台能力分别表述，不把「参与」写成「主导」。
4. **硬门槛不做推断**：届别、学历、城市字面不符即判不可投，不写「应该能通融」。
5. **状态单一来源**：阶段与材料状态只写在 `求职档案.md` 的 `## 状态`，投递明细只写在 `投递/投递记录.md`。
6. **一次只走一个方向**：先让用户选定一个当前方向，基石文档、JD 收集、项目设计、方向简历都只为它做；其余记为备选，当前方向交付并经确认后再开始下一个。
7. **不做外发动作**：不自动填写招聘网站、不上传附件、不投递、不发消息；需要时另行确认目标与范围。

## 虚假数据声明

`assets/` 与 `fixtures/` 中的姓名、学校、公司、电话、邮箱、指标与照片均为**虚构示例**
（如「林知远」、`sample@example.com`、`188-0000-0000`），只用于演示结构与版式。
`qa_resume.py` 会拦截 `sample@example.com`、`188-0000-0000`、`fictional-resume-photo` 等残留标识。
真实信息只写入用户指定的输出目录，不回写模板。

## 许可

本项目以 [MIT License](LICENSE) 发布。其中改编自
[ASu-skills](https://github.com/Hisn00w/ASu-skills) 的模板、脚本与资源同样遵循 MIT，
版权归 Hisn00w 所有，详见 [THIRD_PARTY_LICENSES.txt](THIRD_PARTY_LICENSES.txt)。
