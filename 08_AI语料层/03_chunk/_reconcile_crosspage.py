# -*- coding: utf-8 -*-
import csv, re, os
from collections import defaultdict

BASE = "F:/ADHD文献/08_AI语料层"
META = BASE + "/02_metadata/metadata_63页.csv"
CHUNK_DIR = BASE + "/03_chunk"
BATCHES = [
    "chunks_批次1_书A_14页.csv",
    "chunks_批次2_书B01-B12.csv",
    "chunks_批次3_书B13-B26.csv",
    "chunks_批次4_书B27-B40.csv",
    "chunks_批次5_书B42-B45.csv",
]
PAGE_RE = re.compile(r'(?<![A-Za-z0-9])[A-D]\d{2}(?!\d)')
ANNOT_FIELDS = ['备注', '文本摘要', '双向判定依据']


def read_csv(path):
    with open(path, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


# ---------- 1. metadata edge graph ----------
meta = read_csv(META)
meta_pages = {r['编号'].strip(): r for r in meta}

meta_edges = defaultdict(set)          # src -> set(tgt)  (directed)
edge_count = 0
no_evidence = []
for r in meta:
    src = r['编号'].strip()
    rel = (r.get('关联页', '') or '').strip()
    ev = (r.get('关联依据', '') or '').strip()
    ev_map = {}
    for item in ev.split(';'):
        item = item.strip()
        if not item or item == '无':
            continue
        m = re.match(r'^([A-D]\d{2})\s*=', item)
        if m:
            ev_map[m.group(1)] = item
    for tgt in rel.split(';'):
        tgt = tgt.strip()
        if not tgt or tgt == '无':
            continue
        meta_edges[src].add(tgt)
        edge_count += 1
        if tgt not in ev_map:
            no_evidence.append((src, tgt))

asym = []
for src in meta_edges:
    for tgt in meta_edges[src]:
        if tgt in meta_pages and src not in meta_edges.get(tgt, set()):
            asym.append((src, tgt))

undirected = set()
for src in meta_edges:
    for tgt in meta_edges[src]:
        undirected.add(tuple(sorted([src, tgt])))

# ---------- 2. chunks ----------
all_chunks = []
for b in BATCHES:
    for r in read_csv(os.path.join(CHUNK_DIR, b)):
        r['_batch'] = b
        all_chunks.append(r)

chunk_pages = sorted({r['页编号'].strip() for r in all_chunks})
not_chunked = sorted([p for p in meta_pages if p not in set(chunk_pages)])

# cross-page 前置依赖 violations (should be 0 per §8.5)
cross_page_dep = []
for r in all_chunks:
    dep = (r.get('前置依赖', '') or '').strip()
    if dep and dep != '—':
        src_page = r['页编号'].strip()
        m = re.match(r'^([A-D]\d{2})', dep)
        dep_page = m.group(1) if m else dep
        if dep_page != src_page:
            cross_page_dep.append((r['块id'], src_page, dep, dep_page))

# extract cross-page mentions from annotation fields
chunk_mentions = defaultdict(set)      # src_page -> set(tgt_page)
mention_detail = []                    # (src,tgt,chunk_id,field,snippet)
for r in all_chunks:
    src = r['页编号'].strip()
    for fld in ANNOT_FIELDS:
        txt = r.get(fld, '') or ''
        for m in PAGE_RE.finditer(txt):
            tgt = m.group(0)
            if tgt == src or tgt not in meta_pages:
                continue
            if tgt not in chunk_mentions[src]:
                chunk_mentions[src].add(tgt)
                snip = txt[max(0, m.start() - 15):m.end() + 15].replace('\n', ' ').strip()
                mention_detail.append((src, tgt, r['块id'], fld, snip))

# ---------- 3. reconciliation ----------
meta_edges_chunked = {s: ts for s, ts in meta_edges.items() if s in set(chunk_pages)}
total_meta_chunked = sum(len(ts) for ts in meta_edges_chunked.values())

covered, uncovered, uncovered_rev = [], [], []
for s, ts in meta_edges_chunked.items():
    for t in ts:
        if t in chunk_mentions.get(s, set()):
            covered.append((s, t))
        elif s in chunk_mentions.get(t, set()):
            uncovered_rev.append((s, t))
        else:
            uncovered.append((s, t))

contra = []   # chunk mention with no metadata edge in either direction
for s, ts in chunk_mentions.items():
    for t in ts:
        if (t not in meta_edges.get(s, set())) and (s not in meta_edges.get(t, set())):
            contra.append((s, t))

# ---------- 4. outputs ----------
out_dir = CHUNK_DIR

# 4a. combined chunks CSV
combined_path = os.path.join(out_dir, "chunks_全量58页.csv")
with open(combined_path, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=list(all_chunks[0].keys()))
    w.writeheader()
    for r in all_chunks:
        w.writerow(r)

# 4b. reconciliation detail CSV (per metadata edge)
detail_path = os.path.join(out_dir, "对账_跨页明细.csv")
with open(detail_path, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['源页', '目标页', '有证据(关联依据)', 'chunk是否提及(同向)', 'chunk是否提及(反向)', '处置'])
    for s in sorted(meta_edges_chunked):
        for t in sorted(meta_edges_chunked[s]):
            has_ev = '否' if (s, t) in [(a, b) for a, b in no_evidence] else '是'
            fwd = '是' if t in chunk_mentions.get(s, set()) else '否'
            rev = '是' if s in chunk_mentions.get(t, set()) else '否'
            note = ''
            if fwd == '否' and rev == '否':
                note = 'metadata有边但chunk层未提及(待核是否漏标/正文无此链接)'
            elif fwd == '否' and rev == '是':
                note = '仅反向被chunk提及，metadata该边为单向(正文单向关联?)'
            w.writerow([s, t, has_ev, fwd, rev, note])

# 4c. chunk mentions not in metadata
contra_path = os.path.join(out_dir, "对账_chunk提及未入metadata.csv")
with open(contra_path, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['源页', '目标页', '提及块数', '示例块id', '示例字段', '示例片段', 'metadata是否含反向边'])
    for (s, t) in sorted(contra):
        rel = [d for d in mention_detail if d[0] == s and d[1] == t]
        ex = rel[0] if rel else (s, t, '', '', '')
        rev_in_meta = '是' if s in meta_edges.get(t, set()) else '否'
        w.writerow([s, t, len(rel), ex[2], ex[3], ex[4], rev_in_meta])

# 4d. asymmetric metadata edges
asym_path = os.path.join(out_dir, "对账_metadata非对称边.csv")
with open(asym_path, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['源页', '目标页', '说明'])
    for (s, t) in sorted(asym):
        w.writerow([s, t, f'metadata有 {s}→{t} 但无 {t}→{s}'])

# 4e. no-evidence metadata edges
noev_path = os.path.join(out_dir, "对账_metadata无据边.csv")
with open(noev_path, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['源页', '目标页'])
    for (s, t) in sorted(no_evidence):
        w.writerow([s, t])

# ---------- summary print ----------
print("===== 1. METADATA EDGE GRAPH =====")
print(f"metadata 页数: {len(meta_pages)}")
print(f"关联页 有向边总数: {edge_count}")
print(f"关联页 无向唯一边: {len(undirected)}")
print(f"有向边中缺 关联依据 证据的: {len(no_evidence)}")
print(f"非对称边(A→B 但无 B→A): {len(asym)}")

print("\n===== 2. CHUNK LAYER =====")
print(f"chunk 总数: {len(all_chunks)}")
print(f"chunk 覆盖页: {len(chunk_pages)}")
print(f"metadata 有但未切分的页: {not_chunked}")
print(f"跨页 前置依赖 违规(应为0): {len(cross_page_dep)}")
if cross_page_dep:
    for x in cross_page_dep[:10]:
        print("   ", x)

print("\n===== 3. RECONCILIATION =====")
print(f"chunk层 跨页提及对(去重): {sum(len(v) for v in chunk_mentions.values())}")
print(f"metadata 边(源页已切分): {total_meta_chunked}")
print(f"  - chunk层同向提及覆盖: {len(covered)}")
print(f"  - metadata有边但chunk仅反向提及: {len(uncovered_rev)}")
print(f"  - metadata有边但chunk完全未提及: {len(uncovered)}")
print(f"chunk提及但metadata双向均无边(候选): {len(contra)}")

print("\n===== 4. OUTPUTS =====")
for p in [combined_path, detail_path, contra_path, asym_path, noev_path]:
    print("  ", p, os.path.getsize(p), "bytes")

print("\n--- 样本: chunk提及但未入metadata(候选) 前15 ---")
for (s, t) in sorted(contra)[:15]:
    rel = [d for d in mention_detail if d[0] == s and d[1] == t]
    print(f"  {s}→{t}  e.g. {rel[0][2]} [{rel[0][3]}] «{rel[0][4]}»")

print("\n--- 样本: metadata有边但chunk完全未提及 前15 ---")
for (s, t) in uncovered[:15]:
    print(f"  {s}→{t}")
