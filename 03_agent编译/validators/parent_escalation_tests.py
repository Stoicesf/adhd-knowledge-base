# -*- coding: utf-8 -*-
"""阶段 B 批次 3 · verify_all 第 14 组：parent_escalation 契约验收

对应方案 3c 四项，另补四项「不假合规」断言：
  ① 三档映射：ANGER_TIER 1—5 → low/mid/high（覆盖 2/4 边界）+ 非法入参
  ② 三档真实 build.retrieve 命中（批次 5 起条目 when 单档化，分布 2/2/2）
  ②' 三档输出差异化：火气 1/3/5 的 line 两两不同（D-06 关闭证据）
  ②'' 检索确定性（批次 6A）：每档 first id 固定 + situation 不影响输出
  ③ guardrail block → fallback；line 与 steps 各自过 judge
  ④ degraded（条目未派生/服务不可用）与 blocked（护栏拦截）严格分开
  ⑤ when 白名单：schema_check.py 不校验嵌套 allowed_fields，本组显式兜住
  ⑥ 不编造：6 条新 inject_text 每句都是存量 18 条的逐字子串
  ⑦ 豁免口径：params_exempt 按条目计数=N，豁免模板种类=1（不凑「0→1」）
  ⑧ 既有 18 条触发范围 unchanged、两套求值一致
  ⑨ 批次 6D Q3：设计意图锁定——handle_parent_escalation 不调 router.route()

跨层说明：server.py 位于 09_家长端工具/，用 importlib 按文件路径加载，
不把工具目录永久加入 sys.path；server 自身 import build / guardrail_node，
仍复用编译管线同一份实现（同源契约不变）。
"""
import os
import sys
import json
import importlib.util

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(PARENT, ".."))
sys.path.insert(0, PARENT)
sys.path.insert(0, HERE)

import build                       # noqa: E402
import guardrail_node              # noqa: E402
import predicate_equiv as pe       # noqa: E402
import template_conformance as tc  # noqa: E402
from _common import (iter_entries, compile_predicate, eval_predicate,  # noqa: E402
                     load_guardrail, ROOT as COMMON_ROOT)

SERVER_PATH = os.path.join(ROOT, "09_家长端工具", "parent_cool_clone",
                           "server", "server.py")
SCHEMA_PATH = os.path.join(COMMON_ROOT, "schema", "entry.yaml")
TPL_PATH = os.path.join(PARENT, "templates", "predicate_templates.yaml")
STOCK_SOURCES = {"project_original", "family_emotion_support"}
# 批次 8：新增 6 条 pc_*（修复卡 + 五类预警）的 source_id（授权抓取来源）
BATCH8_SOURCES = {"fhs_hk_anger_management", "aiadhd_yell_repair"}
NEW_TPL = "PT_PARENT_ESCALATION_01"
TIERS = [(1, "low"), (2, "low"), (3, "mid"), (4, "mid"), (5, "high")]
# 批次 5：条目 when 单档化（关闭 D-06）后的三档分布（2/2/2），
# 与 golden tr_PE01..PE06 的 injected_contains 逐条一致。
TIER_ENTRIES = {
    "low": {"pc_escalation_no_label_01", "pc_escalation_restate_01"},
    "mid": {"pc_escalation_one_step_01", "pc_escalation_scope_01"},
    "high": {"pc_escalation_stop_01", "pc_escalation_refer_01"},
}


