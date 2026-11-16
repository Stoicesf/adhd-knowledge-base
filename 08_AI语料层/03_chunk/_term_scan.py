# -*- coding: utf-8 -*-
import os, re, csv
from collections import defaultdict

CORPUS = "F:/ADHD文献/02_内容包"
OUT = "F:/ADHD文献/08_AI语料层/03_chunk/阶段三_术语一致性_原始计数.csv"

# core term -> list of surface variants to search
TERMS = {
    '执行功能': ['执行功能', '执行功能障碍', '执行功能缺陷', '执行功能不足', 'executive function', 'EF'],
    '合理调整': ['合理调整', '合理便利', '便利措施', '便利调整'],
    '转介':     ['转介', '转诊', '转介到', '转介至', '转给', 'refer', 'referral'],
    '共病':     ['共病', '合并症', '伴随疾病', 'comorbid', 'comorbidity'],
    '支持':     ['支持策略', '支持方式', '支持系统', '外部支持', '社会支持', '支持性', '支持', '帮助', '协助'],
    '结构化讨论': ['结构化讨论', '结构化沟通', '结构化对话', '结构化交流', '结构化会谈', '结构化访谈'],
    '环境调整': ['环境调整', '环境改造', '环境布置', '环境安排', '环境支持', '物理环境调整'],
}

# gather md files
files = []
for root, _, fs in os.walk(CORPUS):
    for f in fs:
        if f.endswith('.md'):
            files.append(os.path.join(root, f))
files.sort()

# per (term, variant): per-file count
# structure: data[term][variant][relfile] = count
data = {t: {v: defaultdict(int) for v in vs} for t, vs in TERMS.items()}
corpus_count = {t: {v: 0 for v in vs} for t, vs in TERMS.items()}

for fp in files:
    rel = os.path.relpath(fp, CORPUS)
    # use page id from filename like B44_xxx.md -> B44
    m = re.match(r'([A-D]\d{2})_', os.path.basename(fp))
    pid = m.group(1) if m else rel
    text = open(fp, encoding='utf-8').read()
    for t, vs in TERMS.items():
        for v in vs:
            c = text.count(v)
            if c:
                data[t][v][pid] += c
                corpus_count[t][v] += c

# output raw csv: term, variant, corpus_total, n_files, files(list)
with open(OUT, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['核心术语', '变体', '全库次数', '出现页数', '出现页面'])
    for t, vs in TERMS.items():
        for v in vs:
            files_lst = sorted(data[t][v].keys())
            w.writerow([t, v, corpus_count[t][v], len(files_lst), ';'.join(files_lst)])

# console summary
print("===== 术语变体扫描摘要 =====")
for t, vs in TERMS.items():
    used = [(v, corpus_count[t][v]) for v in vs if corpus_count[t][v] > 0]
    n_var = len(used)
    print(f"\n### {t}  (出现变体数: {n_var})")
    for v, c in used:
        pages = sorted(data[t][v].keys())
        intra = [p for p in pages if sum(1 for vv in vs if data[t][vv].get(p,0)>0) > 1]
        print(f"  {v}: 全库 {c} 次, 页 {len(pages)}: {pages}")
    if n_var > 1:
        # intra-file: files using >1 variant of this term
        intra_files = set()
        for p in set().union(*[set(data[t][v].keys()) for v in vs]):
            cnt = sum(1 for v in vs if data[t][v].get(p,0)>0)
            if cnt > 1:
                intra_files.add(p)
        if intra_files:
            print(f"  >> 同页混用多变体: {sorted(intra_files)}")
print("\n原始计数已写入:", OUT)
