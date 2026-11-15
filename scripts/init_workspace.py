#!/usr/bin/env python3
"""按流程建立用户求职目录，只新建、不覆盖已有文件。

用法：
    python3 scripts/init_workspace.py <求职目录>                              # 首次使用
    python3 scripts/init_workspace.py <求职目录> --direction <方向名>           # 用户选定当前方向后
    python3 scripts/init_workspace.py <求职目录> --direction <方向名> --project <项目名>     # 用户选定项目后
    python3 scripts/init_workspace.py <求职目录> --direction <方向名> --company <公司-岗位>  # 用户贴出 JD 后

目录结构见 SKILL.md「目录与状态契约」。不写技能目录，不修改 assets/ 母版。
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
BAD = re.compile(r'[\s/\\:*?"<>|]')


def check_name(kind: str, name: str) -> None:
    if BAD.search(name):
        sys.exit(f"{kind}“{name}”含空格或非法字符，只用中文、字母、数字、连字符")


def mkdir(p: Path, made: list[str]) -> None:
    if not p.exists():
        p.mkdir(parents=True)
        made.append(str(p) + "/")


def copy(src: Path, dst: Path, made: list[str]) -> None:
    if dst.exists():
        return
    shutil.copyfile(src, dst)
    made.append(str(dst))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--direction")
    ap.add_argument("--project")
    ap.add_argument("--company")
    args = ap.parse_args()
    if (args.project or args.company) and not args.direction:
        sys.exit("--project 与 --company 需要同时给 --direction")

    root = Path(args.root)
    if ASSETS.parent in [root.resolve(), *root.resolve().parents]:
        sys.exit("不要把求职目录建在技能目录里")
    made: list[str] = []
    mkdir(root, made)
    mkdir(root / "投递", made)
    copy(ASSETS / "求职档案模板.md", root / "求职档案.md", made)

    tpl = ASSETS / "过程文档模板"
    if args.direction:
        check_name("方向名", args.direction)
        d = root / "方向" / args.direction
        for sub in ("简历", "项目", "投递", "JD原文", "JD截图"):
            mkdir(d / sub, made)
        for name in ("方向结论.md", "检索词与城市公司.md", "JD样本.md"):
            copy(tpl / name, d / name, made)
        if args.project:
            check_name("项目名", args.project)
            mkdir(d / "项目" / args.project, made)
        if args.company:
            check_name("公司-岗位", args.company)
            c = d / "投递" / args.company
            mkdir(c, made)
            copy(tpl / "匹配分析.md", c / "匹配分析.md", made)

    print("新建：" if made else "没有需要新建的内容")
    for m in made:
        print("  " + m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
