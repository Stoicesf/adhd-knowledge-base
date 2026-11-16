# -*- coding: utf-8 -*-
"""阶段六 · P1 编译管线  build.py
单命令：读源条目 → 跑四条 CI 硬规则 → 谓词编译（同一 when 生成过滤+触发两表示）
        → 产物A chunks.jsonl（检索块） → 产物B skill_registry.json（skill spec）
        → 产物哈希清单 manifest.sha256（P3 规则四：产物与源条目哈希绑定）
        → 写入 03_agent编译/output/

用法：
    python build.py              # 校验 + 编译 + 写出
    python build.py --selftest   # 额外跑 P1 验收断言

说明：真实向量索引属部署阶段；本环境「先结构化过滤、再向量精排」两段式中，
结构化过滤为硬门，向量精排以关键词重叠做占位排序（标注为 placeholder）。
"""
import os
import sys
import json
import glob
import hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
# build.py 位于 03_agent编译/，退一级才是工程根（此前退两级算成 F:\ ，
# 导致 ENTRIES_DIR 不存在、产物哈希清单漏掉全部源条目 —— 2026-11-13 修正）。
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(HERE, "output")
MANIFEST_PATH = os.path.join(OUT, "manifest.sha256")

# 阶段 A · 2.5a（2026-11-13）：取消本文件独立的 ENTRIES_DIR 硬编码。
# 编译（compile_entries）、write_manifest、verify_manifest 三处的路径来源
# 统一为 _common.iter_entry_paths()，与校验器完全同源，杜绝「条目进了
# chunks 但 manifest 不覆盖」；且可扫 02_内容包/*/ 下任意书籍目录。
sys.path.insert(0, os.path.join(HERE, "validators"))
from _common import iter_entries, iter_entry_paths, compile_predicate, eval_predicate
import schema_check, predicate_equiv, safety_scan, exit_exists
import source_intake_check, template_conformance

# 谓词求值函数在本模块顶层暴露，供 router.py 直接 import 同一对象。
# 契约：router.eval_predicate is build.eval_predicate is _common.eval_predicate
# 由 validators/router_tests.py 断言，防止「两套条件判断」漂移。


def validate_all():
    rep = {}
    ok_intake, errs_intake, n_intake = source_intake_check.run()
    rep["source_intake_check"] = (ok_intake, errs_intake, n_intake)
    ok_conf, errs_conf, n_conf = template_conformance.run()
    rep["template_conformance"] = (ok_conf, errs_conf, n_conf)
    ok_schema, errs_schema, n = schema_check.run()
    rep["schema_check"] = (ok_schema, errs_schema, n)
    ok_equiv, errs_equiv, m = predicate_equiv.run()
    rep["predicate_equiv"] = (ok_equiv, errs_equiv, m)
    ok_safe, errs_safe, k = safety_scan.run()
    rep["safety_scan"] = (ok_safe, errs_safe, k)
    ok_exit, errs_exit, j = exit_exists.run()
    rep["exit_exists"] = (ok_exit, errs_exit, j)
    all_ok = all([ok_intake, ok_conf, ok_schema, ok_equiv, ok_safe, ok_exit])
    return all_ok, rep


def compile_entries():
    """返回 list of compiled entry dicts（含双产物所需字段）。"""
    compiled = []
    for path, fm, _b in iter_entries():
        e = dict(fm)
        e["_src"] = os.path.basename(path)
        e["when_compiled"] = compile_predicate(fm.get("when"))
        e["exit_when_compiled"] = compile_predicate(fm.get("exit_when"))
        compiled.append(e)
    return compiled


def _sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def write_manifest(chunks_path, skills_path):
    """P3 规则四：把源条目与产物的 SHA256 绑定，人工不编辑。"""
    lines = [
        "# 阶段六 产物哈希清单（build.py 自动生成，人工不编辑）",
        "# 源条目变更后未重编译 → verify_manifest 失败",
        "# 源条目",
    ]
    for p in iter_entry_paths():
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        lines.append(f"{_sha256(p)}  {rel}")
    lines.append("# 产物")
    for p in (chunks_path, skills_path):
        lines.append(f"{_sha256(p)}  {os.path.basename(p)}")
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return MANIFEST_PATH


