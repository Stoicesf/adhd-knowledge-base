# -*- coding: utf-8 -*-
"""阶段六 · P4 轨迹回归框架（本地版，闭环；真实轨迹采样挂部署后）

读 05_审核与运营/regression/golden_trajectories.jsonl
→ 逐 turn 用 router.route 判定（携带 active_skill 状态延续）
→ 与 expected 比对 → 轨迹级指标 → 逐条对比报告

两轨迹类型：
  conformance : 期望=当前设计契约行为，不一致 = 失败（CI 阻断）
  diagnostic  : 期望=理想行为，不一致 = **识别出的过度介入/撤除缺口**（不阻断，记录基线）

指标（P4 §4.2，除 guardrail 漏放率由 P3 guardrail_tests 覆盖）：
  支架调用准确率 / 过早介入率 / 撤除率 / 角色泄漏率 / 恢复延迟代理指标

v1.1 (2026-11-13)：expected 支持 scaffold_level 断言（降级支架）。
v1.2 (2026-11-13，阶段三首批派生)：expected 支持 injected_contains 断言，
  让解释性条目（无 callable）轨迹能绑到具体块 id，避免「有东西命中」的假覆盖。
v1.3 (2026-11-13，阶段 B 批次 3 · PROP-0005)：支持
  entry_via: "parent_escalation" 旁路分支。家长情绪是独立 scenario，
  运行期走 server.handle_parent_escalation()，**不调 router.route()**；
  本框架用 router.eval_predicate（同源契约）直接过滤 parent_escalation
  检索块，使新轨迹可回归，同时用 _entry_branch_guard() 断言既有 25 条
  轨迹一律走原分支、行为零变化。
"""
import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(PARENT, ".."))
sys.path.insert(0, PARENT)
sys.path.insert(0, HERE)

import router

TRAJ_PATH = os.path.join(ROOT, "05_审核与运营", "regression", "golden_trajectories.jsonl")
REPORT_PATH = os.path.join(ROOT, "05_审核与运营", "regression", "回归报告.md")

ALLOWED = {"child": {"child", "both"}, "parent": {"parent", "both"}}
EXPECTED_VIA_TRAJECTORIES = 6


def _escalation_decision(state, view, chunks):
    """entry_via=parent_escalation 的旁路判定（v1.3）。

    复用 router.eval_predicate（= build = _common 同一对象），不另写条件
    判断，也不 import 09_家长端工具/ 的 server，避免编译管线反向依赖工具层。
    返回与 router._decision 同结构的 dict，使 _match() 的既有断言全部可用。
    """
    allowed = ALLOWED[view]
    hits = []
    for c in chunks:
        if c.get("audience") not in allowed:
            continue
        if c.get("scenario") != "parent_escalation":
            continue
        cond = c.get("when") or {}
        if cond and router.eval_predicate(cond, state):
            hits.append(c["id"])
    return {
        "route": "retrieve" if hits else "none",
        "view": view,
        "state": dict(state),
        "skill": None,
        "injected_chunks": hits,
        "retrieval_silent": not hits,
        "scaffold_level": None,
        "reason": ("entry_via=parent_escalation：结构化谓词过滤命中检索块"
                   "（旁路，不调 router.route）" if hits else
                   "entry_via=parent_escalation：无命中，显式无支架"),
    }


