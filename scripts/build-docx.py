#!/usr/bin/env python3
"""resume-data.json -> 单栏 A4 Word 简历。

用法：
    python3 scripts/build-docx.py <resume-data.json> <输出.docx> [--variant <仅记录用>]

默认样式遵循 references/07-简历输出与质检.md §2：A4、上下 1.5cm/左右 1.8cm、
姓名 18pt 加粗居中、小标题 12pt 加粗带下划线、正文 10.5pt、行距 1.2、时间倒序。
依赖 python-docx（无其他第三方依赖）。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt, RGBColor
except ImportError:
    print("缺少 python-docx，请先安装：pip install python-docx")
    sys.exit(2)

EA_FONT = "Microsoft YaHei"
LATIN_FONT = "Calibri"
ACCENT = RGBColor(0x2C, 0x5B, 0x95)
MUTED = RGBColor(0x5E, 0x67, 0x73)


def style_run(run, size=None, bold=None, color=None, font_ea=EA_FONT, font_latin=LATIN_FONT):
    run.font.name = font_latin
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), font_ea)
    rfonts.set(qn("w:ascii"), font_latin)
    rfonts.set(qn("w:hAnsi"), font_latin)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color
    return run


def para(doc, *, space_before=0, space_after=0, line=1.2, align=None, indent=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = line
    if align is not None:
        p.alignment = align
    if indent is not None:
        pf.left_indent = Cm(indent)
    return p


def bottom_border(p, color="315F98", sz="6"):
    ppr = p._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), sz)
    bottom.set(qn("w:space"), "3")
    bottom.set(qn("w:color"), color)
    pbdr.append(bottom)
    ppr.append(pbdr)


def section_title(doc, text, first=False):
    p = para(doc, space_before=0 if first else 9, space_after=3, line=1.1)
    style_run(p.add_run(text), size=12, bold=True, color=ACCENT)
    bottom_border(p)
    return p


def bullet_items(doc, bullets):
    for b in bullets or []:
        text = b if isinstance(b, str) else f"{b.get('label', '')}{b.get('text', '')}"
        if not text.strip():
            continue
        p = para(doc, space_before=1, space_after=1, line=1.2, indent=0.55)
        p.paragraph_format.first_line_indent = Cm(-0.55)
        style_run(p.add_run("• "), size=10.5)
        style_run(p.add_run(text.strip()), size=10.5)


def entry(doc, dates, left, right, bullets=None):
    """首行：左侧单位/项目 + 职位，右侧时间（07 §2 规定）。"""
    p = para(doc, space_before=4, space_after=0, line=1.15)
    p.paragraph_format.tab_stops.add_tab_stop(Cm(17.2), WD_TAB_ALIGNMENT.RIGHT)
    style_run(p.add_run(left), size=10.5, bold=True)
    if right:
        style_run(p.add_run(" · " + right), size=10.5)
    p.add_run("\t")
    style_run(p.add_run(dates or ""), size=10, bold=True, color=MUTED)
    bullet_items(doc, bullets)


def section_lines(doc, title, lines, first=False):
    if not lines:
        return
    section_title(doc, title, first=first)
    bullet_items(doc, lines)


def build(data, out_path):
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.top_margin = sec.bottom_margin = Cm(1.5)
    sec.left_margin = sec.right_margin = Cm(1.8)

    normal = doc.styles["Normal"]
    normal.font.name = LATIN_FONT
    normal.font.size = Pt(10.5)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), EA_FONT)

    p = data.get("profile", {})
    photo = p.get("photo")
    photo_path = None
    if photo:
        cand = (out_path.parent / photo).resolve()
        if cand.exists():
            photo_path = cand
        else:
            print(f"提示：照片文件不存在，已跳过（{photo}）")

    if photo_path:
        tbl = doc.add_table(rows=1, cols=2)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False
        tbl.columns[0].width = Cm(13.6)
        tbl.columns[1].width = Cm(3.8)
        left_cell = tbl.cell(0, 0)
        right_cell = tbl.cell(0, 1)
        name_p = left_cell.paragraphs[0]
    else:
        left_cell = None
        name_p = para(doc, space_before=0, space_after=2, line=1.1, align=WD_ALIGN_PARAGRAPH.CENTER)

    name_p.alignment = WD_ALIGN_PARAGRAPH.CENTER if not photo_path else WD_ALIGN_PARAGRAPH.LEFT
    style_run(name_p.add_run(p.get("name", "")), size=18, bold=True)

    contacts = [x for x in (p.get("city"), p.get("phone"), p.get("email"), p.get("wechat_or_portfolio"), p.get("language_cert")) if x]
    role = p.get("target_role", "")

    def add_role_and_contacts(paragraph_fn):
        rp = paragraph_fn()
        style_run(rp.add_run(role), size=11, bold=True, color=ACCENT)
        cp = paragraph_fn()
        style_run(cp.add_run(" | ".join(contacts)), size=9.5, color=MUTED)

    if photo_path:
        def left_para():
            pr = left_cell.add_paragraph()
            pr.paragraph_format.space_before = Pt(0)
            pr.paragraph_format.space_after = Pt(0)
            pr.paragraph_format.line_spacing = 1.1
            return pr
        add_role_and_contacts(left_para)
        run = right_cell.paragraphs[0].add_run()
        right_cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run.add_picture(str(photo_path), width=Cm(2.6))
    else:
        def center_para():
            pr = para(doc, space_before=0, space_after=1, line=1.1, align=WD_ALIGN_PARAGRAPH.CENTER)
            return pr
        add_role_and_contacts(center_para)

    if data.get("summary"):
        section_title(doc, "个人简介")
        sp = para(doc, space_after=2)
        style_run(sp.add_run(data["summary"]), size=10.5)

    edu = data.get("education") or []
    exp = data.get("experience") or []
    proj = data.get("projects") or []
    campus_first = not exp

    def add_education(first=False):
        if not edu:
            return
        section_title(doc, "教育背景", first=first)
        for e in edu:
            entry(doc, e.get("dates"), e.get("school", ""), e.get("major_degree", ""), e.get("bullets"))

    def add_experience():
        if not exp:
            return
        section_title(doc, "实习与工作经历")
        for e in exp:
            entry(doc, e.get("dates"), e.get("organization", ""), e.get("role", ""), e.get("bullets"))

    def add_projects():
        if not proj:
            return
        section_title(doc, "项目经历")
        for e in proj:
            entry(doc, e.get("dates"), e.get("name", ""), e.get("role", ""), e.get("bullets"))

    if campus_first:
        add_education()
        add_experience()
        add_projects()
    else:
        add_experience()
        add_projects()
        add_education()

    if data.get("skills"):
        section_title(doc, "技能证书")
        bullet_items(doc, data["skills"])
    if data.get("awards"):
        section_title(doc, "荣誉与奖项")
        bullet_items(doc, data["awards"])
    for extra in data.get("extra_sections") or []:
        section_title(doc, extra.get("title", ""))
        bullet_items(doc, extra.get("bullets"))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))
    print(f"已生成 {out_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("out")
    ap.add_argument("--variant", help="仅记录用；DOCX 不套用 HTML 变体样式")
    args = ap.parse_args()

    data_path = Path(args.data).resolve()
    if not data_path.exists():
        print(f"找不到文件：{data_path}")
        return 2
    try:
        data = json.loads(data_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"JSON 解析失败：{exc}")
        return 2
    if not (data.get("profile") or {}).get("name"):
        print("缺少 profile.name")
        return 2
    build(data, Path(args.out).resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
