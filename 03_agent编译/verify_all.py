# -*- coding: utf-8 -*-
"""阶段六 · 本地统一验证入口（不依赖运行时 / 不触远程）

一条命令跑完 P0–P4 中所有「纯函数 + 数据」可证伪的部分：
  P1  build.py 四条 CI 硬规则 + 双产物编译 + 产物哈希 + 验收自测
  P1  artifact_hash  源条目/产物哈希绑定（规则四，重编译之前独立校验）
  P2  router_tests  路由三态 / 防过度支持 / 角色零泄漏 / 同源断言
  P3  guardrail_tests  pass-block-rewrite / 漏放率 / 误拦率基线
  P4  regression     轨迹回归 / 轨迹级指标 / 降级支架断言
  B3  parent_escalation_tests  阶段 B 批次 3 第 14 组（PROP-0004/0005）

用法：
  E:/ANACONDA/python.exe 03_agent编译/verify_all.py
退出码：全部绿 0；任一失败 1。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "validators"))

import build
import router_tests
import guardrail_tests
import regression
import template_conformance
import parent_escalation_tests


def _run(label, fn):
    ok, errors, checked = fn()
    status = "OK  " if ok else "FAIL"
    print(f"  [{status}] {label:<28} 断言/样本={checked:<8} 失败={len(errors)}")
    for e in errors[:10]:
        print("        ✗", e)
    return ok, len(errors), checked


def main():
    print("=" * 72)
    print("阶段六 · 本地统一验证（P1 CI / P2 路由 / P3 guardrail / P4 回归 / B3 家长急救）")
    print("=" * 72)

    # 阶段性提示（2026-11-13 阶段 B 批次 3）：
    # PROP-0004/0005 full 审批已同批落地，schema 升 v1.2，
    # parent_affect_level 与 parent_escalation 进契约；新增 6 条解释性条目、
    # 6 条 conformance 轨迹（entry_via 旁路）、第 14 组验收。
    # 既有 25 条轨迹、18 条存量条目、11 个 skills 行为零变化。
    print("[PHASE] 阶段 B 批次 3：PROP-0004/0005 已落地（schema v1.2）；"
          "parent_escalation 独立场景 + PT_PARENT_ESCALATION_01 显式豁免；"
          "6 条派生条目 / 6 条旁路轨迹 / 第 14 组验收。"
          "口径如实：params_exempt 按条目计数、diff_mode 维度不变（checked 因条目数增加）。")

    results = []

    # 规则四：先在「重编译之前」基于磁盘现状独立校验哈希，
    # 可抓「源条目改了但产物没重编译」；这是本组存在的主要意义。
    print("\n--- P1 产物哈希（规则四，重编译前独立校验）---")
    o, ne, n = _run("P1/artifact_hash", build.verify_manifest)
    results.append(("P1/artifact_hash", o, ne, n))
    # 规则四自身必须可证伪：构造负例，校验器应拒绝（防哈希校验变成假绿）
    o, ne, n = _run("P1/hash_selftest", build.verify_manifest_selftest)
    results.append(("P1/hash_selftest", o, ne, n))

    # P1：编译期硬规则（build.py 的 validate_all）+ 编译 + selftest
    print("\n--- P1 编译期硬规则 + 双产物 ---")
    ok, rep = build.validate_all()
    for name, (o, errs, n) in rep.items():
        results.append((f"P1/{name}", o, len(errs), n))
        print(f"  [{'OK  ' if o else 'FAIL'}] P1/{name:<23} 样本={n:<8} 失败={len(errs)}")
        for e in errs[:5]:
            print("        ✗", e)
    # 编译（不写不合法产物）；emit_outputs 同时刷新 manifest.sha256
    if ok:
        compiled = build.compile_entries()
        cp, sp, nc, ns = build.emit_outputs(compiled)
        print(f"  [OK  ] 双产物：{nc} chunks / {ns} skills ；manifest.sha256 已刷新")
        ok_st = build.selftest()
        # 样本数随来源批次动态取条目数（阶段三首批后 11 → 18，批次 3 后 24）
        results.append(("P1/selftest", ok_st, 0 if ok_st else 1, len(compiled)))
    else:
        results.append(("P1/selftest", False, 1, 0))

    # P2 / P3 / P4 / B3
    print("\n--- P2 路由 / P3 guardrail / P4 回归 / B3 家长急救 ---")
    for label, fn in [
        ("P2/router_tests", router_tests.run),
        ("P3/guardrail_tests", guardrail_tests.run),
        ("P4/regression", regression.run),
        ("B3/parent_escalation_tests", parent_escalation_tests.run),
    ]:
        o, ne, n = _run(label, fn)
        results.append((label, o, ne, n))

    # 生成回归报告（即便不通过也产出，便于排查）
    try:
        r = regression.evaluate()
        regression.write_report(r)
    except Exception as ex:  # pragma: no cover
        print(f"  [WARN] 回归报告生成失败：{ex}")

    # 同源契约总断言（本轮最隐蔽的坑）
    print("\n--- 同源契约 ---")
    from _common import eval_predicate as common_eval
    import router
    same = (router.eval_predicate is build.eval_predicate is common_eval)
    print(f"  [{'OK  ' if same else 'FAIL'}] router ≡ build ≡ _common 的 eval_predicate 为同一对象")
    results.append(("同源契约", same, 0 if same else 1, 1))

    # 汇总
    total = len(results)
    passed = sum(1 for _, o, _, _ in results if o)
    total_errors = sum(ne for _, _, ne, _ in results)
    total_checked = sum(n for _, _, _, n in results)
    print("\n" + "=" * 72)
    print(f"汇总：{passed}/{total} 组通过；断言/状态点合计 {total_checked}；失败 {total_errors}")
    gm = getattr(guardrail_tests.run, "metrics", {})
    pm = getattr(parent_escalation_tests.run, "metrics", {})
    if pm:
        print(f"      批次3：派生条目={pm.get('derived_entries')}  "
              f"params_exempt={pm.get('params_exempt')}（按条目计数；"
              f"豁免模板种类={pm.get('exempt_template_kinds')}）  "
              f"三档命中={pm.get('three_tier_hits')}")
    try:
        rm = regression.evaluate()["metrics"]
        print(f"      guardrail 漏放率={gm.get('leak_rate', 0)*100:.1f}%  "
              f"误拦率={gm.get('false_block_rate', 0)*100:.1f}%（基线）")
        print(f"      回归 conformance={rm['conformance_pass']}/{rm['conformance_turns']}  "
              f"角色泄漏={rm['role_leak_count']}  诊断案例={rm['diagnostic_identified']}")
    except Exception:
        pass

    # 偏离率告警（不阻断，进报告）：绝对上限 40% 优先，再叠加相对位移判断
    tm = getattr(template_conformance.run, "metrics", None)
    if tm:
        dr = tm.get("deviation_rate", 0) * 100
        if dr > 40:
            print(f"[WARN] 模板偏离率 {dr:.1f}% 超绝对上限 40%：模板库可能整体失效，"
                  f"应先扩展模板而非继续派生")
        elif dr > 20:
            print(f"[WARN] 模板偏离率 {dr:.1f}%，建议审视是否需要扩展模板")
        else:
            print(f"      模板偏离率 {dr:.1f}%（正常，仅记录）")
    print("=" * 72)
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
