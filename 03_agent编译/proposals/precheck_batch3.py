# -*- coding: utf-8 -*-
"""阶段 B 批次 3 · PROP-0004 / PROP-0005 自动化预检（可复跑、可证伪）

对应 01_规范与标准/模板扩展提案流程.md §三 full 审批 / §四 diff_mode：
  1. 状态空间 diff（不是估算，实跑 predicate_equiv.diff_mode）
  2. 受影响条目清单确认（既有 18 条引用新字段/新场景的数量必须为 0）
  3. 新模板谓词可被两套求值分别求值（无「两套条件漂移」）
  4. exempt_reason 过 2.5c 豁免闸（>20 字、字段在契约中声明）
  5. 如实记录「schema_check 不校验嵌套 when.allowed_fields」这一已知限制

用法：E:/ANACONDA/python.exe 03_agent编译/proposals/precheck_batch3.py
退出码：全绿 0；任一失败 1。落地前后均可复跑。
"""
import os
import sys
import json
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(PARENT, ".."))
sys.path.insert(0, os.path.join(PARENT, "validators"))
sys.path.insert(0, PARENT)

import predicate_equiv as pe                     # noqa: E402
from _common import compile_predicate, eval_predicate, iter_entries  # noqa: E402

TPL_PATH = os.path.join(PARENT, "templates", "predicate_templates.yaml")
NEW_TPL_ID = "PT_PARENT_ESCALATION_01"
NEW_WHEN = {"parent_affect_level": ["low", "mid", "high"]}
EXEMPT_REASON = "家长自救非辅导过程，ownership 语义不适用，豁免必填护栏"

# 既有存量来源（阶段三首批之前 + 首批），用于区分「既有」与「本批次新增」
STOCK_SOURCES = {"project_original", "family_emotion_support"}


def _existing_templates():
    with open(TPL_PATH, encoding="utf-8") as f:
        tpls = yaml.safe_load(f).get("templates", [])
    return [t for t in tpls if t["id"] != NEW_TPL_ID]


def main():
    errors = []
    out = {}

    # ---- 1. 状态空间 diff ----
    old = [compile_predicate(t["when"]) for t in _existing_templates()]
    new = old + [compile_predicate(NEW_WHEN)]
    d = pe.diff_mode(old, new)
    out["state_space_points"] = pe.STATE_POINT_COUNT
    out["diff_mode"] = {
        "state_points_before": d["state_points_before"],
        "state_points_after": d["state_points_after"],
        "added": len(d["added"]),
        "removed": len(d["removed"]),
        "scope_change": d["scope_change"],
        "affected_entries": d["affected_entries"],
    }
    if pe.STATE_POINT_COUNT != 10368:
        errors.append(f"状态点基数应为 10368（阶段 A 2.5b 已并入三档），实际 {pe.STATE_POINT_COUNT}")
    if (d["state_points_before"], d["state_points_after"],
            len(d["added"]), len(d["removed"]), d["scope_change"]) != (
            7872, 10368, 2496, 0, "unchanged"):
        errors.append(f"diff_mode 数字漂移：{out['diff_mode']}")
    out["per_tier_points"] = {
        lv: len(pe._state_points([compile_predicate({"parent_affect_level": [lv]})]))
        for lv in ("low", "mid", "high")
    }
    if set(out["per_tier_points"].values()) != {3456}:
        errors.append(f"单档状态点应各 3456，实际 {out['per_tier_points']}")

    # ---- 2. 受影响条目清单确认 ----
    entries = list(iter_entries())
    stock = [(p, fm) for p, fm, _ in entries if fm.get("source_id") in STOCK_SOURCES]
    new_e = [(p, fm) for p, fm, _ in entries if fm.get("source_id") == "parent_cool"]
    out["entries_total"] = len(entries)
    out["stock_entries"] = len(stock)
    out["parent_escalation_entries"] = len(new_e)
    if len(stock) != 18:
        errors.append(f"存量条目应为 18，实际 {len(stock)}（既有产物可能被误删）")
    leaked = [fm["id"] for _, fm in stock
              if "parent_affect_level" in (fm.get("when") or {})
              or fm.get("scenario") == "parent_escalation"]
    out["stock_entries_referencing_new_field_or_scenario"] = leaked
    if leaked:
        errors.append(f"既有条目被新字段/新场景污染：{leaked}")
    out["predicate_equiv_checked_now"] = pe.STATE_POINT_COUNT * len(entries)

    # ---- 3. 两套求值对新字段一致（防第三套条件漂移）----
    mism = []
    for state in pe.iter_states():
        fv = pe.filter_eval(pe.filter_compile(NEW_WHEN), state)
        ev = eval_predicate(compile_predicate(NEW_WHEN), state)
        if fv != ev:
            mism.append(state)
            break
    out["dual_eval_mismatch"] = len(mism)
    if mism:
        errors.append("过滤侧与触发侧对新模板谓词求值不一致")

    # ---- 4. 2.5c 豁免闸 ----
    with open(TPL_PATH, encoding="utf-8") as f:
        contract = (yaml.safe_load(f) or {}).get("template_fields_contract", {}) or {}
    min_len = int(contract.get("exempt_reason_min_length", 20))
    out["exempt_reason_length"] = len(EXEMPT_REASON.strip())
    out["exempt_declared"] = "exempt_reason" in contract.get("optional_fields", [])
    if not out["exempt_declared"]:
        errors.append("template_fields_contract.optional_fields 未声明 exempt_reason")
    if len(EXEMPT_REASON.strip()) <= min_len:
        errors.append(f"exempt_reason 长度 {len(EXEMPT_REASON.strip())} 未 > {min_len}")

    # ---- 5. 已知限制记录（不是失败项，但必须显式出现在预检输出里）----
    out["known_limit"] = (
        "schema_check.py 只校验 fields 下的顶层必填/枚举，不读嵌套 "
        "when.allowed_fields；新字段合法性由 parent_escalation_tests 组断言兜住。"
    )
    out["literal_deviation_note"] = (
        "方案写 diff_mode 186624 → 预期更多；186624 是 checked（18×10368），"
        "维度阶段 A 已扩完、本批次不变。checked 增量来自条目数增加。"
    )

    print(json.dumps(out, ensure_ascii=False, indent=2))
    if errors:
        print("\n[precheck] FAIL")
        for e in errors:
            print("  ✗", e)
        return 1
    print("\n[precheck] OK：diff_mode 数字可复现、受影响条目为空、两套求值一致、豁免闸通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
