# 批次 6A.1 只读审计脚本：打印每档 candidates 顺序、overlap 值、first id。
# 只读，不写任何产物；可复跑。
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "03_agent编译")))
import build  # noqa: E402

for lv in ("low", "mid", "high"):
    state = {"parent_affect_level": lv}
    cands = build.retrieve("parent", "parent_escalation", state)
    q = " ".join(str(v) for v in state.values())
    print(f"--- {lv}  q={q!r}  n={len(cands)}")
    for i, c in enumerate(cands):
        ov = build.overlap(q, c["inject_text"])
        first = c["inject_text"].split("。")[0][:30]
        print(f"  [{i}] {c['id']}  overlap={ov}  first={first}")

# situation 不进 state 的对照证明：换 situation 不会改变 retrieve 结果
# （situation 只传给 assemble，assemble 不用它）。此处直接演示同档两种
# situation 下 assemble 输出一致性由 6A.3 断言锁定，本脚本不重复。
print("audit-print done")
