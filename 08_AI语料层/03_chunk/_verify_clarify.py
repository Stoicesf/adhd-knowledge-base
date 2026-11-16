# -*- coding: utf-8 -*-
import csv, re, os

BASE = "F:/ADHD文献/08_AI语料层"
META = os.path.join(BASE, "02_metadata/metadata_63页.csv")
CHUNK_DIR = os.path.join(BASE, "03_chunk")
BATCHES = [
    "chunks_批次1_书A_14页.csv",
    "chunks_批次2_书B01-B12.csv",
    "chunks_批次3_书B13-B26.csv",
    "chunks_批次4_书B27-B40.csv",
    "chunks_批次5_书B42-B45.csv",
]
PAGE_RE = re.compile(r'(?<![A-Za-z0-9])([A-D]\d{2})(?!\d)')
ANNOT_FIELDS = ['备注', '文本摘要', '双向判定依据']

def read_csv(path):
    with open(path, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

# ---- metadata edges ----
meta = read_csv(META)
mset = {r['编号'].strip() for r in meta}
edges = set()
edge_no_evidence = 0
out_counts = {}
for r in meta:
    s = r['编号'].strip()
    ap = (r.get('关联页','') or '').strip()
    aj = (r.get('关联依据','') or '').strip()
    # split both on ;
    ap_list = [x.strip() for x in ap.split(';') if x.strip()]
    aj_list = [x.strip() for x in aj.split(';') if x.strip()]
    out_counts[s] = len(ap_list)
    for i, t in enumerate(ap_list):
        edges.add((s, t))
        # does this edge have evidence? match aj entry starting with f"{t}="
        has = any(a.startswith(t + "=") for a in aj_list)
        if not has:
            edge_no_evidence += 1

print("=== metadata edges ===")
print("total directed edges:", len(edges))
print("edges with NO 关联依据 evidence:", edge_no_evidence)
cd_pages = {p for p in mset if p.startswith('C') or p.startswith('D')}
print("C/D pages:", sorted(cd_pages))
cd_out = {p: out_counts.get(p,0) for p in sorted(cd_pages)}
print("C/D out-edge counts:", cd_out, "sum:", sum(cd_out.values()))

# ---- chunk mention pairs ----
mentions = {}  # (s,t) -> count
for b in BATCHES:
    for r in read_csv(os.path.join(CHUNK_DIR, b)):
        s = r['页编号'].strip()
        for f in ANNOT_FIELDS:
            txt = r.get(f,'') or ''
            for m in PAGE_RE.finditer(txt):
                t = m.group(1)
                if t != s and t in mset:
                    mentions[(s,t)] = mentions.get((s,t), 0) + 1

total = len(mentions)
direct = [k for k in mentions if k in edges]
reverse_only = [k for k in mentions if k not in edges and (k[1],k[0]) in edges]
none = [k for k in mentions if k not in edges and (k[1],k[0]) not in edges]

print("")
print("=== chunk mention pairs ===")
print("total distinct mention pairs (s,t):", total)
print("  direct (metadata has s->t):", len(direct))
print("  reverse-only (metadata has t->s, not s->t):", len(reverse_only), sorted(reverse_only))
print("  none (no metadata edge at all):", len(none), sorted(none))
print("  SUM direct+reverse+none:", len(direct)+len(reverse_only)+len(none))
print("  -> do they partition total? ", (len(direct)+len(reverse_only)+len(none))==total)

# overlap check: is any direct also reverse? No by mutual exclusivity.
# Are reverse and none disjoint? yes by definition.
# So the only way 45 != 50 is if total computed here is 50 not 45,
# OR earlier '45' was a different dedup (e.g. counted mention instances not pairs).

# total mention INSTANCES (with multiplicity) for reference
tot_inst = sum(mentions.values())
print("total mention instances (with multiplicity):", tot_inst)