def _entry_branch_guard(trajectories):
    """可证伪断言：旁路分支不得污染既有 25 条轨迹（v1.3）。

    返回错误列表，并入 evaluate().errors；不是静默跳过。
    """
    errs = []
    via = [tr for tr in trajectories if tr.get("entry_via")]
    rest = [tr for tr in trajectories if not tr.get("entry_via")]
    if len(via) != EXPECTED_VIA_TRAJECTORIES:
        errs.append(f"[entry_via 守卫] 旁路轨迹应为 {EXPECTED_VIA_TRAJECTORIES} 条，实际 {len(via)}")
    for tr in via:
        tid = tr.get("trajectory_id", "?")
        if tr.get("entry_via") != "parent_escalation":
            errs.append(f"[{tid}] 未知 entry_via={tr.get('entry_via')}")
        if tr.get("scenario") != "parent_escalation":
            errs.append(f"[{tid}] 旁路轨迹 scenario 必须是 parent_escalation")
        if tr.get("view") != "parent":
            errs.append(f"[{tid}] 旁路轨迹 view 必须是 parent（家长自救不进儿童视图）")
        if tr.get("type") != "conformance":
            errs.append(f"[{tid}] 旁路轨迹必须是 conformance")
    polluted = [tr.get("trajectory_id") for tr in rest
                if tr.get("scenario") == "parent_escalation"]
    if polluted:
        errs.append(f"[entry_via 守卫] 非旁路轨迹却使用 parent_escalation：{polluted}")
    # 既有 25 条一律走 router.route 原分支；数量下降即说明既有轨迹被误删
    if len(rest) != 25:
        errs.append(f"[entry_via 守卫] 既有轨迹应为 25 条，实际 {len(rest)}")
    return errs


