#!/usr/bin/env python3
"""交付前质检：残留标注、示例数据、联系方式、日期格式、页数。

用法：
    python3 scripts/qa_resume.py <文件.docx|.html|.pdf> [--draft] [--max-pages 2] [--no-pages] [--json]

退出码：0 通过；1 有 FAIL；2 用法或读文件失败。
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

BLOCKING = ["【未完成】", "【进行中】", "【待实测】", "【计划学习】"]
DRAFT = ["【待补充】", "【待确认】"]
SAMPLES = ["sample@example.com", "188-0000-0000", "sample-id", "fictional-resume-photo", "示例证件照"]
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE_RE = re.compile(r"(?<!\d)1[3-9]\d[- ]?\d{4}[- ]?\d{4}(?!\d)")
DOT_DATE = re.compile(r"\b(20\d{2})\.(0[1-9]|1[0-2])\b")
DASH_DATE = re.compile(r"\b(20\d{2})-(0?[1-9]|1[0-2])\b")


def strip_html(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?is)<!--.*?-->", " ", raw)
    raw = re.sub(r"(?is)<br\s*/?>", "\n", raw)
    raw = re.sub(r"(?is)</(p|li|div|h\d|tr)>", "\n", raw)
    raw = re.sub(r"(?is)<[^>]+>", " ", raw)
    return html.unescape(raw)


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8", "ignore")
        xml = re.sub(r"(?is)</w:p>", "\n", xml)
        xml = re.sub(r"(?is)</w:tr>", "\n", xml)
        xml = re.sub(r"(?is)<[^>]+>", "", xml)
        return html.unescape(xml)
    if suffix in (".html", ".htm"):
        return strip_html(path.read_text(encoding="utf-8", errors="ignore"))
    if suffix == ".pdf":
        if not shutil.which("pdftotext"):
            raise RuntimeError("缺少 pdftotext，无法读取 PDF 文本")
        out = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True, check=True
        )
        return out.stdout
    raise RuntimeError(f"不支持的格式：{suffix}（支持 .docx/.html/.pdf）")


def count_pages(path: Path, workdir: Path):
    """返回页数；无法判定时返回 None。

    HTML 交给 LibreOffice 转换会走 HTML 导入而非打印 CSS，页数不可信，因此不参与判定，
    由 qa 提示用浏览器打印确认。
    """
    suffix = path.suffix.lower()
    if suffix in (".html", ".htm"):
        return None
    pdf = path
    if suffix != ".pdf":
        soffice = shutil.which("soffice") or shutil.which("libreoffice")
        if not soffice:
            return None
        target = workdir / (path.stem + ".pdf")
        subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(workdir), str(path)],
            capture_output=True, text=True, timeout=120,
        )
        if not target.exists():
            return None
        pdf = target
    if shutil.which("pdfinfo"):
        out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True)
        m = re.search(r"^Pages:\s+(\d+)", out.stdout, re.M)
        if m:
            return int(m.group(1))
    if shutil.which("pdftotext"):
        out = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True)
        if out.returncode == 0:
            return out.stdout.count("\f") + (0 if out.stdout.endswith("\f") else 1)
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--draft", action="store_true", help="目标简历或用户决定保留标注的稿子：各类标注只提示、不算失败")
    ap.add_argument("--max-pages", type=int, default=2)
    ap.add_argument("--no-pages", action="store_true", help="跳过页数检查（无 LibreOffice 时）")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    path = Path(args.file).resolve()
    if not path.exists():
        print(f"找不到文件：{path}")
        return 2
    try:
        text = extract_text(path)
    except Exception as exc:  # noqa: BLE001
        print(f"读取失败：{exc}")
        return 2

    fails, warns = [], []

    for m in BLOCKING:
        if m in text:
            (warns if args.draft else fails).append(f"含未完成类标注 {m}")
    for m in DRAFT:
        if m in text:
            (warns if args.draft else fails).append(f"含未补全标注 {m}")
    for m in SAMPLES:
        if m in text:
            fails.append(f"含模板示例数据 {m}")

    if not EMAIL_RE.search(text) and not PHONE_RE.search(text):
        fails.append("没有检测到邮箱或手机号，联系方式可能缺失")
    if "自我评价" in text:
        warns.append("出现「自我评价」段：03 默认不写套话，确认是否为用户明确要求")

    dot = len(DOT_DATE.findall(text))
    dash = len(DASH_DATE.findall(text))
    if dot and dash:
        warns.append(f"同时出现点分隔（{dot} 处）与横线分隔（{dash} 处）日期，03 要求统一格式")

    pages = None if args.no_pages else count_pages(path, Path(tempfile.mkdtemp()))
    if pages is None:
        warns.append("未能判定页数：HTML 需用浏览器打印确认页数；其他格式请检查 LibreOffice/pdfinfo 是否可用")
    elif pages > args.max_pages:
        fails.append(f"页数 {pages} 超出上限 {args.max_pages}")
    elif pages == 0:
        fails.append("页数为 0，文件可能为空或损坏")

    result = {
        "file": str(path),
        "ok": not fails,
        "pages": pages,
        "fails": fails,
        "warnings": warns,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for w in warns:
            print(f"WARN {w}")
        for f in fails:
            print(f"FAIL {f}")
        page_txt = f"{pages} 页" if pages is not None else "页数未知"
        print(f"{'通过' if not fails else '未通过'}：{page_txt}，{len(fails)} 个失败，{len(warns)} 个警告")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