def verify_manifest():
    """独立校验：磁盘上的源条目/产物哈希是否与清单一致（规则四的本地实装）。

    在 verify_all.py 中于重编译**之前**调用，可抓「源条目改了但产物没重编译」；
    重编译之后调用，可抓「产物被人工改过」。
    """
    errors = []
    checked = 0
    if not os.path.exists(MANIFEST_PATH):
        return (False, ["manifest.sha256 不存在：请先运行 build.py 重编译"], 0)
    recorded = {}
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            sha, rel = line.split(None, 1)
            recorded[rel] = sha
    current = {}
    for p in iter_entry_paths():
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        current[rel] = _sha256(p)
    for name in ("chunks.jsonl", "skill_registry.json"):
        p = os.path.join(OUT, name)
        if os.path.exists(p):
            current[name] = _sha256(p)
    for rel, sha in current.items():
        checked += 1
        if rel not in recorded:
            errors.append(f"新增/未编译条目：{rel}（需重跑 build.py）")
        elif recorded[rel] != sha:
            errors.append(f"哈希漂移：{rel}（源或产物已变更但未重编译/被手改）")
    for rel in recorded:
        if rel not in current:
            checked += 1
            errors.append(f"清单中存在已删除条目：{rel}")
    return (len(errors) == 0, errors, checked)


def verify_manifest_selftest():
    """规则四自身的**可证伪性**断言：构造 2 个负例，校验器必须拒绝（防「假绿」）。

    不触碰任何工程文件：把伪造清单写到临时文件，仅在本函数内临时替换
    MANIFEST_PATH，finally 恢复。
    """
    global MANIFEST_PATH
    import tempfile
    errors = []
    checked = 0
    if not os.path.exists(MANIFEST_PATH):
        return (False, ["manifest.sha256 不存在，无法做规则四自测"], 0)
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        good = f.read()
    lines = good.splitlines()

    # 负例 1：篡改最后一个产物哈希（模拟人工改产物）
    bad1 = good.replace(lines[-1].split()[0], "0" * 64, 1)
    # 负例 2：清单删掉一个源条目行（模拟新增条目未重编译）
    bad2_lines, removed = [], False
    for l in lines:
        if (not removed and l and not l.startswith("#")
                and "chunks.jsonl" not in l and "skill_registry.json" not in l):
            removed = True
            continue
        bad2_lines.append(l)
    bad2 = "\n".join(bad2_lines) + "\n"

    orig = MANIFEST_PATH
    tmp_path = None
    try:
        for label, payload, keyword in (
            ("产物哈希被篡改", bad1, "哈希漂移"),
            ("源条目未编译", bad2, "新增/未编译条目"),
        ):
            checked += 1
            with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8",
                                             suffix=".sha256") as tf:
                tf.write(payload)
                tmp_path = tf.name
            MANIFEST_PATH = tmp_path
            ok, errs, _ = verify_manifest()
            if ok or not any(keyword in e for e in errs):
                errors.append(f"规则四自测失败：{label} 未被拒绝（ok={ok}, errs={errs[:2]}）")
            os.unlink(tmp_path)
            tmp_path = None
    finally:
        MANIFEST_PATH = orig
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
    return (len(errors) == 0, errors, checked)


