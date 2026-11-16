# -*- coding: utf-8 -*-
"""CI 硬闸（编译前）：template_conformance — 模板一致性 + 偏离登记。

宽松模式的「底线」实装：模板是默认路径，偏离是例外路径，例外必须被计数。
不对称设计：
  - exit_when  → 硬校验（不匹配任何 EX_* 即失败，不允许手写退出条件）；
  - when       → 软校验（套模板为主，手写补充记 deviation，不阻断）。

判定规则（用户 2026-11-13 拍板）：
  - when 与 template_ref 指向模板的字段集合交集非空      → 通过（from_template / with_deviation）
  - when 有手写补充且交集非空（填 deviation）           → 通过，记 when_with_deviation (Y)
  - template_ref: null                                  → 失败，记 when_fully_handwritten (Z)
  - when 与模板字段交集为空（无论 template_ref 是否非 null）→ 失败，同 Z（防「假合规」）
  - 解释性条目 exit_when                                → 不适用（exit_not_applicable 单列）
  - 程序性条目 exit_when 不匹配任何 EX_*                 → 失败（硬校验）
  - required_params 声明的必填字段未出现在 when          → 失败（角色护栏硬闸）

required_params 与 params 分离（2026-11-13）：
  params           = 可调参数，条目出现时排除「字段补充」判定，允许缺席；
  required_params  = 必填护栏，条目 when 必须显式出现，缺失即判失败。
  若按「params 全部必填」实现会误判 10/11（consecutive_failures / wm_load
  是条件性参数，并非每条都填），故 ownership 单列 required_params。

返回签名与现有 validator 一致：(ok, errors, checked)。
偏离统计通过 run.metrics 属性暴露（类似 guardrail_tests），不塞进返回值。
偏离清单自动生成到 05_审核与运营/regression/模板偏离清单.md，禁手改。

阶段 A · 2.5c (2026-11-13)：必填硬闸支持**显式豁免**。
required_params 为空不再静默放行，必须配模板字段契约声明的
exempt_reason 且长度 > 20 字；豁免计数 params_exempt 进 metrics 与
偏离清单，可审计。内嵌 _exemption_selftest() 六个用例（构造数据、
不碰磁盘），失败并入 errors，使「豁免变成默认」每次 verify_all 都可证伪。
"""
import os
import sys
import datetime

import yaml

sys.path.insert(0, os.path.dirname(__file__))
from _common import iter_entries, ROOT, compile_predicate

TEMPLATES_DIR = os.path.join(ROOT, "03_agent编译", "templates")
PRED_TEMPLATE_PATH = os.path.join(TEMPLATES_DIR, "predicate_templates.yaml")
EXIT_TEMPLATE_PATH = os.path.join(TEMPLATES_DIR, "exit_templates.yaml")
DEVIATION_REPORT_PATH = os.path.join(
    ROOT, "05_审核与运营", "regression", "模板偏离清单.md"
)


def _load_templates(path):
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("templates", [])


def _load_contract(path):
    """读取模板字段契约（2.5c）。缺失返回空 dict → 任何豁免都不被允许，
    保守失败，避免契约文件丢失时硬闸反而变松。"""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return (data or {}).get("template_fields_contract", {}) or {}


def _required_gate(tpl, entry_fields, contract):
    """必填护栏 / 显式豁免判定（纯函数，2.5c）。

    返回 (ok, error_msg, exempt: bool)：
      - required_params 非空 → 逐字段必填，缺一即失败；
      - required_params 为空 → 必须配 exempt_reason（字段须在契约
        optional_fields 中声明、长度 > exempt_reason_min_length），
        否则判失败，杜绝「把 required_params 删空就静默绕过」；
      - 豁免成立时 exempt=True，由 run() 计入 params_exempt 并留痕。
    """
    tid = tpl.get("id", "?")
    required = set(tpl.get("required_params", []))
    if required:
        missing = sorted(required - entry_fields)
        if missing:
            return False, (f"params 必填校验失败：模板 {tid} 要求 when 显式出现 "
                           f"{missing}（角色护栏）；缺失请补填或走扩展提案"), False
        return True, "", False

    min_len = int(contract.get("exempt_reason_min_length", 20))
    if "exempt_reason" not in contract.get("optional_fields", []):
        return False, (f"模板 {tid} required_params 为空，但 exempt_reason "
                       f"未在 template_fields_contract.optional_fields 中声明"), False
    reason = tpl.get("exempt_reason")
    if not isinstance(reason, str) or len(reason.strip()) <= min_len:
        return False, (f"模板 {tid} required_params 为空：必须配 exempt_reason "
                       f"且长度 > {min_len} 字（防豁免变默认），当前 {reason!r}"), False
    return True, "", True


