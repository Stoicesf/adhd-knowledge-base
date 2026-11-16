# -*- coding: utf-8 -*-
import csv, os, re, json, math

CORPUS_DIR = "F:/ADHD文献/02_内容包"
EVAL_CSV = "F:/ADHD文献/08_AI语料层/04_评测集草案/阶段四_评测集草案_30题.csv"

# ---- 载入语料（每页正文 + metadata 边界摘要）----
def page_id_from(fn):
    m = re.match(r"([A-D]\d{2})_", os.path.basename(fn))
    return m.group(1) if m else None

docs = {}  # pid -> text
for root, _, files in os.walk(CORPUS_DIR):
    for f in files:
        if f.endswith(".md"):
            pid = page_id_from(f)
            if not pid:
                continue
            txt = open(os.path.join(root, f), encoding="utf-8").read()
            # 去掉 markdown 标记噪音
            txt = re.sub(r"[#>*`\-|\[\]\(\)]", " ", txt)
            docs[pid] = txt

# metadata 边界摘要（增强检索锚点）
meta = {}
for r in csv.DictReader(open("F:/ADHD文献/08_AI语料层/02_metadata/metadata_63页.csv", encoding="utf-8-sig")):
    pid = r["编号"].strip()
    parts = [r.get("页题", ""), r.get("适用条件", ""), r.get("不适用条件", ""), r.get("关联页", "")]
    meta[pid] = " ".join(parts)

# 合并：正文 + 边界摘要（边界摘要帮助对齐“场景语义”）
index_text = {pid: docs.get(pid, "") + " " + meta.get(pid, "") for pid in set(list(docs) + list(meta))}

# ---- 分词：字一元 + 字二元 + 领域词典 ----
LEX = ["执行功能","合理调整","转介","共病","合并症","支持","结构化讨论","环境调整","安全事件","推搡",
       "抢东西","孤立","插嘴","打断","暴怒","发脾气","评估","药物","剂量","补剂","漏诊","女性",
       "青春期","学前","学龄","教师","家长","伴侣","成人","作业","座位","考试","自伤","情绪",
       "社交","诊断","报告","班主任","年级组","心理老师","精神科","合理调整","运动","睡眠","提醒"]

def tokenize(s):
    s = re.sub(r"\s+", "", s)
    toks = set()
    # 词典匹配
    for w in LEX:
        if w in s:
            toks.add("LEX:" + w)
    # 字一元
    for ch in s:
        if ch.strip():
            toks.add("U:" + ch)
    # 字二元
    for i in range(len(s) - 1):
        toks.add("B:" + s[i:i+2])
    return toks

# 构建 DF
df = {}
all_tok = {}
for pid, t in index_text.items():
    tk = tokenize(t)
    all_tok[pid] = tk
    for x in tk:
        df[x] = df.get(x, 0) + 1

N = len(all_tok)
def idf(tok):
    return math.log((N + 1) / (df.get(tok, 0) + 1)) + 1.0

# 预计算每篇文档的 token 计数
doc_tf = {}
for pid, tk in all_tok.items():
    c = {}
    for x in tk:
        c[x] = c.get(x, 0) + 1
    doc_tf[pid] = c

def score(pid, qtok):
    c = doc_tf[pid]
    s = 0.0
    for t in qtok:
        if t in c:
            s += idf(t) * (1 + math.log(1 + c[t]))
    return s

# ---- 跑评测题 ----
rows = list(csv.DictReader(open(EVAL_CSV, encoding="utf-8-sig")))
results = []
for r in rows:
    q = r["问题原文"]
    qt = tokenize(q)
    scored = [(score(pid, qt), pid) for pid in doc_tf]
    scored.sort(reverse=True)
    top5 = [pid for _, pid in scored[:5]]
    must = [x.strip() for x in r["必须命中页"].split(";") if x.strip()]
    should = [x.strip() for x in r["应该命中页"].split(";") if x.strip()]
    must_hit = [m for m in must if m in top5]
    should_hit = [s for s in should if s in top5]
    results.append({
        "题号": r["题号"], "问题": q, "top5": top5,
        "必须命中": must, "应该命中": should,
        "must_in_top5": must_hit, "should_in_top5": should_hit,
        "命中期望页": "是" if must_hit else "否",
    })

# 统计
hit = sum(1 for x in results if x["命中期望页"] == "是")
print("=== 必须命中页 top5 命中率: %d/%d (%.1f%%) ===" % (hit, len(results), 100*hit/len(results)))
print()
for x in results:
    print("%s | 命中:%s | top5:%s | 必须:%s 命中[%s] | 应该命中[%s]" % (
        x["题号"], x["命中期望页"], ",".join(x["top5"]),
        "/".join(x["必须命中"]), "/".join(x["must_in_top5"]),
        "/".join(x["should_in_top5"])))

json.dump(results, open("F:/ADHD文献/08_AI语料层/04_评测集草案/_retrieval_results.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n[written] _retrieval_results.json")
