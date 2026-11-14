#!/usr/bin/env python3
"""resume-data.json 的结构与一致性校验。

用法：
    python3 scripts/validate_resume_data.py <resume-data.json> [--allow-draft] [--json]

做三件事：
1. 按 assets/resume-data.schema.json 校验字段、类型、枚举、必填；
2. 语义检查：时间倒序、日期格式统一、投递版不得含未完成标注、不得含示例数据；
3. 输出可定位的失败项，退出码 1 表示不可交付。

只校验结构与确定性矛盾，不判断经历是否真实，也不联网核查。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE.parent / "assets" / "resume-data.schema.json"

BLOCKING_MARKERS = ["【未完成】", "【进行中】", "【待实测】", "【计划学习】"]
DRAFT_MARKERS = ["【待补充】", "【待确认】"]
SAMPLE_MARKERS = ["sample@example.com", "188-0000-0000", "sample-id", "fictional-resume-photo"]
DATE_RE = re.compile(r"^(\d{4})\.(\d{2})(?:\s*[-–]\s*(\d{4}\.\d{2}|至今|Present))?$")
BAD_DASH_DATE = re.compile(r"\b\d{4}-\d{1,2}\b")


def walk_strings(node, path="$"):
    """产出 (路径, 字符串) 对，用于全文标记扫描。"""
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk_strings(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_strings(v, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


def check_schema(data, errors):
    try:
        import jsonschema
    except ImportError:
        errors.append("环境缺少 jsonschema，无法做结构校验（pip install jsonschema）；已跳过该步")
        return
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft7Validator(schema)
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        loc = ".".join(str(p) for p in err.path) or "<root>"
        errors.append(f"[结构] {loc}: {err.message}")


def parse_start(dates: str):
    m = DATE_RE.match(dates or "")
    if not m:
        return None
    return int(m.group(1)) * 12 + int(m.group(2))


def check_order(section, items, errors):
    starts = []
    for idx, item in enumerate(items or []):
        s = parse_start(item.get("dates", ""))
        if s is None:
            errors.append(f"[日期] {section}[{idx}].dates 格式不是 YYYY.MM 或 YYYY.MM–YYYY.MM：{item.get('dates')!r}")
        else:
            starts.append((idx, s, item.get("dates")))
    for (i1, s1, d1), (i2, s2, d2) in zip(starts, starts[1:]):
        if s2 > s1:
            errors.append(f"[顺序] {section} 应从新到旧排列：第 {i2} 项（{d2}）比第 {i1} 项（{d1}）更新")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--allow-draft", action="store_true", help="允许【待补充】【待确认】等草稿标注")
    ap.add_argument("--json", action="store_true", help="输出机器可读结果")
    args = ap.parse_args()

    path = Path(args.data)
    if not path.exists():
        print(f"找不到文件：{path}")
        return 2
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"JSON 解析失败：{exc}")
        return 2

    errors: list[str] = []
    warnings: list[str] = []

    check_schema(data, errors)

    for section in ("education", "experience", "projects"):
        if isinstance(data.get(section), list):
            check_order(section, data[section], errors)

    deliverable = bool((data.get("meta") or {}).get("is_deliverable"))
    for loc, text in walk_strings(data):
        for m in BLOCKING_MARKERS:
            if m in text:
                errors.append(f"[标注] {loc} 含投递版禁止的标记 {m}")
        for m in DRAFT_MARKERS:
            if m in text and (deliverable or not args.allow_draft):
                errors.append(f"[标注] {loc} 含未补全标记 {m}")
        for m in SAMPLE_MARKERS:
            if m in text:
                errors.append(f"[示例] {loc} 含模板示例数据 {m}，交付前必须替换")
        if BAD_DASH_DATE.search(text):
            warnings.append(f"[格式] {loc} 出现 2025-07 这类横线日期，03 要求统一为 2025.07")

    prof = data.get("profile") or {}
    if not (prof.get("phone") or prof.get("email")):
        errors.append("[联系] profile 至少要有一个联系方式（phone 或 email）")
    if deliverable and not prof.get("target_role"):
        errors.append("[定位] 投递版必须有 target_role")

    result = {"file": str(path), "ok": not errors, "errors": errors, "warnings": warnings}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for w in warnings:
            print(f"WARN {w}")
        for e in errors:
            print(f"FAIL {e}")
        print(f"{'通过' if not errors else '未通过'}：{len(errors)} 个错误，{len(warnings)} 个警告")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
