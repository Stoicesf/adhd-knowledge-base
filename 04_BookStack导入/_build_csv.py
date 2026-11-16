#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性生成 导入结构清单.csv（UTF-8 带 BOM）。

产物 = 19 条内容页（REGISTRY） + 18 条药品名壳页（来自 03/重定向页保留清单.csv）。
壳页行的"页面类型"列固定写"重定向壳页"，import_bookstack.py 的
--redirects-only 分支以此列作为只导这 18 条的筛选标记。
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from import_bookstack import (  # noqa: E402
    REGISTRY, BOOKS, CHAPTER_ORDER, CONTENT_ROOT, REDIRECT_DIR,
    load_pages, load_redirect_entries,
)

pages = load_pages(None)
actual = {p.entry["id"]: p.entry["slug"] for p in pages}

rows = []
seq = 0
# ---------- 19 条内容页 ----------
for e in REGISTRY:
    seq += 1
    code = e["book"]
    book_slug = BOOKS[code]["slug"]
    book_name = BOOKS[code]["name"]
    chap = e["chapter"] if e["chapter"] else "（书籍顶层）"
    chap_order = CHAPTER_ORDER[code].index(e["chapter"]) + 1 if e["chapter"] else 0
    slug = actual.get(e["id"], e["slug"])
    abs_path = str((CONTENT_ROOT / e["rel"]).resolve())
    rows.append([
        seq,
        book_name,
        book_slug,
        chap,
        chap_order,
        e["title"],
        Path(e["rel"]).name,
        slug,
        e["audience"],
        e["evidence"],
        e["page_type"],
        abs_path,
    ])

# ---------- 18 条药品名壳页（以 03/重定向页保留清单.csv 为准） ----------
redirect_entries = load_redirect_entries()
assert len(redirect_entries) == 18, (
    f"保留清单应为 18 行，实际 {len(redirect_entries)} 行；"
    f"请先核对 03/重定向页保留清单.csv。"
)
for e in redirect_entries:
    seq += 1
    abs_path = str((REDIRECT_DIR / e["filename"]).resolve())
    rows.append([
        seq,
        BOOKS["A"]["name"],                 # 公开知识库（C 端）
        BOOKS["A"]["slug"],                 # public-kb
        "（书籍顶层）",                      # 不挂任何章节
        0,
        e["title"],                         # 页面标题 = 词条本身
        e["filename"],
        e["slug"],                          # redirect_page_slug
        "全部",
        "—",
        "重定向壳页",                        # ← --redirects-only 的筛选标记
        abs_path,
    ])

out = Path(__file__).parent / "导入结构清单.csv"
with open(out, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["序号", "书籍", "书籍slug", "章节", "章节顺序",
                "页面标题", "文件名", "slug", "面向", "证据状态",
                "页面类型", "源文件绝对路径"])
    w.writerows(rows)

content_rows = sum(1 for r in rows if r[10] != "重定向壳页")
shell_rows = sum(1 for r in rows if r[10] == "重定向壳页")
print(f"已写出 {out}")
print(f"总行数 {len(rows)}（内容页 {content_rows} + 壳页 {shell_rows}）")
# 校验 slug 无重复
slugs = [r[7] for r in rows]
dups = [s for s in set(slugs) if slugs.count(s) > 1]
print(f"slug 重复：{dups if dups else '无'}")
