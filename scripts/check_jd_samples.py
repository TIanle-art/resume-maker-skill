#!/usr/bin/env python3
"""检查方向 JD 样本的数量、覆盖与时效，给出“使用前复查”的判定。

用法：
    python3 scripts/check_jd_samples.py <方向目录 或 JD样本.md> [--city 首选城市] [--fast] [--niche] [--today YYYY-MM-DD] [--json]

判定（规则见 references/03-JD收集.md §2.0 与 §6）：
    可直接用 / 需要增量 / 需要重收 / 需要补收
退出码：0 可直接用；1 需要增量、重收或补收；2 文件无法读取或没有任何条目。

输入是方向目录时，读其中的 JD样本.md（索引，取方向规模）与 JD原文/*.md（条目）；
也可以直接给单个文件。脚本只做计数与日期判断，不判断 JD 内容是否真实，不去重，也不联网；重复发布的岗位在录入时合并为一条。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

ENTRY = re.compile(r"^###\s+(J\d+)\s+(.+?)\s*$", re.M)
FIELD = re.compile(r"^-\s*([^：:]+)[：:]\s*(.*)$", re.M)
DATE = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})")

TIERS = {
    "常规": ({"valid": 20, "companies": 10, "ceiling": 5, "city": 5}, {"valid": 30, "companies": 15}),
    "小众": ({"valid": 10, "companies": 5, "ceiling": 3, "city": 3}, {"valid": 15, "companies": 8}),
}
NICHE = re.compile(r"方向规模\s*[：:]\s*小众")
INVALID = {"已关闭", "已过期", "已下线", "抓取失败"}


def parse_date(text: str) -> date | None:
    m = DATE.search(text or "")
    if not m:
        return None
    try:
        return date(int(m[1]), int(m[2]), int(m[3]))
    except ValueError:
        return None


def parse(text: str) -> list[dict]:
    heads = list(ENTRY.finditer(text))
    entries = []
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        nxt = re.search(r"^##\s", text[h.end():end], re.M)
        body = text[h.end(): h.end() + nxt.start()] if nxt else text[h.end():end]
        fields = {k.strip(): v.strip() for k, v in FIELD.findall(body)}
        title = h[2]
        company = re.split(r"[｜|]", title)[0].strip()
        entries.append({"id": h[1], "company": company, "fields": fields})
    return entries


def filled(v: str | None) -> bool:
    return bool(v) and "〈" not in v and v not in {"无", "未知"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--city", help="首选城市，检查该城市有效条数是否达到最低线")
    ap.add_argument("--fast", action="store_true", help="技术迭代快的方向：时效线从 30/90 天收紧为 14/60 天")
    ap.add_argument("--niche", action="store_true", help="按小众方向的门槛判定；收集概况里写了“方向规模：小众”时自动启用")
    ap.add_argument("--today", help="用于测试的当前日期 YYYY-MM-DD")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"找不到：{path}")
        return 2
    index_ids: set[str] = set()
    if path.is_dir():
        index = path / "JD样本.md"
        index_text = index.read_text(encoding="utf-8") if index.exists() else ""
        index_ids = set(re.findall(r"^\|\s*(J\d+)\s*\|", index_text, re.M))
        raws = sorted((path / "JD原文").glob("*.md")) if (path / "JD原文").is_dir() else []
        text = index_text + "\n" + "\n".join(f.read_text(encoding="utf-8") for f in raws)
    else:
        text = path.read_text(encoding="utf-8")
    tier = "小众" if (args.niche or NICHE.search(text)) else "常规"
    MIN, GOAL = TIERS[tier]
    entries = parse(text)
    if not entries:
        print("没有找到任何 JD 条目（条目标题应为“### J001 公司｜岗位名”）")
        return 2

    today = parse_date(args.today) if args.today else date.today()
    fresh, stale = (14, 60) if args.fast else (30, 90)

    valid, problems = [], []
    status_count = Counter()
    for e in entries:
        f = e["fields"]
        status = f.get("状态", "")
        status_count[status or "未填"] += 1
        if status != "有效":
            continue
        if not (filled(f.get("核心职责")) and filled(f.get("核心要求"))):
            problems.append(f"{e['id']} 标为有效但职责或要求不完整，未计入")
            continue
        if not filled(f.get("来源")):
            problems.append(f"{e['id']} 缺来源，未计入")
            continue
        pub = parse_date(f.get("发布日期", ""))
        if pub and (today - pub).days > 183:
            problems.append(f"{e['id']} 发布超过半年，未计入")
            continue
        valid.append(e)

    companies = Counter(e["company"] for e in valid)
    cities = Counter()
    for e in valid:
        for c in re.split(r"[、,，/／\s]+", e["fields"].get("城市", "")):
            if c:
                cities[c] += 1
    layers = Counter(e["fields"].get("分层", "未填") for e in valid)
    dates = [d for d in (parse_date(e["fields"].get("抓取日期", "")) for e in valid) if d]
    latest = max(dates) if dates else None
    age = (today - latest).days if latest else None
    dead = sum(status_count[s] for s in INVALID)
    judged = dead + len(valid)
    dead_ratio = dead / judged if judged else 0.0

    gaps = []
    if len(valid) < MIN["valid"]:
        gaps.append(f"有效条数 {len(valid)}，低于最低线 {MIN['valid']}")
    if len(companies) < MIN["companies"]:
        gaps.append(f"覆盖公司 {len(companies)} 家，低于最低线 {MIN['companies']}")
    if layers.get("天花板", 0) < MIN["ceiling"]:
        gaps.append(f"天花板层 {layers.get('天花板', 0)} 条，低于最低线 {MIN['ceiling']}")
    if not layers.get("可投"):
        gaps.append("没有可投层样本")
    if args.city and cities.get(args.city, 0) < MIN["city"]:
        gaps.append(f"首选城市 {args.city} 只有 {cities.get(args.city, 0)} 条，低于最低线 {MIN['city']}")
    if dead_ratio > 1 / 3:
        gaps.append(f"失效条目占 {dead_ratio:.0%}，超过三分之一")

    if latest is None:
        verdict, reason = "需要补收", "有效条目都没有抓取日期，无法判断时效"
    elif age > stale:
        verdict, reason = "需要重收", f"最近一轮在 {age} 天前，超过 {stale} 天"
    elif gaps:
        verdict, reason = "需要补收", "；".join(gaps)
    elif age > fresh:
        verdict, reason = "需要增量", f"最近一轮在 {age} 天前，超过 {fresh} 天"
    else:
        verdict, reason = "可直接用", f"最近一轮在 {age} 天前，数量与覆盖达到最低线"

    notes = []
    if index_ids:
        ids = {e["id"] for e in entries}
        if ids - index_ids:
            notes.append(f"索引表缺 {len(ids - index_ids)} 条原文里有的 JD：" + "、".join(sorted(ids - index_ids)[:5]))
        if index_ids - ids:
            notes.append(f"索引表有 {len(index_ids - ids)} 条在原文里找不到：" + "、".join(sorted(index_ids - ids)[:5]))
    if verdict == "可直接用":
        if len(valid) < GOAL["valid"]:
            notes.append(f"有效条数 {len(valid)}，未到目标 {GOAL['valid']}，建议继续补")
        if len(companies) < GOAL["companies"]:
            notes.append(f"公司 {len(companies)} 家，未到目标 {GOAL['companies']}")

    result = {
        "verdict": verdict, "reason": reason, "tier": tier, "entries": len(entries), "valid": len(valid),
        "companies": len(companies), "cities": dict(cities), "layers": dict(layers),
        "status": dict(status_count), "latest": latest.isoformat() if latest else None,
        "age_days": age, "dead_ratio": round(dead_ratio, 2), "gaps": gaps,
        "notes": notes, "problems": problems,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"判定：{verdict}——{reason}（按{tier}方向门槛）")
        print(f"条目 {len(entries)}，有效 {len(valid)}，公司 {len(companies)} 家，最近一轮 {result['latest'] or '未知'}")
        print("城市：" + ("、".join(f"{k}×{v}" for k, v in cities.most_common()) or "未填"))
        print("分层：" + ("、".join(f"{k}×{v}" for k, v in layers.most_common()) or "未填"))
        print("状态：" + "、".join(f"{k}×{v}" for k, v in status_count.most_common()))
        for line in notes + problems:
            print("提示：" + line)
    return 0 if verdict == "可直接用" else 1


if __name__ == "__main__":
    sys.exit(main())
