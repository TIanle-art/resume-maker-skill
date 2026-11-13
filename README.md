# 简历制作 Skill（resume-maker）

面向中文求职的 Agent Skill：用一份可持续更新的事实基线，把求职串成五个阶段——
**方向选择 → 方向简历 → JD 定制 → 面试准备 → 投递记录**。

适用于校招与社招、任意专业与行业；不绑定特定模型、平台或专有工具，只依赖宿主提供的对话、
文件读写、浏览器/搜索和文档能力。

## 为什么不是一个「简历润色提示词」

- **阶段化推进**：简历不是一次写完，而是随方向、JD、面试反馈反复迭代；每个阶段有独立入口和验收标准。
- **事实基线优先**：公司、职位、时间、技术栈、成果均需来自用户材料或已确认证据；强主张（主导、0→1、核心作者）要求可核验的证据账本。
- **未完成内容强制标注**：`【未完成】`、`【进行中】`、`【待实测】`、`【计划学习】` 一律不得进入正式投递版。
- **默认交付可编辑 Word**，可附加自包含 HTML（浏览器内可编辑）、PDF、LaTeX；三者必须来自同一份已核实事实。
- **脚本零 npm 依赖**：构建、内联、PDF 导出只用 Node 内置模块与本机浏览器。

## 何时使用

| 你的情况 | 会得到 |
|---|---|
| 不知道找什么工作、想比较方向 | 方向报告与本方向的岗位画像 |
| 已确定方向，要一份能长期迭代的底稿 | 最终目标简历 + 项目设计方案 |
| 拿到某家公司的具体 JD | 定制简历 + 逐条匹配分析 |
| 收到面试、想模拟追问 | 面试准备清单与追问预案 |
| 投了几家、想管理进度和复盘 | 投递记录与转化分析 |

## 安装

把整个目录放进宿主约定的 skills 目录即可，目录名保持 `resume-maker-skill`，
宿主读取 `SKILL.md` 前置元数据中的 `name: resume-maker` 作为入口：

- 个人级：如 `~/.claude/skills/resume-maker-skill/`；
- 项目级：如项目的 `.opencode/skills/`、`.claude/skills/`。

具体路径以你所使用宿主的文档为准。本仓库不包含打包产物（`.skill` 单文件），需要时自行打包。

## 触发方式

- 输入 `/resume-maker` 或 `$resume-maker`；
- 或直接说「使用简历制作 skill」「帮我改简历」「按这个 JD 定制」；
- 不确定下一步时，说「使用简历制作」，会从总览开始路由。

## 阶段与产出

| 阶段 | 入口 | 主要产出 |
|---|---|---|
| 总览 | [references/00-求职总览.md](references/00-求职总览.md) | 现状盘点、下一步建议 |
| ① 方向选择 | [references/01-方向选择.md](references/01-方向选择.md) | `方向报告.md`、`方向画像-〈方向〉.md` |
| ② 方向简历 | [references/02-方向简历.md](references/02-方向简历.md) | `最终目标简历-〈方向〉.docx`、`项目设计方案-〈项目名〉.md` |
| ③ JD 定制 | [references/03-JD定制.md](references/03-JD定制.md) | `定制简历-〈公司〉-〈岗位〉.docx`、`匹配分析-〈公司〉-〈岗位〉.md` |
| ④ 面试准备 | [references/04-面试准备.md](references/04-面试准备.md) | `面试准备-〈公司〉-〈岗位〉.md` |
| ⑤ 投递记录 | [references/05-投递记录.md](references/05-投递记录.md) | `投递记录.md` |
| 证据账本 | [references/06-证据账本.md](references/06-证据账本.md) | `career-claim-ledger.json` |
| 成稿质检 | [references/07-简历输出与质检.md](references/07-简历输出与质检.md) | Word/HTML/PDF/LaTeX 成稿与验收记录 |

阶段②与③的分工：**②产可复用底稿，③只做单岗位定制**。③不创建新方向简历，也不把规划中的项目写成已完成。

## 目录结构

