# -*- coding: utf-8 -*-
"""CI 规则（组件）：predicate_equiv — 同一 when 的「注入过滤条件」与
「skill 触发条件」等价性断言。在有限状态空间上穷举验证，防止两条通道条件漂移。

实现：用 _common.compile_predicate 作为 skill 触发条件（规范表示），
并重写一份**独立**的注入过滤编译（filter_compile），两者在全部可达
state 上求值必须完全一致。独立重写确保 build.py 若只改了一边也不会漏过。

阶段 A · 2.5b (2026-11-13)：状态空间增 parent_affect_level 三档（3456
→ 10368 状态点），run() 与 _state_points() 共用 iter_states() 单一来源，
并新增 precheck() 验证「两套求值 + 新维度确实参与求值」。当前无条目引用
新字段，故既有等价性结论不变，只有 checked 从 62208 → 186624。
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from _common import iter_entries, compile_predicate, eval_predicate

CMP_RE = __import__("re").compile(r"^(>=|<=|>|<|==|!=)\s*(\d+)$")

TASK_PHASES = ["启动", "理解", "计划", "执行", "检查", "微休息"]
ATTN = ["on-task", "drift", "re-entry"]
OWNER = ["child-leading", "parent-hinting", "parent-taking-over"]

# ---------------------------------------------------------------------
# 阶段 A · 2.5b（2026-11-13）：为阶段 B 的 parent_affect_level 铺路。
# 当前没有任何条目引用该字段，所以扩维度**不改变任何既有条目的等价性
# 结论**，只把状态点基数 ×3（3456 → 10368）；run() 的 checked 因此从
# 62208 → 186624。阶段 B 的 PROP-0004 落地后无需再动本文件。
#
# 单一状态空间来源：run()（过滤侧 + 触发侧）、_state_points()（diff_mode
# 用）必须共用 iter_states()。若各自维护一份六/七重循环，就会出现
# 「过滤侧有新维度、求值侧没有」的假绿 —— 与 P2 同源契约同级的坑。
# diff_mode 不持有维度列表，它只调 _state_points()，故自动同步。
# ---------------------------------------------------------------------
PARENT_AFFECT = ["low", "mid", "high"]


def iter_states():
    """穷举全部可达状态（含 parent_affect_level 三档）。唯一来源。"""
    for tp in TASK_PHASES:
        for at in ATTN:
            for ow in OWNER:
                for wm in range(0, 4):
                    for cf in range(0, 4):
                        for cs in range(0, 4):
                            for pa in PARENT_AFFECT:
                                yield {
                                    "task_phase": tp,
                                    "attention_state": at,
                                    "ownership": ow,
                                    "wm_load": wm,
                                    "consecutive_failures": cf,
                                    "consecutive_successes": cs,
                                    "parent_affect_level": pa,
                                }


STATE_POINT_COUNT = (len(TASK_PHASES) * len(ATTN) * len(OWNER)
                     * 4 * 4 * 4 * len(PARENT_AFFECT))  # 10368


def filter_compile(when):
    """独立实现的注入过滤编译（与 _common.compile_predicate 分离）。"""
    out = {}
    if not when:
        return out
    for field, val in when.items():
        if isinstance(val, list):
            out[field] = ("in", list(val))
        elif isinstance(val, str) and CMP_RE.match(val):
            op, num = CMP_RE.match(val).groups()
            out[field] = (op, int(num))
        else:
            out[field] = ("==", val)
    return out


def filter_eval(pred, state):
    for field, (op, target) in pred.items():
        if field not in state:
            return False
        sv = state[field]
        if op == "in":
            if sv not in target:
                return False
        else:
            try:
                svi, tv = int(sv), int(target)
            except Exception:
                return False
            table = {"==": svi == tv, "!=": svi != tv, ">": svi > tv,
                     "<": svi < tv, ">=": svi >= tv, "<=": svi <= tv}
            if not table[op]:
                return False
    return True


def precheck():
    """2.5b 前置小测试：扩维度前先确认两套求值对新字段的行为一致，
    不把问题留到阶段 B。三条可证伪断言：

      ① state 含 parent_affect_level 但谓词不引用 → 两套求值都忽略该字段，
        三档下结果完全一致（新维度不污染既有结论）；
      ② filter_eval 与 eval_predicate 在三档上逐点一致（无「两套条件漂移」）；
      ③ 引用该字段的谓词确实能被分别求值（low/mid/high 各自命中），
        证明新维度真的接上了，而不是空转常量。

    返回 (ok, errors, checked)。checked **不并入 run()**，保证 run().checked
    精确等于「状态点数 × 含 when 的条目数」（2.5b 后应为 186624）。
    """
    errors = []
    checked = 0
    base = {"task_phase": "执行", "attention_state": "drift",
            "ownership": "child-leading", "wm_load": 2,
            "consecutive_failures": 1, "consecutive_successes": 0}
    when = {"attention_state": ["drift"], "wm_load": ">=2"}
    trig = compile_predicate(when)
    flt = filter_compile(when)

    results = []
    for pa in PARENT_AFFECT:
        state = {**base, "parent_affect_level": pa}
        checked += 1
        fv, ev = filter_eval(flt, state), eval_predicate(trig, state)
        if fv != ev:
            errors.append(f"pa={pa}: 过滤侧={fv} 触发侧={ev} 不一致（两套求值漂移）")
        if not ev:
            errors.append(f"pa={pa}: 既有谓词应恒为真，实际 {ev}（新维度污染旧求值）")
        results.append(ev)
    if len(set(results)) != 1:
        errors.append(f"三档取值改变了不引用该字段的谓词结果：{results}")

    for pa in PARENT_AFFECT:
        checked += 1
        state = {**base, "parent_affect_level": pa}
        only = {"parent_affect_level": {"op": "in", "values": [pa]}}
        others = {"parent_affect_level": {"op": "in", "values":
                                          [x for x in PARENT_AFFECT if x != pa]}}
        if not eval_predicate(only, state) or eval_predicate(others, state):
            errors.append(f"pa={pa}: parent_affect_level 未被正确求值（维度未接上）")
    return (len(errors) == 0, errors, checked)


def run():
    errors = []
    checked = 0
    entries = iter_entries()  # 预加载，避免状态空间内层重复读盘

    # 2.5b 前置小测试：失败并入 errors（阻断），但 checked 不并入，
    # 使「状态点数 × 条目数」的计数保持可解释。
    ok_pc, errs_pc, _ = precheck()
    if not ok_pc:
        errors.extend(f"[2.5b precheck] {e}" for e in errs_pc)

    # 遍历全状态空间：唯一来源 iter_states()，过滤侧与触发侧共用。
    for state in iter_states():
        for _path, fm, _b in entries:
            when = fm.get("when")
            if not when:
                continue
            checked += 1
            trig = compile_predicate(when)
            flt = filter_compile(when)
            if filter_eval(flt, state) != eval_predicate(trig, state):
                errors.append(
                    f"[{fm['id']}] 状态{tuple(state.items())}"
                    f" 过滤={filter_eval(flt,state)} 触发={eval_predicate(trig,state)} 不一致"
                )
    return (len(errors) == 0, errors, checked)


def _state_points(predicates):
    """把一组谓词在有限状态空间上求值，返回「为真的状态点集合」。

    predicates: list[dict]，每个 dict 是 compile_predicate 规范表示
                 （或等价结构，字段为 op/value）。
    state_point 用 tuple(sorted(state.items())) 表示。
    """
    points = set()
    # 2.5b：与 run() 共用 iter_states()，维度自动同步；diff_mode 因此
    # 无需自己维护维度列表，scope_change 计算逻辑保持不变。
    for state in iter_states():
        for pred in predicates:
            if eval_predicate(pred, state):
                points.add(tuple(sorted(state.items())))
                break
    return points


def diff_mode(old_predicates, new_predicates, affected_entries=None):
    """状态空间 diff（扩展提案预检用）。

    输入两组谓词集合（list[dict]，compile_predicate 规范表示），在有限状态
    空间上穷举，输出「为真状态点集合」的差异 + 受影响条目的触发范围变化。

    affected_entries: list[dict]，形如 {"id":..., "pred":...}，用于计算每个
                     受影响条目的 scope_change。缺省时 scope_change 为
                     "unchanged"（无法判定单条目）。

    返回：
      {
        "state_points_before": int,
        "state_points_after":  int,
        "added":   list[tuple],   # 新增状态点 (field, value) 对
        "removed": list[tuple],   # 删除状态点
        "affected_entries": list[str],
        "scope_change": "narrowed | widened | unchanged",
      }

    本函数是独立新增，不改动 run() 的穷举等价验证逻辑。
    2.5b：状态空间由 iter_states() 单一来源提供（含 parent_affect_level
    三档），本函数不持有维度列表，故维度扩展时无需改动本函数。
    """
    before = _state_points(old_predicates)
    after = _state_points(new_predicates)

    added = sorted(after - before)
    removed = sorted(before - after)

    entry_ids = []
    scope = "unchanged"
    if affected_entries:
        entry_ids = [e["id"] for e in affected_entries]
        # 每个受影响条目：旧谓词为真状态点 vs 新谓词为真状态点
        narrowed = widened = False
        for e in affected_entries:
            ob = _state_points([e["pred"]])
            nb = _state_points([e.get("new_pred", e["pred"])])
            if nb < ob:
                narrowed = True
            elif nb > ob:
                widened = True
        if narrowed and not widened:
            scope = "narrowed"
        elif widened and not narrowed:
            scope = "widened"
        elif narrowed and widened:
            scope = "widened"  # 有宽有窄时，取更危险的「widened」提示关注
        else:
            scope = "unchanged"

    return {
        "state_points_before": len(before),
        "state_points_after": len(after),
        "added": added,
        "removed": removed,
        "affected_entries": entry_ids,
        "scope_change": scope,
    }


def main():
    ok_pc, errs_pc, n_pc = precheck()
    print(f"[predicate_equiv] precheck: ok={ok_pc}  断言={n_pc}  错误={len(errs_pc)}")
    ok, errors, checked = run()
    print(f"[predicate_equiv] 状态点={STATE_POINT_COUNT}  "
          f"状态空间断言次数={checked}  不一致={len(errors)}")
    for e in errors[:20]:
        print("  ✗", e)
    sys.exit(0 if ok and ok_pc else 1)


if __name__ == "__main__":
    main()
