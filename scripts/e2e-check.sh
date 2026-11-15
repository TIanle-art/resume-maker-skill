#!/usr/bin/env bash
# 全链路自检。维护者改动 references/、assets/ 或 scripts/ 后运行，确认没有回归。
#
# 用法：bash scripts/e2e-check.sh
# 退出码：0 全部符合预期；1 有非预期结果。

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

PASS=0
FAIL=0
ok() { echo "PASS $1"; PASS=$((PASS + 1)); }
bad() { echo "FAIL $1"; FAIL=$((FAIL + 1)); }

echo "== 1. ASu 模板一致性 =="
if node scripts/build-asu-resume.mjs --check; then ok "ASu 基线一致"; else bad "ASu 基线不一致"; fi

echo "== 2. 全部壳模板可构建 =="
if node scripts/inline-template.mjs --all "$WORK/tpl" >/dev/null 2>&1; then
  COUNT=$(find "$WORK/tpl" -maxdepth 1 -name '*.html' | wc -l)
  if [ "$COUNT" -eq 4 ]; then ok "4 个壳构建成功"; else bad "壳数量为 $COUNT，期望 4"; fi
  if grep -rq '自我评价' "$WORK"/tpl 2>/dev/null; then bad "构建产物仍含自我评价段"; else ok "产物无自我评价段"; fi
  # 壳文件演示数据是有意保留的（用于版式密度），交付阶段的拦截由 qa_resume.py 负责（见第 7 步）
  if grep -rq 'resume-toolbar' "$WORK"/tpl 2>/dev/null && ! grep -rq 'design-preview' "$WORK"/tpl 2>/dev/null; then
    ok "产物已内联工具栏且移除预览类"
  else
    bad "产物内联不完整"
  fi
else
  bad "壳模板构建失败"
fi

echo "== 3. 事实数据校验（正例应通过）=="
if python3 scripts/validate_resume_data.py fixtures/resume-data.example.json >/dev/null; then
  ok "正例通过结构校验"
else
  bad "正例未通过结构校验"
fi

echo "== 4. 事实数据校验（负例应失败）=="
if python3 scripts/validate_resume_data.py fixtures/resume-data.draft.json >"$WORK/neg1.txt" 2>&1; then
  bad "负例未报错（应判失败）"
else
  # 至少要命中标注、示例数据、日期倒序三类问题
  HITS=0
  grep -q '【待补充】' "$WORK/neg1.txt" && HITS=$((HITS + 1))
  grep -q 'sample@example.com' "$WORK/neg1.txt" && HITS=$((HITS + 1))
  grep -q '顺序' "$WORK/neg1.txt" && HITS=$((HITS + 1))
  if [ "$HITS" -ge 3 ]; then ok "负例命中标注/示例/倒序 3 类问题"; else bad "负例只命中 $HITS 类问题，期望 ≥3"; fi
fi

echo "== 5. JSON -> HTML =="
if node scripts/build-html.mjs fixtures/resume-data.example.json "$WORK/resume.html" >/dev/null 2>&1; then
  if grep -q 'resume-toolbar' "$WORK/resume.html" && ! grep -q 'frame/base.css' "$WORK/resume.html"; then
    ok "HTML 自包含（已内联 CSS 与工具栏）"
  else
    bad "HTML 未正确内联"
  fi
else
  bad "HTML 生成失败"
fi

echo "== 6. JSON -> DOCX 并质检 =="
if python3 scripts/build-docx.py fixtures/resume-data.example.json "$WORK/resume.docx" >/dev/null; then
  if python3 scripts/qa_resume.py "$WORK/resume.docx" --max-pages 2 >"$WORK/qa1.txt" 2>&1; then
    ok "DOCX 生成且质检通过（$(grep -o '[0-9] 页' "$WORK/qa1.txt" | head -1)）"
  else
    bad "DOCX 质检未通过：$(tail -2 "$WORK/qa1.txt" | tr '\n' ' ')"
  fi
else
  bad "DOCX 生成失败"
fi

echo "== 7. 质检应拦截含标注的稿子 =="
if node scripts/build-html.mjs --shell assets/templates-html/variant-black-后端分布式.html \
     fixtures/resume-data.draft.json "$WORK/draft.html" >/dev/null 2>&1; then
  if python3 scripts/qa_resume.py "$WORK/draft.html" >"$WORK/qa2.txt" 2>&1; then
    bad "负例稿未被拦截"
  else
    ok "负例稿被拦截（$(grep -c '^FAIL' "$WORK/qa2.txt") 项失败）"
  fi
