# -*- coding: utf-8 -*-
"""批次 6-D 只读审计探针（可复跑，不修改任何项目文件）。

覆盖：
  6D.1  Q1：24 条 inject_text 逐句召回「修复语义」候选句（宽召回，人工判定在审计 md）
  6D.2  Q2：四组 (audience, scenario) 检索 + 全 10368 状态点可达集交叉检查
        + router.route 场景收窄实测（含 scenario=None 的边界灰区）
  6D.3  Q3：server.py 入参/依赖静态证据、README 是否已写明、回归旁路守卫

用法：E:/ANACONDA/python.exe data/_batch6D_audit.py
输出仅为 stdout 证据，不落盘、不改产物。
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
CLONE = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(CLONE, "..", ".."))
COMPILE = os.path.join(ROOT, "03_agent编译")
CHUNKS = os.path.join(COMPILE, "output", "chunks.jsonl")
SERVER = os.path.join(CLONE, "server", "server.py")
README = os.path.join(CLONE, "README.md")

sys.path.insert(0, COMPILE)
sys.path.insert(0, os.path.join(COMPILE, "validators"))

import build            # noqa: E402
import router           # noqa: E402
import predicate_equiv as pe  # noqa: E402

chunks = [json.loads(l) for l in open(CHUNKS, encoding="utf-8") if l.strip()]


def sentences(text):
    """与 server.assemble_line_and_steps 同一套切句口径。"""
    return [s.strip() for s in (text or "").replace("\n", "。").split("。") if s.strip()]


# ---------------------------------------------------------------- 6D.1 / Q1
# 宽召回：宁可多召回再人工排除，也不漏判。「修复语义」的判定标准写在审计 md，
# 这里只负责把「事后态 / 关系词 / 回避态」相关句子全部摊出来。
REPAIR_CUES = [
    "修复", "道歉", "对不起", "抱歉", "和好", "承认", "主动", "重新连",
    "关系", "抱", "说清楚", "解释", "事后", "发火", "吼", "刚才我", "我刚才",
]
AFTER_CUES = ["刚才", "之后", "回来", "第二天", "明晚", "回头", "复盘", "事后"]
AVOID_CUES = ["不翻旧账", "旧账", "不追问", "不在当晚", "不预测明天", "不提", "不展开"]

print("=" * 78)
print("6D.1 / Q1：24 条 inject_text 修复语义候选句（宽召回）")
print("=" * 78)
print("chunks =", len(chunks))
cand_rows = []
for c in chunks:
    segs = sentences(c["inject_text"])
    hits = []
    for i, s in enumerate(segs):
        cue = [k for k in (REPAIR_CUES + AFTER_CUES + AVOID_CUES) if k in s]
        if cue:
            hits.append((i, s, cue))
    cand_rows.append((c["id"], c["scenario"], len(segs), hits))
    if hits:
        print("")
        print("### %s | scenario=%s | 句数=%d" % (c["id"], c["scenario"], len(segs)))
        for i, s, cue in hits:
            print("   [%02d] (%s) %s" % (i, "/".join(cue), s))
    else:
        print("")
        print("### %s | scenario=%s | 句数=%d | 无候选句" % (c["id"], c["scenario"], len(segs)))

n_cand = sum(len(r[3]) for r in cand_rows)
print("")
print("[Q1 召回统计] 条目=%d  含候选句的条目=%d  候选句总数=%d"
      % (len(cand_rows), sum(1 for r in cand_rows if r[3]), n_cand))

# 24 行审计表（逐字取自 inject_text 首句，供审计 md 直接引用，不手抄）
print("")
print("--- (T) 24 行审计表 markdown ---")
for c in chunks:
    ss = sentences(c["inject_text"])
    first = ss[0] if ss else ""
    short = first[:34] + ("…" if len(first) > 34 else "")
    short = short.replace("|", "／")
    nc = sum(1 for s in ss if any(k in s for k in (REPAIR_CUES + AFTER_CUES + AVOID_CUES)))
    col4 = "否" if nc == 0 else "否（%d 候选）" % nc
    col5 = "—" if nc == 0 else "见 §Q1 候选句排除表"
    print("| `%s` | %s | %s | %s | %s |"
          % (c["id"], c["scenario"], short, col4, col5))

# 严格「主动修复关系」信号：家长承认/道歉/和好/主动重新连接。
# 任一命中即需人工复核是否可逐字派生；全 0 说明连候选都无。
STRICT = ["修复关系", "道歉", "对不起", "抱歉", "和好", "我刚才不该", "刚才是我",
          "主动承认", "重新连接", "跟他和好", "抱一抱"]
strict_hits = []
for c in chunks:
    for s in sentences(c["inject_text"]):
        for k in STRICT:
            if k in s:
                strict_hits.append((c["id"], k, s))
print("[Q1 严格信号] 主动修复关系词命中 =", len(strict_hits))
for eid, k, s in strict_hits:
    print("   %s | %s | %s" % (eid, k, s))

# ---------------------------------------------------------------- 6D.2 / Q2
print("")
print("=" * 78)
print("6D.2 / Q2：场景隔离实测")
print("=" * 78)

COMBOS = [
    ("parent", "frustration_escalation"),
    ("parent", "parent_escalation"),
    ("child", "frustration_escalation"),
    ("child", "parent_escalation"),
]

# (A) 代表性状态：真实调用 build.retrieve，打印命中 id
REP_STATE = {
    "task_phase": "执行", "attention_state": "drift", "ownership": "child-leading",
    "wm_load": 2, "consecutive_failures": 2, "consecutive_successes": 0,
    "parent_affect_level": "high",
}
print("--- (A) 代表性状态真实 retrieve ---")
for aud, sc in COMBOS:
    hits = build.retrieve(aud, sc, REP_STATE)
    ids = [h["id"] for h in hits]
    foreign = [i for i in ids if not (i.startswith("fes_") if sc == "frustration_escalation"
                                      else i.startswith("pc_"))]
    print("  (%s, %-24s) -> %d 命中 %s | 非本场景前缀=%s"
          % (aud, sc, len(ids), ids, foreign))

# (B) 全状态空间：遍历 10368 点，各自收集可达 id 全集，检查两两交叉
print("--- (B) 全状态空间（%d 点）可达集交叉检查 ---" % pe.STATE_POINT_COUNT)
reach = {combo: set() for combo in COMBOS}
for state in pe.iter_states():
    for combo in COMBOS:
        aud, sc = combo
        for c in chunks:
            if c["audience"] != aud or c["scenario"] != sc:
                continue
            if build.eval_predicate(c["when"], state):
                reach[combo].add(c["id"])
for combo in COMBOS:
    print("  (%s, %-24s) 可达=%d %s"
          % (combo[0], combo[1], len(reach[combo]), sorted(reach[combo])))
cross = []
for i, a in enumerate(COMBOS):
    for b in COMBOS[i + 1:]:
        ov = reach[a] & reach[b]
        if ov:
            cross.append((a, b, sorted(ov)))
print("  [交叉] 任意两组可达集交集 =", cross if cross else "空（无场景串扰）")

# (C) 场景字段一致性：pc_* / fes_* 的 scenario 分布
print("--- (C) chunk 场景字段一致性 ---")
for tag, pred in [("pc_*", lambda i: i.startswith("pc_")),
                  ("fes_*", lambda i: i.startswith("fes_"))]:
    dist = {}
    for c in chunks:
        if pred(c["id"]):
            dist.setdefault((c["audience"], c["scenario"]), []).append(c["id"])
    print("  %s -> %s" % (tag, {str(k): len(v) for k, v in dist.items()}))

# (D) router.route 场景收窄实测：既有辅导轨迹 vs scenario=None 边界
print("--- (D) router.route 场景收窄实测 ---")
GOLDEN = os.path.join(ROOT, "05_审核与运营", "regression", "golden_trajectories.jsonl")
trs = [json.loads(l) for l in open(GOLDEN, encoding="utf-8") if l.strip()]
via = [t for t in trs if t.get("entry_via")]
rest = [t for t in trs if not t.get("entry_via")]
print("  轨迹总数=%d  旁路=%d  走 router=%d" % (len(trs), len(via), len(rest)))
print("  走 router 的 scenario 集合 =", sorted({t.get("scenario") for t in rest}))
print("  其中 parent_escalation 条数 =",
      sum(1 for t in rest if t.get("scenario") == "parent_escalation"))
skills, rchunks = router.load_artifacts()
st = dict(REP_STATE)
for sc in [None, "frustration_escalation", "parent_escalation"]:
    d = router.route(st, "parent", sc, skills=skills, chunks=rchunks)
    inj = d["injected_chunks"]
    pc_in = [i for i in inj if i.startswith("pc_")]
    print("  route(scenario=%-24s) -> route=%-9s 注入=%d 其中 pc_*=%d %s"
          % (str(sc), d["route"], len(inj), len(pc_in),
             pc_in if pc_in else ""))

# (E) 边界灰区：router.route 的 in_scope 是
#     `scenario is None or rec.scenario == scenario` —— 没有辅导场景白名单，
#     scenario=None 时完全不收窄。传 skills=[] 强制走检索通道暴露真实行为。
print("--- (E) router 无场景白名单（skills=[] 强制检索通道）---")
for sc in [None, "frustration_escalation", "parent_escalation"]:
    d = router.route(st, "parent", sc, skills=[], chunks=rchunks)
    inj = d["injected_chunks"]
    pc_in = [i for i in inj if i.startswith("pc_")]
    fes_in = [i for i in inj if i.startswith("fes_")]
    print("  route(scenario=%-24s) -> %-9s 注入=%-2d pc_*=%d fes_*=%d"
          % (str(sc), d["route"], len(inj), len(pc_in), len(fes_in)))

# (F) handle_parent_escalation 实际调用的检索场景（Q2 第 2 点）
print("--- (F) handle_parent_escalation 实际检索场景 ---")
import importlib.util  # noqa: E402
spec = importlib.util.spec_from_file_location("_pc_server_6D", SERVER)
srv6d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(srv6d)
seen = []


def fake_retrieve(audience, scenario, state):
    seen.append((audience, scenario, dict(state)))
    return []


srv6d.handle_parent_escalation(3, "", retrieve_fn=fake_retrieve)
print("  retrieve 调用序列 =", seen)
print("  只查 parent_escalation =",
      len(seen) == 1 and seen[0][1] == "parent_escalation")

# ---------------------------------------------------------------- 6D.3 / Q3
print("")
print("=" * 78)
print("6D.3 / Q3：孩子状态感知的静态证据")
print("=" * 78)
src = open(SERVER, encoding="utf-8").read()
readme = open(README, encoding="utf-8").read()
import re  # noqa: E402
sig = re.search(r"def handle_parent_escalation\(([^)]*)\)", src)
print("  handle 签名 =", sig.group(1) if sig else "未找到")
print("  server.py 是否 import router =", bool(re.search(r"^\s*(import|from)\s+router\b", src, re.M)))
print("  server.py 是否出现 router.route =", "router.route" in src)
print("  server.py docstring 含「独立 scenario」 =", "独立 scenario" in src)
print("  server.py docstring 含「不与辅导状态机打架」 =", "不与辅导状态机打架" in src)
for kw in ["不感知孩子状态", "孩子状态", "辅导端"]:
    print("  README 含「%s」 = %s" % (kw, kw in readme))
print("  regression.py 含 entry_via 守卫 =",
      "entry_via 守卫" in open(os.path.join(COMPILE, "validators", "regression.py"),
                              encoding="utf-8").read())
print("")
print("probe done（只读，未修改任何文件）")
