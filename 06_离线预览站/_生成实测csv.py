#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索实测结果.csv 生成脚本（可复算）
- 从 index.html 内嵌的 PAGES JSON 复刻搜索逻辑
- 从 重定向页保留清单.csv 读取 18 条壳页标题
- 对 8 个查询词逐条统计：横幅/跳转/前10条标题/壳页占比/现存壳页标题命中数
输出：搜索实测结果.csv (UTF-8 BOM)
"""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "index.html"
CSV_IN = ROOT.parent / "03_零用药系统配置" / "重定向页保留清单.csv"
CSV_OUT = ROOT / "搜索实测结果.csv"

# ---- 1. 从 index.html 提取内嵌 JS 中的 PAGES / MEDKW / REDIRECT_TERMS ----
html = HTML.read_text(encoding="utf-8")
m = re.search(r"<script>([\s\S]*?)</script>", html)
js = m.group(1)

def grab(name, js):
    m = re.search(r"var %s = (\[.*?\]);" % name, js, re.S)
    return json.loads(m.group(1))

PAGES = grab("PAGES", js)
MEDKW = grab("MEDKW", js)
REDIRECT_TERMS = grab("REDIRECT_TERMS", js)

# ---- 2. 读取 18 条壳页标题（CSV 权威） ----
shell_titles = []
with open(CSV_IN, encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        t = (row.get("词条") or "").strip()
        if t:
            shell_titles.append(t)
print("壳页标题数: %d" % len(shell_titles))

# ---- 3. 复刻搜索逻辑 ----
def do_search(q):
    ql = q.strip().lower()
    med_hit = any(kw.lower() in ql for kw in MEDKW)
    redirect_hit = any(kw.lower() in ql for kw in REDIRECT_TERMS)
    hits = [p for p in PAGES if ql in (p["title"] + " " + p["text"]).lower()]
    hits.sort(key=lambda p: 0 if ql in p["title"].lower() else 1)
    return med_hit, redirect_hit, hits

# ---- 4. 8 个查询词 ----
queries = [
    ("药物", "通用词"),
    ("剂量", "通用词"),
    ("副作用", "通用词"),
    ("要不要吃药", "通用词"),
    ("专注达", "药品名"),
    ("择思达", "药品名"),
    ("作业", "普通词"),
    ("老师", "普通词"),
]

rows = []
for q, qtype in queries:
    med_hit, redirect_hit, hits = do_search(q)
    top10 = hits[:10]
    titles = [("%s · %s" % (p["id"], p["title"])) for p in top10]
    # 壳页占比：预览搜索索引里只有 19 个内容页，壳页不在索引里，所以恒为 0
    shell_in_results = [t for t in titles if any(shell in t for shell in shell_titles)]
    # 现存壳页标题命中数：18 个壳页标题中含该查询词的条数
    shell_title_hits = [s for s in shell_titles if q in s]
    rows.append({
        "查询词": q,
        "词条类型": qtype,
        "前10条结果条数": len(hits),
        "其中重定向壳页条数": len(shell_in_results),
        "是否出现横幅": "是" if med_hit else "否",
        "是否出现跳转提示": "是" if redirect_hit else "否",
        "跳转落点": "A06（用药兜底页 medication-boundary）" if redirect_hit else "—",
        "现存壳页标题命中数": len(shell_title_hits),
        "前10条结果标题(用;分隔)": "; ".join(titles),
        "其中壳页标题": "; ".join(shell_in_results),
    })

# ---- 5. 写 CSV (UTF-8 BOM) ----
MEASUREMENT_BASIS = "预览站本地检索模拟（非真实 BookStack 站内搜索）"
fieldnames = ["测量口径","查询词","词条类型","前10条结果条数","其中重定向壳页条数",
              "是否出现横幅","是否出现跳转提示","跳转落点",
              "现存壳页标题命中数","前10条结果标题(用;分隔)","其中壳页标题"]
with open(CSV_OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in rows:
        row_out = {"测量口径": MEASUREMENT_BASIS}
        row_out.update(r)
        w.writerow(row_out)

print("输出: %s" % CSV_OUT)
print("行数(含表头): %d" % (len(rows) + 1))
print("列数: %d" % len(fieldnames))
print()
print("=== 关键统计 ===")
for r in rows:
    print("%s\t横幅=%s\t跳转=%s\t结果数=%d\t壳页命中=%d\t现存壳页标题命中=%d"
          % (r["查询词"], r["是否出现横幅"], r["是否出现跳转提示"],
             r["前10条结果条数"], r["其中重定向壳页条数"], r["现存壳页标题命中数"]))