def _exemption_selftest():
    """2.5c 豁免闸可证伪性自测（monkeypatch 构造数据，不碰磁盘）。

    用户清单四例 + 两条回归保护：
      ① 空 required_params、无 exempt_reason       → 失败
      ② 空 + 短 exempt_reason（≤20 字）           → 失败
      ③ 空 + >20 字 exempt_reason                 → 放行且 exempt=True
      ④ 非空 required_params 缺字段               → 仍失败（回归保护）
      ⑤ 非空 required_params 且字段齐全           → 放行且 exempt=False
      ⑥ 契约未声明 exempt_reason，理由再长也不放行 → 失败（防豁免变默认）

    checked 不并入 run()，使样本数仍等于源条目数。
    """
    contract = {"optional_fields": ["exempt_reason"],
                "exempt_reason_min_length": 20}
    long_reason = ("家长火气场景是家长主导自救，不涉及儿童主导权归属，"
                   "故 ownership 语义不适用且不应硬塞进谓词。")
    cases = [
        ("①空列表无理由", {"id": "T_EMPTY", "required_params": []},
         set(), False, False),
        ("②空列表短理由", {"id": "T_SHORT", "required_params": [], "exempt_reason": "太短"},
         set(), False, False),
        ("③空列表长理由", {"id": "T_OK", "required_params": [], "exempt_reason": long_reason},
         set(), True, True),
        ("④非空缺字段", {"id": "T_MISS", "required_params": ["ownership"]},
         set(), False, False),
        ("⑤非空字段齐全", {"id": "T_FULL", "required_params": ["ownership"]},
         {"ownership"}, True, False),
    ]
    errors = []
    for label, tpl, fields, want_ok, want_exempt in cases:
        ok, err, exempt = _required_gate(tpl, fields, contract)
        if ok != want_ok or exempt != want_exempt:
            errors.append(f"{label}: 期望 ok={want_ok}/exempt={want_exempt}，"
                          f"实际 ok={ok}/exempt={exempt} err={err}")
    ok6, _, _ = _required_gate(
        {"id": "T_NOCONTRACT", "required_params": [], "exempt_reason": long_reason},
        set(), {"optional_fields": [], "exempt_reason_min_length": 20})
    if ok6:
        errors.append("⑥契约未声明 exempt_reason 却放行（豁免变成默认）")
    return (len(errors) == 0, errors, len(cases) + 1)


def _field_set(when):
    """when dict → 字段名集合（用于交集判定，忽略取值）。"""
    if not isinstance(when, dict):
        return set()
    return set(when.keys())


def _normalize_exit(exit_when):
    """exit_when → 规范化结构（复用 compile_predicate），用于与 EX_* 模板比较。"""
    return compile_predicate(exit_when)


def _exit_match(entry_exit, templates):
    """返回匹配的模板 id，或 None。逐字段完全一致。"""
    norm = _normalize_exit(entry_exit)
    for t in templates:
        if _normalize_exit(t.get("exit_when")) == norm:
            return t["id"]
    return None