def _load():
    with open(TRAJ_PATH, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def _match(expected, decision):
    """返回 (是否一致, 差异说明列表)。"""
    diff = []
    if "route" in expected and decision["route"] != expected["route"]:
        diff.append(f"route 期望 {expected['route']} ≠ 实际 {decision['route']}")
    if "skill" in expected and decision["skill"] != expected["skill"]:
        diff.append(f"skill 期望 {expected['skill']} ≠ 实际 {decision['skill']}")
    if "reason_contains" in expected and expected["reason_contains"] not in decision["reason"]:
        diff.append(f"reason 应含 '{expected['reason_contains']}'，实际 '{decision['reason']}'")
    if expected.get("skill_is_none") and decision["skill"] is not None:
        diff.append(f"应无 skill，实际 {decision['skill']}")
    if expected.get("injected_not_empty") and not decision["injected_chunks"]:
        diff.append("应注入检索块，实际为空")
    # v1.2（阶段三首批派生）：解释性条目无 callable，轨迹必须能绑到具体块 id，
    # 否则只断言「有东西命中」等于没覆盖新条目。added by PROP-0003 批次。
    if ("injected_contains" in expected
            and expected["injected_contains"] not in decision["injected_chunks"]):
        diff.append(f"应注入检索块 {expected['injected_contains']}，"
                    f"实际 {decision['injected_chunks']}")
    if expected.get("injected_empty") and decision["injected_chunks"]:
        diff.append(f"注入通道应静默，实际 {decision['injected_chunks']}")
    # v1.1：降级支架强度断言（用户 2026-11-13 裁决 D2 走降级语义）
    if "scaffold_level" in expected and decision.get("scaffold_level") != expected["scaffold_level"]:
        diff.append(f"scaffold_level 期望 {expected['scaffold_level']} ≠ 实际 {decision.get('scaffold_level')}")
    return (len(diff) == 0, diff)


def evaluate():
    trajectories = _load()
    skills, chunks = router.load_artifacts()
    chunk_aud = {c["id"]: c["audience"] for c in chunks}
    skill_aud = {s["name"]: s["audience"] for s in skills}

    records = []
    errors = []
    checked = 0

    # v1.3：旁路分支守卫（失败即阻断，可证伪，不是静默跳过）
    errors.extend(_entry_branch_guard(trajectories))

    # 指标累加器
    m = {
        "turns": 0, "conf_turns": 0, "conf_pass": 0,
        "skill_expected": 0, "skill_correct": 0,
        "exit_expected": 0, "exit_correct": 0,
        "independent_turns": 0, "premature": 0,
        "role_leak": 0, "drift_to_recovery": [],
        "diagnostic": [],
    }

    for tr in trajectories:
        view = tr["view"]
        allowed = ALLOWED[view]
        active_skill = None
        turns_rec = []
        drift_turn = None

        for t in tr["turns"]:
            checked += 1
            m["turns"] += 1
            state = t["state"]
            # v1.3：家长情绪走旁路；其余 25 条轨迹仍 100% 走 router.route()
            if tr.get("entry_via") == "parent_escalation":
                d = _escalation_decision(state, view, chunks)
            else:
                d = router.route(state, view, tr.get("scenario"),
                                 active_skill=active_skill,
                                 skills=skills, chunks=chunks)
            ok, diff = _match(t["expected"], d)

            # 角色泄漏（全 turn 无差别检查，含 diagnostic）
            leaked = [cid for cid in d["injected_chunks"]
                      if chunk_aud.get(cid) not in allowed]
            if d["skill"] and skill_aud.get(d["skill"]) not in allowed:
                leaked.append(f"skill:{d['skill']}")
            m["role_leak"] += len(leaked)

            # 支架调用准确率
            if t["expected"].get("route") == "skill":
                m["skill_expected"] += 1
                if ok:
                    m["skill_correct"] += 1
            # 撤除率
            if "exit_when" in str(t["expected"].get("reason_contains", "")):
                m["exit_expected"] += 1
                if d["route"] == "none" and "exit_when" in d["reason"]:
                    m["exit_correct"] += 1
            # 过早介入率：孩子仍可独立推进（on-task / 连续成功≥2 / 无失败）却注入支架
            independent = (state.get("attention_state") == "on-task"
                           and state.get("consecutive_successes", 0) >= 2
                           and state.get("consecutive_failures", 0) == 0)
            if independent:
                m["independent_turns"] += 1
                if d["route"] != "none":
                    m["premature"] += 1
            # 恢复延迟代理：drift → on-task/re-entry 的轮次差
            if state.get("attention_state") == "drift" and drift_turn is None:
                drift_turn = t["turn"]
            if drift_turn is not None and state.get("attention_state") in ("on-task", "re-entry"):
                m["drift_to_recovery"].append(t["turn"] - drift_turn)
                drift_turn = None

            if tr["type"] == "conformance":
                m["conf_turns"] += 1
                if ok:
                    m["conf_pass"] += 1
                else:
                    errors.append(f"[{tr['trajectory_id']}] turn{t['turn']}: " + "; ".join(diff))
            else:
                if not ok:
                    m["diagnostic"].append({
                        "id": tr["trajectory_id"], "turn": t["turn"],
                        "note": tr.get("note", ""),
                        "expected": t["expected"], "actual_route": d["route"],
                        "actual_reason": d["reason"],
                        "actual_injected": d["injected_chunks"], "diff": diff,
                    })

            # active_skill 状态延续：命中 skill 则激活；撤除则清空
            if d["route"] == "skill" and d["skill"]:
                active_skill = d["skill"]
            elif d["route"] == "none" and "exit_when" in d["reason"]:
                active_skill = None

            turns_rec.append({
                "turn": t["turn"], "ok": ok, "diff": diff,
                "expected_route": t["expected"].get("route", "—"),
                "route": d["route"], "skill": d["skill"],
                "scaffold_level": d.get("scaffold_level"),
                "injected": d["injected_chunks"], "reason": d["reason"],
                "reason_assert": t["expected"].get("reason_contains"),
                "leaked": leaked,
            })

        records.append({**{k: tr[k] for k in ("trajectory_id", "type", "view", "scenario", "note")},
                        "turns": turns_rec})

    conf_n = sum(1 for t in trajectories if t["type"] == "conformance")
    diag_n = len(trajectories) - conf_n
    metrics = {
        "trajectory_count": len(trajectories),
        "conformance_count": conf_n,
        "diagnostic_count": diag_n,
        "conformance_turns": m["conf_turns"],
        "conformance_pass": m["conf_pass"],
        "conformance_pass_rate": (m["conf_pass"] / m["conf_turns"] if m["conf_turns"] else 0),
        "skill_call_accuracy": (m["skill_correct"] / m["skill_expected"] if m["skill_expected"] else None),
        "withdrawal_rate": (m["exit_correct"] / m["exit_expected"] if m["exit_expected"] else None),
        "premature_intervention": f"{m['premature']}/{m['independent_turns']}",
        "role_leak_count": m["role_leak"],
        "recovery_lag_avg": (sum(m["drift_to_recovery"]) / len(m["drift_to_recovery"])
                             if m["drift_to_recovery"] else None),
        "diagnostic_identified": len(m["diagnostic"]),
    }
    return {"ok": len(errors) == 0, "errors": errors, "checked": checked,
            "records": records, "metrics": metrics, "diagnostic": m["diagnostic"]}


def write_report(result, path=REPORT_PATH):
    r = result
    mtr = r["metrics"]
    L = []
    L.append("# 阶段六 · P4 轨迹回归报告（本地版）\n")
    L.append("> 运行方式：`E:/ANACONDA/python.exe 03_agent编译/validators/regression.py`\n")
    L.append(f"> 输入：`golden_trajectories.jsonl`（{mtr['trajectory_count']} 条 = "
             f"{mtr['conformance_count']} conformance + {mtr['diagnostic_count']} diagnostic）\n")
    L.append("> 判定器：`03_agent编译/router.py`（复用 build.py 同一谓词求值函数）\n")
    L.append("> 边界：本框架为本地闭环；**真实 agent 轨迹采样挂部署后**。\n")
    L.append("> v1.3（阶段 B 批次 3）：`entry_via: parent_escalation` 的 6 条轨迹走"
             "旁路判定（复用 router.eval_predicate，不调 router.route）；"
             "既有 25 条一律走原分支，`_entry_branch_guard()` 逐条断言，失败即阻断。\n")
    L.append("\n## 一、基线指标（可复现，不要求第一版达标）\n")
    L.append("| 指标 | 本轮基线 | 目标方向 |")
    L.append("|---|---|---|")
    L.append(f"| 轨迹数 | {mtr['trajectory_count']}（{mtr['conformance_count']} conformance + "
             f"{mtr['diagnostic_count']} diagnostic） | ≥15 起步，新增来源批次后递增 ✓ |")
    L.append(f"| conformance 通过率 | {mtr['conformance_pass']}/{mtr['conformance_turns']} "
             f"({mtr['conformance_pass_rate']*100:.1f}%) | ↑ |")
    acc = mtr["skill_call_accuracy"]
    acc_s = f"{acc*100:.1f}%" if acc is not None else "N/A"
    L.append(f"| 支架调用准确率 | {acc_s} | ↑ |")
    wd = mtr["withdrawal_rate"]
    wd_s = f"{wd*100:.1f}%" if wd is not None else "N/A"
    L.append(f"| 撤除率 | {wd_s} | ↑ |")
    L.append(f"| 过早介入率 | {mtr['premature_intervention']} | ↓ |")
    L.append(f"| 角色泄漏率 | {mtr['role_leak_count']} 次 | → 0 |")
    lag = mtr["recovery_lag_avg"]
    lag_s = f"{lag:.2f} 轮" if lag is not None else "N/A"
    L.append(f"| 恢复延迟代理 | {lag_s} | ↓ |")
    L.append("| guardrail 漏放率 | 见 P3 `guardrail_tests` 报告 | → 0 |")
    L.append(f"| 未解决的诊断案例 | {mtr['diagnostic_identified']} 个 | 已回写，见 §4 |")

    L.append("\n## 二、逐条对比\n")
    L.append("| 轨迹 | 类型 | 视图 | turn | 期望 route | 实际 route | 一致 |")
    L.append("|---|---|---|---|---|---|---|")
    for rec in r["records"]:
        for t in rec["turns"]:
            mark = "✓" if t["ok"] else ("⚠ 诊断" if rec["type"] == "diagnostic" else "✗")
            L.append(f"| {rec['trajectory_id']} | {rec['type']} | {rec['view']} | {t['turn']} "
                     f"| {t['expected_route']} | {t['route']} | {mark} |")

    L.append("\n## 三、未解决的诊断轨迹\n")
    if not r["diagnostic"]:
        L.append("无。上一轮识别的 3 个缺陷已按 2026-11-13 裁决全部回写，见 §4。")
    for i, d in enumerate(r["diagnostic"], 1):
        L.append(f"### 案例 {i}：{d['id']} · turn {d['turn']}")
        L.append(f"- 场景：{d['note']}")
        L.append(f"- 期望：`{json.dumps(d['expected'], ensure_ascii=False)}`")
        L.append(f"- 实际：route=`{d['actual_route']}`，reason=`{d['actual_reason']}`，"
                 f"注入=`{d['actual_injected']}`")
        L.append(f"- 差异：{'；'.join(d['diff'])}")
        L.append("")

    L.append("\n## 四、已回写的调整（2026-11-13 用户裁决，本轮执行）\n")
    L.append("| 案例 | 裁决 | 落地 |")
    L.append("|---|---|---|")
    L.append("| tr_D1 过度介入 | **内容层**：改源条目 `when`，不走 router 静默 | 4 个解释性块 `when` 增 "
             "`attention_state: [drift, re-entry]`（知识缺口代理信号，排除 `on-task`） |")
    L.append("| tr_D3 过度介入 | **内容层**：同上 | 4 个解释性块 `when` 增 "
             "`ownership: [child-leading, parent-hinting]`（排除 `parent-taking-over`） |")
    L.append("| tr_D2 撤除边界 | **降级支架**（非撤除、非 `exit_when` 加 re-entry） | 新增 "
             "`parent_reentry_light_01`（`scaffold_level: light`，re-entry 只给完成信号）；"
             "`schema/entry.yaml` 升 v1.1；router 只通用透传字段，不另写条件 |")
    L.append("\n**联动期望复核**（因解释块 `when` 收窄，以下 conformance 期望同步更新，非放宽断言）："
             "`tr_011`、`tr_012` turn2 由 `retrieve` 改为 `none/no_scaffold`；"
             "`build.py::selftest` 第 5 项检索输入由 `on-task` 改为 `re-entry`。"
             "逐条改前→改后见 `阶段六_本地验证总报告.md` §五。\n")
    L.append("> 降级条件（`when`/`exit_when`）只写在源条目里；`router.py` 不含任何状态判断，"
             "同源契约断言 `router ≡ build ≡ _common` 仍成立。\n")

    # 复查点 3（2026-11-13）：触发路径断言注记，从轨迹集动态统计，重跑可复现
    ra = [(rec["trajectory_id"], t["turn"], t.get("reason_assert"))
          for rec in r["records"] for t in rec["turns"] if t.get("reason_assert")]
    d2 = [x for x in ra if x[0] == "tr_D2" and x[1] == 2]
    d2_state = (f"`{d2[0][2]}` ✓" if d2 else "**缺失 ✗**")
    L.append("\n> **触发路径断言（复查点 3，2026-11-13 补）**：`tr_D2` turn2 补 "
             "`reason_contains: \"skill trigger_condition 命中\"`，取自 `router.py` skill 命中分支的 "
             "reason 字面量，可同时排除 `no_scaffold` / `exit_when` 两条错误路径；"
             f"本轮共 {len(ra)} 个 turn 带 `reason_contains` 断言，其中 tr_D2 turn2 = {d2_state}。"
             "本注记由 `write_report()` 从轨迹集动态生成，重跑可复现，非手写静态文本。\n")

    L.append("\n## 五、复现与门控\n")
    L.append("- 单命令：`E:/ANACONDA/python.exe 03_agent编译/verify_all.py`")
    L.append("- CI 门控（部署后启用）：conformance 通过率 <100%、角色泄漏率 >0、"
             "过早介入率上升 → 阻断合并（配置见 `03_agent编译/ci/agent-ci.yml`，本轮不启用）。")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    return path


def run():
    r = evaluate()
    return (r["ok"], r["errors"], r["checked"])


def main():
    r = evaluate()
    print(f"[regression] 轨迹={r['metrics']['trajectory_count']}  turn 断言={r['checked']}  "
          f"conformance={r['metrics']['conformance_pass']}/{r['metrics']['conformance_turns']}  "
          f"诊断案例={r['metrics']['diagnostic_identified']}  角色泄漏={r['metrics']['role_leak_count']}")
    for e in r["errors"][:20]:
        print("  ✗", e)
    p = write_report(r)
    print(f"[regression] 报告写出：{p}")
    sys.exit(0 if r["ok"] else 1)


if __name__ == "__main__":
    main()