else
  bad "负例稿生成失败"
fi

echo "== 8. HTML -> PDF（环境有 Chrome 时）=="
if node scripts/export-resume-pdf.mjs "$WORK/resume.html" --out "$WORK/resume.pdf" >/dev/null 2>&1 \
   && [ -s "$WORK/resume.pdf" ]; then
  ok "PDF 导出成功"
else
  echo "SKIP 未导出 PDF（缺 Chrome/Chromium 或脚本不可用）"
fi

echo "== 9. JD 样本检查脚本 =="
python3 - "$WORK" <<'PY'
import sys, os
w = sys.argv[1]
def gen(n, cos, ceil, d):
    out = ["# JD 样本：自检\n\n## 第 1 轮\n"]
    for i in range(n):
        layer = "天花板" if i < ceil else "可投"
        out.append(f"### J{i+1:03d} 公司{i % cos}｜岗位{i}\n\n- 状态：有效\n- 分层：{layer}\n- 城市：上海\n"
                   f"- 来源：官网｜材料{i}\n- 抓取日期：{d}\n- 发布日期：{d}\n- 核心职责：做事\n- 核心要求：会做事\n")
    return "\n".join(out)
for name, a in {"ok": (22, 11, 6, "2026-11-10"), "few": (8, 5, 2, "2026-11-10"), "old": (22, 11, 6, "2026-07-01"), "niche": (11, 6, 3, "2026-11-10")}.items():
    open(os.path.join(w, f"jd-{name}.md"), "w", encoding="utf-8").write(gen(*a))
PY
JD="python3 scripts/check_jd_samples.py --today 2026-11-15"
# 脚本在非“可直接用”时退出码为 1，这里只看输出文字
OUT_OK="$($JD "$WORK/jd-ok.md" || true)"; OUT_FEW="$($JD "$WORK/jd-few.md" || true)"; OUT_OLD="$($JD "$WORK/jd-old.md" || true)"
case "$OUT_OK" in *可直接用*) ok "达标样本判为可直接用" ;; *) bad "达标样本未判为可直接用" ;; esac
case "$OUT_FEW" in *需要补收*) ok "数量不足判为需要补收" ;; *) bad "数量不足未被拦截" ;; esac
OUT_NICHE="$($JD --niche "$WORK/jd-niche.md" || true)"
case "$OUT_NICHE" in *可直接用*小众*) ok "小众档达标样本判为可直接用" ;; *) bad "小众档判定不符合预期" ;; esac
case "$OUT_OLD" in *需要重收*) ok "过旧样本判为需要重收" ;; *) bad "过旧样本未被拦截" ;; esac

# 两层结构：方向目录下 JD样本.md（索引）＋ JD原文/（条目）
mkdir -p "$WORK/dir/JD原文" && cp "$WORK/jd-ok.md" "$WORK/dir/JD原文/第1轮-2026-11-10.md"
printf '# JD 样本\n\n- 方向规模：常规\n\n| 编号 | 公司 |\n|---|---|\n| J001 | 公司0 |\n' > "$WORK/dir/JD样本.md"
OUT_DIR="$($JD "$WORK/dir" || true)"
case "$OUT_DIR" in *可直接用*索引表缺*) ok "方向目录两层结构可读，并提示索引缺条目" ;; *) bad "方向目录两层结构检查不符合预期" ;; esac

echo "== 10. 建目录脚本 =="
if python3 scripts/init_workspace.py "$WORK/求职" --direction 自检方向 --company 某司-某岗 >/dev/null \
   && [ -f "$WORK/求职/求职档案.md" ] && [ -d "$WORK/求职/方向/自检方向/JD截图" ] && [ -d "$WORK/求职/方向/自检方向/JD原文" ] && [ -f "$WORK/求职/方向/自检方向/JD样本.md" ] \
   && [ -f "$WORK/求职/方向/自检方向/投递/某司-某岗/匹配分析.md" ]; then
  ok "目录按契约建立"
else
  bad "目录建立不符合契约"
fi
echo "改过" >> "$WORK/求职/求职档案.md"
python3 scripts/init_workspace.py "$WORK/求职" >/dev/null
if tail -1 "$WORK/求职/求职档案.md" | grep -q '改过'; then ok "重复运行不覆盖已有文件"; else bad "重复运行覆盖了已有文件"; fi

echo
echo "结果：$PASS 项通过，$FAIL 项失败"
[ "$FAIL" -eq 0 ]
