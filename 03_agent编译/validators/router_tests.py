# -*- coding: utf-8 -*-
"""P2 路由判定器验收（本地纯函数，可脱离运行时验证）。

最小验收（用户给定）：
  1. skill 命中 → 该微步骤内检索静默（无重复支持）
  2. exit_when 满足 → 路由回落 none，不重复注入
  3. 均未命中 → 显式 none，不允许自由生成
  4. 儿童视图下 audience=parent 条目命中率 = 0
另加：
  5. 同源断言：router.eval_predicate is build.eval_predicate is _common.eval_predicate
     （防「两套条件判断」漂移，本轮最隐蔽的坑）
  6. 有限状态空间穷举：child view 全空间零角色泄漏 + skill 命中必静默
  7. 批次 6-E / PROP-0006：scenario=None 只命中辅导场景白名单。
     三条断言全部按可证伪设计——关键前提是 st() 默认状态不含
     parent_affect_level，pc_* 的 when 恒不命中，用默认状态会让
     「改前也绿」；故 E1 显式带 parent_affect_level=high
     （该状态下 6D 审计实测改前注入 11 条 / pc_*=2）。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, PARENT)
sys.path.insert(0, HERE)

import router
import build
from _common import eval_predicate as common_eval

TASK_PHASES = ["启动", "理解", "计划", "执行", "检查", "微休息"]
ATTN = ["on-task", "drift", "re-entry"]
OWNER = ["child-leading", "parent-hinting", "parent-taking-over"]


def st(tp="执行", attn="drift", owner="child-leading", wm=0, cf=0, cs=0,
       affect="neutral"):
    return {
        "task_phase": tp, "attention_state": attn, "ownership": owner,
        "wm_load": wm, "consecutive_failures": cf,
        "consecutive_successes": cs, "affect": affect,
    }


def run():
    errors = []
    checked = 0

    skills, chunks = router.load_artifacts()
    chunk_aud = {c["id"]: c["audience"] for c in chunks}
    skill_aud = {s["name"]: s["audience"] for s in skills}

    # ---- 5. 同源断言（最高优先，先验）----
    checked += 1
    if not (router.eval_predicate is build.eval_predicate is common_eval):
        errors.append("同源断言失败：router 未复用 build.py 的谓词求值函数对象")

    # ---- 1. skill 命中 → 检索静默 ----
    checked += 1
    d = router.route(st(cf=2), "parent", skills=skills, chunks=chunks)
    if d["route"] != "skill":
        errors.append(f"[1] 期望 skill，实际 {d['route']}（state={st(cf=2)}）")
    else:
        if not d["retrieval_silent"]:
            errors.append("[1] skill 命中但 retrieval_silent=False")
        # 注入通道只允许 audience=both 且 type=boundary 通过
        leaked = [cid for cid in d["injected_chunks"]
                  if chunk_aud.get(cid) != "both"]
        if leaked:
            errors.append(f"[1] skill 命中却注入了非边界块（重复支持）：{leaked}")

    # ---- 2. exit_when 满足 → none，不重复注入 ----
    checked += 1
    exit_state = st(attn="on-task", cs=2, cf=2)
    d = router.route(exit_state, "parent", active_skill="redirect_low_affect",
                     skills=skills, chunks=chunks)
    if d["route"] != "none":
        errors.append(f"[2] exit_when 满足却未回落 none，实际 {d['route']}")
    if "exit_when" not in d["reason"]:
        errors.append(f"[2] 回落原因未标注 exit_when：{d['reason']}")
    if d["injected_chunks"]:
        errors.append(f"[2] 撤除后仍注入了块：{d['injected_chunks']}")

    # 反例：exit_when 未满足时不应误撤除（cs 不足）
    checked += 1
    d = router.route(st(attn="on-task", cs=1, cf=2), "parent",
                     active_skill="redirect_low_affect",
                     skills=skills, chunks=chunks)
    if "exit_when satisfied" in d["reason"]:
        errors.append("[2b] consecutive_successes 未达阈值却误判撤除")

    # ---- 3. 均未命中 → 显式 none ----
    checked += 1
    no_hit = st(tp="微休息", attn="re-entry", owner="parent-taking-over", wm=0, cf=0)
    d = router.route(no_hit, "parent", skills=skills, chunks=chunks)
    if d["route"] != "none":
        errors.append(f"[3] 均未命中却未显式 none，实际 {d['route']} / {d['injected_chunks']}")
    if "no_scaffold" not in d["reason"]:
        errors.append(f"[3] 未标注 no_scaffold 禁止自由生成：{d['reason']}")

    # ---- 4 + 6. 有限状态空间穷举：角色零泄漏 / skill 静默 ----
    leak_hits = 0
    silent_violations = 0
    for tp in TASK_PHASES:
        for at in ATTN:
            for ow in OWNER:
                for wm in range(0, 4):
                    for cf in range(0, 4):
                        for cs in range(0, 4):
                            s = st(tp, at, ow, wm, cf, cs)
                            for view, allowed in (("child", {"child", "both"}),
                                                  ("parent", {"parent", "both"})):
                                checked += 1
                                dd = router.route(s, view, skills=skills, chunks=chunks)
                                # 角色泄漏：不允许的 audience 出现在命中里
                                for cid in dd["injected_chunks"]:
                                    if chunk_aud.get(cid) not in allowed:
                                        leak_hits += 1
                                if dd["skill"] and skill_aud.get(dd["skill"]) not in allowed:
                                    leak_hits += 1
                                # skill 命中必静默（仅 both+boundary 例外）
                                if dd["route"] == "skill" and not dd["retrieval_silent"]:
                                    silent_violations += 1
    if leak_hits:
        errors.append(f"[4/6] 状态空间内角色泄漏 {leak_hits} 次（要求 0）")
    if silent_violations:
        errors.append(f"[6] skill 命中未静默 {silent_violations} 次")

    # ---- 7 / 6E.3：辅导场景白名单（PROP-0006），checked +3 ----
    # 独立重算不使用 router.in_scope / scenario_in_scope，避免「用被测逻辑
    # 验证被测逻辑」的假绿；白名单来自 manifest，期望值来自 entry.yaml。
    import yaml as _yaml
    _root = os.path.abspath(os.path.join(PARENT, ".."))
    with open(os.path.join(_root, "agent_manifest.yaml"), encoding="utf-8") as _f:
        _manifest = _yaml.safe_load(_f) or {}
    with open(os.path.join(_root, "schema", "entry.yaml"), encoding="utf-8") as _f:
        _entry = _yaml.safe_load(_f) or {}
    _declared = _manifest.get("coaching_scenarios")
    _enum = set(_entry["fields"]["scenario"]["values"])
    _wl = router.load_coaching_scenarios()
    _allowed_parent = router.ALLOWED_AUDIENCE["parent"]

    def _expect(sc_filter, state):
        """独立重算期望注入集：audience 护栏 + 场景过滤 + 同源谓词。"""
        return [c["id"] for c in chunks
                if c["audience"] in _allowed_parent
                and sc_filter(c["scenario"])
                and c.get("when") and common_eval(c["when"], state)]

    # 关键：带 parent_affect_level 才能让 pc_* 在「改前」真实可达
    state6e = st(cf=2)
    state6e["parent_affect_level"] = "high"

    # E1：None 收窄到白名单，且注入集 == 独立重算的白名单并集（9 条）
    checked += 1
    d6e = router.route(state6e, "parent", None, skills=[], chunks=chunks)
    inj6e = d6e["injected_chunks"]
    pc6e = [cid for cid in inj6e if cid.startswith("pc_")]
    if pc6e:
        errors.append(f"[6E E1] scenario=None 串入非辅导场景块：{pc6e}")
    exp_union = _expect(lambda s: s in _wl, state6e)
    if sorted(inj6e) != sorted(exp_union):
        errors.append(f"[6E E1] None 注入集 ≠ 白名单并集："
                      f"多={sorted(set(inj6e) - set(exp_union))} "
                      f"少={sorted(set(exp_union) - set(inj6e))}")
    # manifest 声明 ≡ schema 枚举减 parent_escalation（防两处定义漂移）
    if not isinstance(_declared, list) or set(_declared) != _enum - {"parent_escalation"}:
        errors.append(f"[6E E1] manifest::coaching_scenarios 与 entry.yaml 枚举不一致：{_declared}")
    if set(_wl) != set(_declared or []):
        errors.append("[6E E1] router 加载的白名单与 manifest 声明不一致")

    # E2：None 仍命中辅导场景 + passthrough 同款收窄（构造块端到端）
    checked += 1
    if not any(cid.startswith("fes_") for cid in inj6e):
        errors.append("[6E E2] scenario=None 未命中任何辅导场景条目（收窄过头）")
    if router.scenario_in_scope("parent_escalation", None, _wl):
        errors.append("[6E E2] 白名单仍放行 parent_escalation")
    if not router.scenario_in_scope("task_initiation", None, _wl):
        errors.append("[6E E2] 白名单误挡辅导场景 task_initiation")
    # 构造 audience=both & type=boundary 的探针块：skill 命中态下走 passthrough。
    # 改前（无白名单）probe_bad 会被注入，改后不应注入；probe_ok 作正向对照。
    probe_bad = dict(chunks[0], id="_6e_probe_parent_escalation",
                     audience="both", type="boundary", scenario="parent_escalation")
    probe_ok = dict(chunks[0], id="_6e_probe_coaching",
                    audience="both", type="boundary", scenario="frustration_escalation")
    d_pt = router.route(st(cf=2), "parent", None, skills=skills,
                        chunks=chunks + [probe_bad, probe_ok])
    if d_pt["route"] != "skill":
        errors.append(f"[6E E2] 探针未进入 skill 分支（{d_pt['route']}），passthrough 未覆盖")
    else:
        if "_6e_probe_parent_escalation" in d_pt["injected_chunks"]:
            errors.append("[6E E2] passthrough 串入非辅导 boundary 块")
        if "_6e_probe_coaching" not in d_pt["injected_chunks"]:
            errors.append("[6E E2] passthrough 误挡辅导 boundary 块（正向对照失败）")

    # E3：具体 scenario 行为不变（5 个辅导 scene 精确比对 + 显式家长场景不堵死）
    checked += 1
    for sc6e in sorted(_wl):
        exp_sc = _expect(lambda s, _sc=sc6e: s == _sc, state6e)
        got_sc = router.route(state6e, "parent", sc6e,
                              skills=[], chunks=chunks)["injected_chunks"]
        if sorted(got_sc) != sorted(exp_sc):
            errors.append(f"[6E E3] scenario={sc6e} 注入集与精确匹配期望不符："
                          f"{sorted(got_sc)} ≠ {sorted(exp_sc)}")
    d_pe = router.route(state6e, "parent", "parent_escalation",
                        skills=[], chunks=chunks)
    pe_hits = [cid for cid in d_pe["injected_chunks"] if cid.startswith("pc_")]
    # 批次 8：新增 6 条 pc_*（修复卡 + 五类预警，source_id 非 parent_cool，
    # when 三档全命中）后，显式 parent_escalation 查询命中数 2 → 8。
    # 断言语义不变：白名单不误堵显式查询。期望值用 _expect 独立重算
    # （与 E1 同款逻辑），不硬编码数字。
    pe_expected = sorted(
        c["id"] for c in chunks
        if c["scenario"] == "parent_escalation"
        and c["audience"] in _allowed_parent
        and c.get("when") and common_eval(c["when"], state6e)
        and c["id"].startswith("pc_"))
    if sorted(pe_hits) != pe_expected:
        errors.append(f"[6E E3] 白名单误堵显式 parent_escalation 查询："
                      f"pc_*={sorted(pe_hits)}（应 {pe_expected}）")

    return (len(errors) == 0, errors, checked)


def main():
    ok, errors, checked = run()
    print(f"[router_tests] 断言/状态点数={checked}  失败={len(errors)}")
    for e in errors[:20]:
        print("  ✗", e)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