def run():
    pred_templates = _load_templates(PRED_TEMPLATE_PATH)
    exit_templates = _load_templates(EXIT_TEMPLATE_PATH)
    contract = _load_contract(PRED_TEMPLATE_PATH)   # 2.5c 模板字段契约
    pred_by_id = {t["id"]: t for t in pred_templates}

    errors = []
    checked = 0
    deviations = []          # 偏离清单行
    exempt_records = []      # 2.5c：显式豁免留痕（模板 + 理由）

    # 统计口径
    entries_total = 0
    when_from_template = 0
    when_with_deviation = 0      # 字段补充（进主偏离率）
    when_value_adjusted = 0      # 取值变更（单列，不进主偏离率）
    when_fully_handwritten = 0   # 失败态（template_ref 缺失/交集空），正常恒为 0
    exit_from_template = 0
    exit_hard_fail = 0
    exit_not_applicable = 0
    params_required_missing = 0   # 必填护栏缺失（失败态，正常恒为 0）
    params_exempt = 0             # 2.5c：required_params 为空且显式豁免成立的条目数

    for path, fm, _body in iter_entries():
        checked += 1
        entries_total += 1
        eid = fm.get("id", "?")
        etype = fm.get("type")
        when = fm.get("when")
        template_ref = fm.get("template_ref")
        deviation = fm.get("deviation")

        # ---- when 校验（软，但有空交集/空引用则判失败）----
        if template_ref is None or template_ref == "null" or template_ref == "":
            # template_ref 缺失/空 → 判失败（模板库缺场景，需提案）
            when_fully_handwritten += 1
            errors.append(
                f"[{eid}] template_ref 缺失/为 null：完全手写 when，需提交 "
                f"A 类（新谓词字段）或 B 类（新场景类型）扩展提案，而非记偏离"
            )
        elif template_ref not in pred_by_id:
            when_fully_handwritten += 1
            errors.append(
                f"[{eid}] template_ref={template_ref} 不在谓词模板库中（悬空引用）"
            )
        else:
            tpl = pred_by_id[template_ref]
            # applies_to 过滤：解释性条目只能引用 applies_to 含 explanatory 的模板
            if etype == "explanatory" and "explanatory" not in tpl.get("applies_to", []):
                errors.append(
                    f"[{eid}] 解释性条目 template_ref={template_ref} 的 applies_to "
                    f"不含 explanatory（{tpl.get('applies_to')}）"
                )
            entry_fields = _field_set(when)
            tpl_fields = _field_set(tpl.get("when"))

            # ---- 必填护栏 / 显式豁免（2.5c）----
            # required_params 非空 → 逐字段必填；为空 → 必须配契约声明的
            # exempt_reason 且 >20 字，否则判失败（防「删空即绕过」）。
            ok_gate, err_gate, exempt = _required_gate(tpl, entry_fields, contract)
            if not ok_gate:
                params_required_missing += 1
                errors.append(f"[{eid}] {err_gate}")
            elif exempt:
                params_exempt += 1
                exempt_records.append({
                    "template": template_ref,
                    "reason": str(tpl.get("exempt_reason", "")).strip(),
                })

            if not entry_fields & tpl_fields:
                # 防「假合规」：挂一个模板 ID 但 when 完全重写，交集为空 → 判失败
                when_fully_handwritten += 1
                errors.append(
                    f"[{eid}] when 字段集合与模板 {template_ref} 交集为空："
                    f"模板名存实亡，视为完全手写，需提案而非记偏离"
                )
            elif deviation and deviation not in (None, "none", {}):
                dev_kind = deviation.get("kind", "") if isinstance(deviation, dict) else ""
                reason = deviation.get("reason", "") if isinstance(deviation, dict) else ""
                if not reason:
                    errors.append(f"[{eid}] deviation 缺 reason（偏离必须说明原因）")
                if dev_kind == "value_adjusted":
                    # 取值变更：字段名相同、取值超出模板，单列不进主偏离率
                    when_value_adjusted += 1
                else:
                    # 字段补充：进主偏离率
                    when_with_deviation += 1
                deviations.append({
                    "entry": eid, "template": template_ref,
                    "field": dev_kind or "field_supplement",
                    "content": reason,
                    "reason": reason,
                    "date": str(datetime.date.today()),
                })
            else:
                when_from_template += 1

        # ---- exit_when 校验（硬）----
        exit_when = fm.get("exit_when")
        if etype == "explanatory":
            # 解释性条目无退出条件 → 不适用，单列
            exit_not_applicable += 1
        else:
            # 程序性（或 boundary 等其他）条目：exit_when 必须匹配 EX_*
            if not exit_when:
                exit_hard_fail += 1
                errors.append(f"[{eid}] 程序性条目缺 exit_when（必须匹配 EX_* 模板）")
            else:
                matched = _exit_match(exit_when, exit_templates)
                if matched is None:
                    exit_hard_fail += 1
                    errors.append(
                        f"[{eid}] exit_when 不匹配任何 EX_* 模板：退出条件不允许手写，"
                        f"需 C 类（新退出模板）提案"
                    )
                else:
                    exit_from_template += 1

    # ---- 偏离率 ----
    # 主偏离率只算「字段补充」when_with_deviation；取值变更 value_adjusted 单列，
    # 完全手写 fully_handwritten 是失败态（正常恒为 0，非 0 说明绕过）。
    n = entries_total if entries_total else 1
    deviation_rate = when_with_deviation / n

    metrics = {
        "entries_total": entries_total,
        "when_from_template": when_from_template,
        "when_with_deviation": when_with_deviation,
        "when_value_adjusted": when_value_adjusted,
        "when_fully_handwritten": when_fully_handwritten,
        "exit_from_template": exit_from_template,
        "exit_hard_fail": exit_hard_fail,
        "exit_not_applicable": exit_not_applicable,
        "params_required_missing": params_required_missing,
        "params_exempt": params_exempt,          # 2.5c
        "deviation_rate": deviation_rate,
    }
    run.metrics = metrics

    # ---- 2.5c：豁免闸可证伪性自测（构造数据，不碰磁盘、不并入 checked）----
    ok_gate_test, errs_gate_test, _ = _exemption_selftest()
    if not ok_gate_test:
        errors.extend(f"[2.5c 豁免闸自测] {e}" for e in errs_gate_test)

    # ---- 偏离清单（自动生成，禁手改）----
    _write_deviation_report(deviations, metrics, exempt_records)

    return (len(errors) == 0, errors, checked)