def emit_outputs(compiled):
    os.makedirs(OUT, exist_ok=True)
    # 产物A：检索块
    chunks = []
    for e in compiled:
        chunks.append({
            "id": e["id"],
            "audience": e["audience"],
            "scenario": e["scenario"],
            "exec_target": e.get("exec_target"),
            "evidence_level": e.get("evidence_level"),
            "contraindication_flag": e.get("contraindication_flag"),
            "type": e["type"],
            "when": e["when_compiled"],
            "exit_when": e["exit_when_compiled"],
            "inject_text": e.get("inject_text", ""),
            "text_for_embedding": e.get("inject_text", ""),
            "source": e["_src"],
        })
    chunks_path = os.path.join(OUT, "chunks.jsonl")
    with open(chunks_path, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    # 产物B：skill registry（仅 type=procedural 且含 callable）
    skills = []
    for e in compiled:
        if e.get("type") == "procedural" and "callable" in e:
            cb = e["callable"]
            skills.append({
                "name": cb.get("name"),
                "audience": e["audience"],
                "scenario": e["scenario"],
                "trigger_condition": e["when_compiled"],
                "exit_condition": e["exit_when_compiled"],
                "params_schema": cb.get("params", {}),
                "returns_schema": cb.get("returns", {}),
                "side_effect": cb.get("side_effect"),
                # v1.1：支架强度，默认 full；light=re-entry 降级支架
                "scaffold_level": cb.get("scaffold_level", "full"),
            })
    skills_path = os.path.join(OUT, "skill_registry.json")
    with open(skills_path, "w", encoding="utf-8") as f:
        json.dump(skills, f, ensure_ascii=False, indent=2)

    # P3 规则四：产物哈希与源条目哈希绑定
    write_manifest(chunks_path, skills_path)
    return chunks_path, skills_path, len(chunks), len(skills)


def retrieve(audience, scenario, state, chunks_path=None):
    """两段式检索：①结构化过滤（audience+scenario+谓词）②向量精排占位（关键词重叠降序）。
    批次 6A 审计留痕：②的占位精排在中文语料上实际无区分度——查询串（state 值文本化，
    实际为 'low'/'mid'/'high' 等）经字符集 overlap 与中文 inject_text 比对实测恒 0，
    排序退化为 chunks.jsonl 文件序（Python sort 稳定）。真正的硬门是①的结构化过滤；
    勿误以为重叠排序在起作用（审计：05_审核与运营/regression/批次6A_审计.md）。
    返回命中的 chunk 字典列表（含 id / inject_text 等），不含错误 audience 的块。"""
    if chunks_path is None:
        chunks_path = os.path.join(OUT, "chunks.jsonl")
    hits = []
    with open(chunks_path, encoding="utf-8") as f:
        for line in f:
            c = json.loads(line)
            if c["audience"] != audience:
                continue
            if c["scenario"] != scenario:
                continue
            if not eval_in_state(c["when"], state):
                continue
            hits.append(c)
    # 占位精排：关键词重叠（state 文本化 vs inject_text）
    q = " ".join(str(v) for v in state.values())
    hits.sort(key=lambda c: overlap(q, c["inject_text"]), reverse=True)
    return hits


def eval_in_state(pred, state):
    return eval_predicate(pred, state)


def overlap(a, b):
    return sum(1 for w in set(a) if w in b)


def selftest():
    print("\n=== P1 验收自测 ===")
    fails = []

    # 1. 条目计数（阶段 A · 2.5a）：总数与类型分布全部动态取 len()，
    #    新增书籍目录（阶段 B 的书籍F）后自动跟上，不再硬编码 18/11/7。
    #    保留两条既有来源的存量基线（防既有条目被误删，有价值的回归断言），
    #    并新增「编译数 == 源条目路径数」交叉断言，直接验证多目录扫描无漏读。
    compiled = compile_entries()
    proc = [e for e in compiled if e["type"] == "procedural"]
    expl = [e for e in compiled if e["type"] == "explanatory"]
    by_source = {}
    for e in compiled:
        by_source.setdefault(e.get("source_id"), []).append(e)
    stock = by_source.get("project_original", [])
    new = by_source.get("family_emotion_support", [])
    n_paths = len(iter_entry_paths())
    if len(stock) != 11:
        fails.append(f"存量 project_original 条目应为11，实际 {len(stock)}")
    if len(new) != 7:
        fails.append(f"首批 family_emotion_support 条目应为7，实际 {len(new)}")
    if len(compiled) != n_paths:
        fails.append(f"编译条目数({len(compiled)}) != 源条目路径数({n_paths})：多目录扫描漏读")
    if len(proc) + len(expl) != len(compiled):
        fails.append(f"类型分布不自洽：程序性{len(proc)}+解释性{len(expl)} != 总数{len(compiled)}")

    # 2. 每条程序性都生成 skill spec
    chunks_path = os.path.join(OUT, "chunks.jsonl")
    skills_path = os.path.join(OUT, "skill_registry.json")
    with open(skills_path, encoding="utf-8") as f:
        skills = json.load(f)
    if len(skills) != len(proc):
        fails.append(f"skill spec 数({len(skills)}) != 程序性条目数({len(proc)})")

    # 2b. 降级支架产物字段（D2 裁决）：恰有 1 条 light，且来自 reentry 条目
    light = [s for s in skills if s.get("scaffold_level") == "light"]
    if len(light) != 1 or light[0]["name"] != "reentry_light_scaffold":
        fails.append(f"降级支架产物不符：{[(s.get('name'), s.get('scaffold_level')) for s in skills]}")

    # 3. 家长视角检索：attention_drift + 走神状态 → 命中 parent_redirect_drift_01，不串 child
    st_parent = {"task_phase": "执行", "attention_state": "drift",
                 "ownership": "child-leading", "wm_load": 0,
                 "consecutive_failures": 2, "consecutive_successes": 0}
    res_p = retrieve("parent", "attention_drift", st_parent, chunks_path)
    if not any(r["id"] == "parent_redirect_drift_01" for r in res_p):
        fails.append(f"家长检索未命中 parent_redirect_drift_01，实际命中：{[r['id'] for r in res_p]}")
    if any(r["audience"] == "child" for r in res_p):
        fails.append("家长检索串入了 child 条目（角色泄漏）")

    # 4. 儿童视角检索：不串 parent
    st_child = {"task_phase": "执行", "attention_state": "drift",
                "ownership": "child-leading", "wm_load": 0,
                "consecutive_failures": 2, "consecutive_successes": 0}
    res_c = retrieve("child", "attention_drift", st_child, chunks_path)
    if not any(r["id"] == "child_redirect_drift_01" for r in res_c):
        fails.append(f"儿童检索未命中 child_redirect_drift_01，实际命中：{[r['id'] for r in res_c]}")
    if any(r["audience"] == "parent" for r in res_c):
        fails.append("儿童检索串入了 parent 条目（角色泄漏）")

    # 5. 工作记忆场景检索
    #    注意：解释性块 when 于 2026-11-13 增「知识缺口」代理信号（排除 on-task），
    #    故检索输入改为 re-entry（存在缺口）才是有效场景；这是联动调整，非放宽断言。
    st_wm = {"task_phase": "计划", "attention_state": "re-entry",
             "ownership": "child-leading", "wm_load": 2,
             "consecutive_failures": 0, "consecutive_successes": 0}
    res_w = retrieve("parent", "wm_overload", st_wm, chunks_path)
    if not res_w:
        fails.append("工作记忆场景家长检索无命中")

    if fails:
        print("  ✗ 验收未通过：")
        for f_ in fails:
            print("    -", f_)
        return False
    print(f"  ✓ 全部验收断言通过（{len(compiled)}条 / {len(proc)}程序性+{len(expl)}解释性 / "
          "降级支架字段 / 角色零泄漏 / 场景可达）")
    return True


def main():
    print("[build] 校验 + 编译 ...")
    ok, rep = validate_all()
    for name, (o, errs, n) in rep.items():
        status = "OK" if o else f"FAIL({len(errs)})"
        print(f"  {name}: {status}  (样本={n})")
        for e in errs[:10]:
            print("    ✗", e)
    if not ok:
        print("\n[build] CI 硬规则未全绿，终止编译（不写产物）。")
        sys.exit(1)

    compiled = compile_entries()
    chunks_path, skills_path, nc, ns = emit_outputs(compiled)
    print(f"[build] 写出：{chunks_path} ({nc} 块) ；{skills_path} ({ns} skills) ；manifest.sha256")

    if "--selftest" in sys.argv:
        ok_st = selftest()
        sys.exit(0 if ok_st else 1)
    print("[build] 完成。")


if __name__ == "__main__":
    main()