```
SKILL.md                      # 技能入口：路由表与共用工作规则
references/                   # 八个阶段的执行规范（按需读取，不一次性全读）
assets/
  asu-resume/template.html    # 默认 ASu 单栏高密度模板（母版）
  templates-html/             # 18 套 HTML 壳模板
  latex-resume/               # 3 套 LaTeX 母版（ASu / 紧凑 / 学术）
  frame/                      # 共享 CSS、工具栏与内联编辑器
  icons/ logos/               # 图标与公司 Logo
  resume-data-template.json   # 简历数据结构（全为虚构示例）
  career-claim-ledger-template.json
  application-tracker.html    # 投递记录可视化面板
scripts/                      # 构建、导出、转换与校验脚本
agents/                       # 宿主适配清单（doubao / openai）
THIRD_PARTY_LICENSES.txt      # 第三方来源与许可证
```

## 脚本

所有脚本都以相对路径定位本目录资源，输出必须写到用户目录，不写回 `assets/`。

| 脚本 | 用法 | 作用 |
|---|---|---|
| `scripts/build-asu-resume.mjs` | `node scripts/build-asu-resume.mjs <内容壳.html> <输出.html>` | 按默认 ASu 模板内联为自包含 HTML |
| `scripts/inline-template.mjs` | `node scripts/inline-template.mjs <壳.html> [输出.html]`<br>`node scripts/inline-template.mjs --all <输出目录>` | 其他 HTML 模板内联；`--all` 批量验证 18 套壳模板 |
| `scripts/export-resume-pdf.mjs` | `node scripts/export-resume-pdf.mjs <html> --out <pdf> [--browser <路径>]` | 用本机 Edge/Chrome 无头导出 PDF，纸张以 CSS `@page` 为准 |
| `scripts/build-latex-resume.mjs` | `node scripts/build-latex-resume.mjs <数据.json> <输出.tex> [母版.tex]` | 生成 `.tex` 源文件（不编译，交给 Overleaf/XeLaTeX） |
| `scripts/html-to-docx.ps1` | `powershell -NoProfile -File scripts/html-to-docx.ps1 <html> <docx>` | Windows + 桌面版 Word 下把自包含 HTML 转 DOCX |
| `scripts/validate_claim_ledger.py` | `python scripts/validate_claim_ledger.py <ledger.json> [--json]`<br>（Windows 无 `python` 时用 `py -3`） | 校验证据账本的确定性问题 |

## 运行时依赖

| 能力 | 需要 | 说明 |
|---|---|---|
| HTML 构建 / 内联 | Node.js | 无 npm 依赖 |
| PDF 导出 | Node.js + 本机 Edge/Chromium/Chrome | 走 CDP，不读取浏览器 Cookie 或数据库 |
| Word 转换 | Windows + 桌面版 Microsoft Word | 缺少时可用宿主 DOCX 能力或改为交付 HTML/Markdown |
| 证据账本校验 | Python 3.8+ | 仅用到标准库 |
| LaTeX | 不需要编译器 | 只产出 `.tex`，由 Overleaf 或本地 XeLaTeX 编译 |

缺少某项能力时，技能会降级交付并明确列出未完成的验收项，不会声称「已全面检查」。

## 设计原则

1. **不编造**：公司、职位、学校、时间、职责、技能、项目、证书、论文、指标、开源贡献都不得虚构。
2. **区分贡献**：团队成果、个人动作、AI 辅助、平台能力分别表述，不把「参与」写成「主导」。
3. **标注即阻断**：未完成、未实测、计划学习的内容带标注，正式投递前必须清除。
4. **一次只做一个方向**：多方向排队，当前方向交付并经确认后再开始下一个。
5. **不做外发动作**：不自动填写招聘网站、不上传附件、不投递、不发消息；需要时另行确认目标与范围。

## 虚假数据声明

`assets/` 中的人名、学校、电话、邮箱、公司、项目与照片均为**虚构示例**（如「林知远」、
`188-0000-0000`、`sample@example.com`），只用于演示结构与版式。正式使用前必须全部替换为用户真实信息，
且真实信息只写入用户指定的输出目录，不回写模板。

## 许可

本项目以 [MIT License](LICENSE) 发布。其中改编自
[ASu-skills](https://github.com/Hisn00w/ASu-skills) 的模板、脚本与资源同样遵循 MIT，
版权归 Hisn00w 所有，详见 [THIRD_PARTY_LICENSES.txt](THIRD_PARTY_LICENSES.txt)。