def _write_deviation_report(deviations, metrics, exempt_records=None):
    exempt_records = exempt_records or []
    os.makedirs(os.path.dirname(DEVIATION_REPORT_PATH), exist_ok=True)
    lines = [
        "# 模板偏离清单",
        "",
        "> 本文件由 template_conformance.py 自动生成，人工不编辑（与 manifest.sha256 同纪律）。",
        "> 每轮 verify_all 重跑时同步刷新。",
        "",
        f"- 条目总数：{metrics['entries_total']}",
        f"- when 套模板（无偏离）：{metrics['when_from_template']}",
        f"- when 字段补充（进偏离率）：{metrics['when_with_deviation']}",
        f"- when 取值变更（单列）：{metrics['when_value_adjusted']}",
        f"- when 完全手写（失败态）：{metrics['when_fully_handwritten']}",
        f"- exit 套模板：{metrics['exit_from_template']}",
        f"- exit 不适用（解释性）：{metrics['exit_not_applicable']}",
        f"- required_params 必填护栏缺失：{metrics.get('params_required_missing', 0)}",
        f"- required_params 显式豁免条目（params_exempt）：{metrics.get('params_exempt', 0)}",
        f"- 偏离率（字段补充/条目总数）：{metrics['deviation_rate']*100:.1f}%",
        "",
    ]
    if deviations:
        lines.append("| 条目 | 模板 | 偏离字段 | 偏离内容 | 原因 | 登记日期 |")
        lines.append("|---|---|---|---|---|---|")
        for d in deviations:
            lines.append(
                f"| {d['entry']} | {d['template']} | {d['field']} | "
                f"{d['content']} | {d['reason']} | {d['date']} |"
            )
    else:
        lines.append("（当前无偏离条目）")

    lines.append("")
    lines.append("## 豁免模板（2.5c：required_params 为空，必须配显式理由）")
    if exempt_records:
        agg = {}
        for r in exempt_records:
            key = (r["template"], r["reason"])
            agg[key] = agg.get(key, 0) + 1
        lines.append("| 模板 | 豁免理由 | 命中条目数 |")
        lines.append("|---|---|---|")
        for (tid, reason), n in agg.items():
            lines.append(f"| `{tid}` | {reason} | {n} |")
    else:
        lines.append("无（当前 `params_exempt=0`；现有 5 个模板 `required_params` 均为 `[ownership]`）。")

    with open(DEVIATION_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    ok, errors, checked = run()
    print(f"[template_conformance] 校验条目={checked}  错误={len(errors)}")
    m = getattr(run, "metrics", {})
    print(f"  偏离率={m.get('deviation_rate', 0)*100:.1f}%  "
          f"套模板={m.get('when_from_template', 0)}  "
          f"有偏离={m.get('when_with_deviation', 0)}  "
          f"完全手写={m.get('when_fully_handwritten', 0)}")
    ok_st, errs_st, n_st = _exemption_selftest()
    print(f"  豁免闸自测={ok_st}  用例={n_st}  失败={len(errs_st)}  "
          f"params_exempt={m.get('params_exempt', 0)}")
    for e in errors + errs_st:
        print("  ✗", e)
    sys.exit(0 if ok and ok_st else 1)


if __name__ == "__main__":
    main()