def _server():
    spec = importlib.util.spec_from_file_location("_pc_server_batch3", SERVER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _chunk(text):
    return {"id": "fake_escalation", "audience": "parent",
            "scenario": "parent_escalation", "inject_text": text}


def _entries():
    stock = [(p, fm) for p, fm, _ in iter_entries()
             if fm.get("source_id") in STOCK_SOURCES]
    new = [(p, fm) for p, fm, _ in iter_entries()
           if fm.get("source_id") == "parent_cool"]
    batch8 = [(p, fm) for p, fm, _ in iter_entries()
              if fm.get("source_id") in BATCH8_SOURCES]
    return stock, new, batch8


def run():
    errors = []
    checked = 0

    def ck(cond, msg):
        nonlocal checked
        checked += 1
        if not cond:
            errors.append(msg)

    srv = _server()
    stock, new, batch8 = _entries()
    ck(len(stock) == 18, f"存量条目应为 18，实际 {len(stock)}")
    ck(len(new) == 6, f"批次 3 派生条目应为 6，实际 {len(new)}")
    ck(len(batch8) == 6, f"批次 8 派生条目应为 6（修复卡 1 + 五类预警 5），实际 {len(batch8)}")

    # ---- ① 三档映射 ----
    seen = []

    def fake_retrieve(audience, scenario, state):
        seen.append((audience, scenario, state.get("parent_affect_level")))
        return []

    for n, expect in TIERS:
        r = srv.handle_parent_escalation(n, "", retrieve_fn=fake_retrieve)
        ck(r["level"] == expect, f"anger={n} 期望 {expect}，实际 {r['level']}")
    ck([x[2] for x in seen] == [x[1] for x in TIERS],
       f"三档映射序列不符：{[x[2] for x in seen]}")
    ck(all(x[0] == "parent" and x[1] == "parent_escalation" for x in seen),
       "retrieve 的 audience/scenario 不是 parent / parent_escalation")
    for bad in (0, 6, 1.5, "3", None, True):
        try:
            srv.handle_parent_escalation(bad, "", retrieve_fn=fake_retrieve)
            ck(False, f"非法入参 {bad!r} 未抛 ValueError")
        except ValueError:
            ck(True, "")

    # ---- ② 三档真实检索命中（批次 5：条目 when 单档化，分布 2/2/2）----
    # 批次 8：新增 6 条 pc_*（修复卡 + 五类预警，source_id 非 parent_cool，
    # when 三档全命中）并入 parent_escalation。三档命中数由 2 → 8
    # （既有 2 单档 + 新 6 三档）。断言改为：既有单档条目仍在对应档命中
    # （不污染）+ 新 6 条三档全命中 + 命中总数 = 8。
    for lv in ("low", "mid", "high"):
        hits = build.retrieve("parent", "parent_escalation",
                              {"parent_affect_level": lv})
        ids = {h["id"] for h in hits}
        ck(TIER_ENTRIES[lv] <= ids,
           f"{lv} 档应仍含单档条目 {sorted(TIER_ENTRIES[lv])}，实际 {sorted(ids)}")
        ck(len(hits) == 8,
           f"{lv} 档应恰命中 8 条（既有 2 单档 + 新 6 三档），实际 {len(hits)}")
        ck(all(h["scenario"] == "parent_escalation" and h["audience"] == "parent"
               for h in hits), f"{lv} 档串入了非 parent_escalation / 非 parent 块")
        ck(all(h["when"] for h in hits), f"{lv} 档命中了无谓词块")
    # 条目派生后，服务不再走 degraded
    for n, _lv in TIERS:
        r = srv.handle_parent_escalation(n, "错题又错了")
        ck(r["degraded"] is False and r["blocked"] is False,
           f"anger={n} 条目已派生却仍 degraded/blocked：{r['degraded']}/{r['blocked']}")
        ck(len(r["steps"]) == 3, f"anger={n} steps 不是 3 段")

    # ---- ②' 三档输出差异化（批次 5 关闭 D-06 的可证伪证据）----
    d06 = {}
    for n in (1, 3, 5):
        r = srv.handle_parent_escalation(n, "孩子又摔笔了")
        d06[r["level"]] = r["line"]
    ck(len(set(d06.values())) == 3,
       f"三档 line 应两两不同（D-06 关闭证据），实际：{d06}")

    # ---- ②'' 批次 6A 检索确定性锁定（审计：05_审核与运营/regression/批次6A_审计.md）----
    # 每档固定返回 chunks.jsonl 顺序第一条（排序键 overlap 恒 0，稳定排序退化为文件序）；
    # situation 不参与选择，用户输入是未来 LLM 化的上下文入口，不是排序依据。
    EXPECTED_FIRST = {
        "low": "pc_escalation_no_label_01",
        "mid": "pc_escalation_one_step_01",
        "high": "pc_escalation_refer_01",
    }
    for lv, eid in EXPECTED_FIRST.items():
        cands = build.retrieve("parent", "parent_escalation",
                               {"parent_affect_level": lv})
        first = cands[0]["id"] if cands else None
        ck(first == eid,
           f"{lv} 档 candidates[0] 应固定为 {eid}（chunks 顺序），实际 {first}")
    # 同档不同 situation 同输出：可证伪锚点——将来若改「situation 参与选择」，
    # 此断言变红，强制走行为变更流程而不是静默改变。
    _a = srv.handle_parent_escalation(3, "孩子又摔笔了")
    _b = srv.handle_parent_escalation(3, "完全无关的输入 xyz")
    ck(_a["line"] == _b["line"] and _a["steps"] == _b["steps"],
       "同档不同 situation 输出应一致（锁定固定第一条，见批次 6A 审计）")
    # ---- ②''' 批次 6C.4：when 过滤硬门锁定——不存在的档位必须返回空。
    # 防 when 写错/过滤失效导致全档命中（那是 degraded 分支真实可达的根因路径）。
    ck(build.retrieve("parent", "parent_escalation",
                      {"parent_affect_level": "nonexistent"}) == [],
       "不存在档位应返回空列表（when 过滤硬门；非空说明谓词失效）")

    # ---- ③ guardrail block → fallback（line / steps 各自过 judge）----
    rules = load_guardrail().get("rules", [])
    blocked_line = srv.handle_parent_escalation(
        5, "", retrieve_fn=lambda a, s, st: [
            _chunk("你就是ADHD，先别急。把本子合上。等呼吸平了再说话。今晚到这里就好。")])
    ck(blocked_line["blocked"] is True and blocked_line["degraded"] is False,
       "line 含违规词未触发 blocked，或把 degraded/blocked 混用")
    ck("你就是ADHD" not in json.dumps(blocked_line, ensure_ascii=False),
       "blocked 后仍暴露被拦文本")
    blocked_step = srv.handle_parent_escalation(
        2, "", retrieve_fn=lambda a, s, st: [
            _chunk("先停一下。他就是懒，得催着写。把第一句读一遍。今晚到这里。")])
    ck(blocked_step["blocked"] is True,
       "steps 单独含违规词也必须被拦（line 与 steps 各自过 judge）")
    ck(guardrail_node.judge("你就是ADHD", rules)["decision"] == "block",
       "guardrail 规则表与运行时判定器不同源或已失效")

    # ---- ④ degraded / blocked 严格分开 ----
    degraded = srv.handle_parent_escalation(
        3, "", retrieve_fn=lambda a, s, st: [])
    ck(degraded["degraded"] is True and degraded["blocked"] is False,
       "无条目时应 degraded=true / blocked=false")
    ck(degraded["line"] == srv.PENDING and degraded["hint"] == srv.DEGRADED_HINT,
       "degraded 未走占位 + 撤退指引")
    for label, r in (("degraded", degraded), ("blocked", blocked_line),
                     ("blocked_step", blocked_step)):
        ck(r["degraded"] != r["blocked"], f"{label} 的 degraded 与 blocked 未互斥")
    ck(blocked_line["hint"] == srv.BLOCKED_HINT, "blocked 未走独立提示")

    # ---- ⑤ when 白名单（schema_check 不校验嵌套，本组兜住）----
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    allowed = set(schema["fields"]["when"]["allowed_fields"])
    enums = schema["fields"]["when"]["field_enums"].get("parent_affect_level")
    ck("parent_affect_level" in allowed, "entry.yaml when.allowed_fields 缺 parent_affect_level")
    ck(enums == ["low", "mid", "high"], f"parent_affect_level 枚举不符：{enums}")
    ck("parent_escalation" in schema["fields"]["scenario"]["values"],
       "entry.yaml scenario 枚举缺 parent_escalation")
    for p, fm in new + batch8:
        ck(set((fm.get("when") or {}).keys()) <= allowed,
           f"[{fm['id']}] when 字段越出 entry.yaml 白名单")
        val = (fm.get("when") or {}).get("parent_affect_level")
        ck(isinstance(val, list), f"[{fm['id']}] 枚举字段未写成列表（eval_predicate 会 int(sv) 恒假）")
        ck(set(val or []) <= set(enums or []), f"[{fm['id']}] 取值越出枚举")
        ck(fm.get("scenario") == "parent_escalation" and fm.get("audience") == "parent",
           f"[{fm['id']}] scenario/audience 不符")
        ck("callable" not in fm and "exit_when" not in fm,
           f"[{fm['id']}] 解释性条目不得含 callable / exit_when")
        ck(fm.get("template_ref") == NEW_TPL, f"[{fm['id']}] template_ref 不对")

    # ---- ⑥ 不编造：每句逐字可溯到存量 18 条 ----
    stock_texts = [fm.get("inject_text", "") for _, fm in stock]
    for p, fm in new:
        segs = [s.strip() for s in fm.get("inject_text", "").replace("\n", "").split("。")
                if s.strip()]
        ck(len(segs) >= 4, f"[{fm['id']}] 句子不足 4 句，assemble 无法生成 line+3 steps")
        for seg in segs:
            ck(any(seg in t for t in stock_texts),
               f"[{fm['id']}] 非逐字可溯句：{seg[:40]}…")

    # ---- ⑥' 批次 8 不编造：新 6 条每句逐字可溯到 staging 原文 ----
    # 批次 8 条目来源是 5 份授权抓取的中文 staging 原文（fhs / aiadhd），
    # 不是存量 18 条。每句必须是对应 staging 原文的逐字子串。
    staging_texts = {}
    for fn in ("fhs_gov_hk_parent_anger_management_tc_2026-11-15.md",
               "aiadhd_yell_repair_2026-11-15.md"):
        sp = os.path.join(COMMON_ROOT, "00_来源治理", "_staging", fn)
        with open(sp, encoding="utf-8") as f:
            staging_texts[fn] = f.read().replace("\n", " ")
    for p, fm in batch8:
        segs = [s.strip() for s in fm.get("inject_text", "").replace("\n", "").split("。")
                if s.strip()]
        ck(len(segs) >= 4, f"[{fm['id']}] 句子不足 4 句，assemble 无法生成 line+3 steps")
        for seg in segs:
            ck(any(seg in t for t in staging_texts.values()),
               f"[{fm['id']}] 批次8 非逐字可溯句（应来自 staging 原文）：{seg[:40]}…")

    # ---- ⑦ 豁免口径（按条目计数，不凑 0→1）----
    with open(TPL_PATH, encoding="utf-8") as f:
        tpldoc = yaml.safe_load(f)
    contract = tpldoc.get("template_fields_contract", {}) or {}
    tpl = next((t for t in tpldoc["templates"] if t["id"] == NEW_TPL), None)
    ck(tpl is not None, "模板库缺 PT_PARENT_ESCALATION_01")
    if tpl is None:
        return (False, errors, checked)
    if tpl:
        ck(tpl.get("required_params") == [], "新模板 required_params 应为空")
        ck("exempt_reason" in contract.get("optional_fields", []),
           "契约未声明 exempt_reason，豁免应判失败")
        ck(len(str(tpl.get("exempt_reason", "")).strip())
           > int(contract.get("exempt_reason_min_length", 20)),
           "exempt_reason 长度未过 2.5c 硬闸")
        ck(compile_predicate(tpl["when"])["parent_affect_level"]["op"] == "in",
           "模板 when 未编译成 op=in")
    ok_conf, errs_conf, _ = tc.run()
    ck(ok_conf, "template_conformance 未全绿：" + "; ".join(errs_conf[:2]))
    m = getattr(tc.run, "metrics", {})
    # 批次 8：新增 6 条 pc_*（source_id 非 parent_cool）也套 PT_PARENT_ESCALATION_01，
    # params_exempt 按条目计数 6 → 12。正确口径 = 所有 scenario=parent_escalation 条目数。
    pe_all = [p for p, fm, _ in iter_entries()
              if fm.get("scenario") == "parent_escalation"]
    ck(m.get("params_exempt") == len(pe_all),
       f"params_exempt 应按条目计数={len(pe_all)}（parent_cool 6 + 批次8 新 6），"
       f"实际 {m.get('params_exempt')}（方案字面写 0→1 是模板种类口径）")
    ck(m.get("deviation_rate", 1) == 0.0, "主偏离率未保持 0.0%")
    with open(os.path.join(COMMON_ROOT, "05_审核与运营", "regression",
                          "模板偏离清单.md"), encoding="utf-8") as f:
        dev_report = f.read()
    ck(f"`{NEW_TPL}`" in dev_report, "偏离清单未留痕豁免模板")
    # 豁免模板种类按 (模板,理由) 聚合后恒为 1
    exempt_lines = [l for l in dev_report.splitlines()
                    if l.startswith(f"| `{NEW_TPL}` |")]
    ck(len(exempt_lines) == 1, f"豁免模板种类应为 1，实际 {len(exempt_lines)}")

    # ---- ⑧ 既有条目触发范围 unchanged + 两套求值一致 ----
    polluted = [fm["id"] for _, fm in stock
                if "parent_affect_level" in (fm.get("when") or {})
                or fm.get("scenario") == "parent_escalation"]
    ck(polluted == [], f"既有条目被新字段/新场景污染：{polluted}")
    old_preds = [compile_predicate(t["when"]) for t in tpldoc["templates"]
                 if t["id"] != NEW_TPL]
    d = pe.diff_mode(old_preds, old_preds + [compile_predicate(tpl["when"])])
    ck(d["scope_change"] == "unchanged" and not d["affected_entries"],
       f"diff_mode scope 异常：{d['scope_change']} / {d['affected_entries']}")
    ck((d["state_points_before"], d["state_points_after"],
        len(d["added"]), len(d["removed"])) == (7872, 10368, 2496, 0),
       "diff_mode 数字漂移（提案审批记录需同步更新）")
    mismatch = 0
    for state in pe.iter_states():
        if (pe.filter_eval(pe.filter_compile(tpl["when"]), state)
                != eval_predicate(compile_predicate(tpl["when"]), state)):
            mismatch += 1
            break
    ck(mismatch == 0, "过滤侧与触发侧对新模板谓词求值不一致")

    # ---- ⑨ 批次 6D Q3：设计意图锁定 ----
    # 用 AST 而非字符串匹配：server.py 的 docstring 里也写了「不调 router.route()」，
    # 简单 grep 会假绿。这里检查模块级 import 与 handle 函数体内的实际调用节点。
    # 可证伪性：若将来有人把 router.route() 接进家长工具（即让孩子状态合流），
    # 本断言变红，强制走 API 契约变更流程，而不是静默改变架构边界。
    import ast
    with open(SERVER_PATH, encoding="utf-8") as f:
        server_tree = ast.parse(f.read())
    imported_router = any(
        (isinstance(n, ast.Import) and any(a.name == "router" for a in n.names))
        or (isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] == "router")
        for n in ast.walk(server_tree))
    handle_fn = next((n for n in ast.walk(server_tree)
                      if isinstance(n, ast.FunctionDef)
                      and n.name == "handle_parent_escalation"), None)
    router_calls = []
    if handle_fn:
        for n in ast.walk(handle_fn):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                owner = n.func.value
                if isinstance(owner, ast.Name) and owner.id == "router":
                    router_calls.append(n.func.attr)
    # 单条断言（方案 6D.4 要求 +1，不凑数）：函数存在 + 无 import + 无调用节点
    ck(handle_fn is not None and not imported_router and not router_calls,
       f"handle_parent_escalation 不得调用 router.route()（6D Q3 设计意图）；"
       f"fn={handle_fn is not None} import={imported_router} calls={router_calls}")

    run.metrics = {
        "derived_entries": len(new),
        "stock_entries": len(stock),
        "params_exempt": m.get("params_exempt"),
        "exempt_template_kinds": len(exempt_lines),
        "three_tier_hits": {lv: len(build.retrieve("parent", "parent_escalation",
                                                   {"parent_affect_level": lv}))
                            for lv in ("low", "mid", "high")},
        "deviation_rate": m.get("deviation_rate"),
    }
    return (len(errors) == 0, errors, checked)


def main():
    ok, errors, checked = run()
    print(f"[parent_escalation_tests] 断言={checked}  失败={len(errors)}")
    for e in errors[:20]:
        print("  ✗", e)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
