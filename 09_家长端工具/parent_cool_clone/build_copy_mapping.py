# -*- coding: utf-8 -*-
"""
阶段 B 批次 0 文案盘点 + 批次 3 回填生成器（可复跑、可证伪）。

职责：
  1) 读 03_agent编译/output/chunks.jsonl（编译产物，唯一文案来源）；
  2) 按 09_家长端工具/parent_cool_clone/data/features.json 的槽位定义生成
     data/copy_mapping.json；
  3) mapped 槽位的 text 直接取该条 inject_text 全文（逐字，不手抄、不截断、不改写）；
  4) 映射不上的槽位一律 status=pending_batch3 + text=null，绝不编造；
  5) 内嵌验收断言 + 生成 data/盘点结果.md 留痕。

批次 3 变更（2026-11-13，PROP-0004/0005 同批）：
  - chunks.jsonl 由 18 条增至 24 条（新增 6 条 parent_escalation 解释性条目）；
  - 其中 5 条逐字回填 script_card_08..12，第 6 条只作 ai_line 运行时检索候选；
  - 三档撤退 / 修复卡 / 五类预警 / 免责声明仍无来源，按不编造纪律
    **如实保留 pending_batch3**，并在 note 里追加批次 3 复核结论；
  - 存量条目计数断言从「chunks 总数 == 18」改为「非 parent_escalation
    的存量条目 == 18」，使脚本在批次 3 之后仍可复跑。

纪律依据（用户 2026-11-13 阶段 B 方案）：
  - 不依赖 parent-cool 原文；文案从现有 18 条源条目取；
  - 映射不上的槽位如实标「待批次 3 派生」，不编造；
  - 只写 09_家长端工具/ 目录，不改编译管线文件。
"""
import ast
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CHUNKS = os.path.join(ROOT, "03_agent编译", "output", "chunks.jsonl")
DATA = os.path.join(HERE, "data")
FEATURES = os.path.join(DATA, "features.json")
OUT = os.path.join(DATA, "copy_mapping.json")
REPORT = os.path.join(DATA, "盘点结果.md")
SERVER_PY = os.path.join(HERE, "server", "server.py")

# 批次 3 回填：新条目 → 静态槽位。text 仍由脚本从 chunks.jsonl 直取，不手抄。
BATCH3_CARD_MAP = [
    ("script_card_08", "pc_escalation_restate_01"),
    ("script_card_09", "pc_escalation_stop_01"),
    ("script_card_10", "pc_escalation_scope_01"),
    ("script_card_11", "pc_escalation_one_step_01"),
    ("script_card_12", "pc_escalation_refer_01"),
]
BATCH3_RUNTIME_ONLY_ENTRY = "pc_escalation_no_label_01"

# 批次 5：三档撤退槽位映射（when 单档化后按档位取条目）。
# 同档多条时按 id 字母序取第一条，可复现、不主观。
BATCH5_RETREAT_MAP = [
    ("retreat_low", "low", "pc_escalation_no_label_01", "pc_escalation_restate_01"),
    ("retreat_mid", "mid", "pc_escalation_one_step_01", "pc_escalation_scope_01"),
    ("retreat_high", "high", "pc_escalation_refer_01", "pc_escalation_stop_01"),
]

BATCH3_PENDING_NOTE = (
    "【批次 3 复核｜批次 5 更新】已派生 6 条 parent_escalation 解释性条目（逐字摘句自现有 18 条），"
    "其中 5 条回填 script_card_08..12；批次 5 已将三档撤退 3 槽按单档化条目回填为 mapped、"
    "免责 1 槽改为 filled_constant。本槽位所需文案在现有 18 条与派生条目中"
    "仍无对应，故按不编造纪律保留 pending_batch3 占位，等 parent-cool 原文到位后"
    "另行走来源接入。本状态是如实标注，不是漏做。"
)

# 批次 8：6 个 pending_batch3 槽位（修复卡 1 + 五类预警 5）授权抓取来源接入后回填。
# 逐字取自 derive_batch8_entries.py 生成的 6 条条目（source_id 非 parent_cool）。
BATCH8_SLOT_MAP = [
    ("repair_card_01", "pc_repair_card_01"),
    ("warning_signs_呼吸", "pc_warning_breath_01"),
    ("warning_signs_肌肉", "pc_warning_muscle_01"),
    ("warning_signs_声音", "pc_warning_voice_01"),
    ("warning_signs_胸口", "pc_warning_chest_01"),
    ("warning_signs_念头", "pc_warning_thought_01"),
]


def server_disclaimer():
    """从 server.py 用 ast 机械提取 DISCLAIMER 常量（同源直取，不手抄）。"""
    with open(SERVER_PY, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "DISCLAIMER":
                    val = ast.literal_eval(node.value)
                    if isinstance(val, tuple):
                        val = "".join(val)
                    if not isinstance(val, str) or not val.strip():
                        raise AssertionError("server.py DISCLAIMER 不是非空字符串")
                    return val
    raise AssertionError("server.py 未找到 DISCLAIMER 常量")


def load_chunks():
    out = {}
    with open(CHUNKS, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            out[row["id"]] = row
    return out


def mapped(slot, entry_id, chunks, note, **extra):
    if entry_id not in chunks:
        raise AssertionError(f"[{slot}] source_entry_id 不在 chunks.jsonl: {entry_id}")
    rec = {
        "slot": slot,
        "source_entry_id": entry_id,
        "status": "mapped",
        "note": note,
        "text": chunks[entry_id]["inject_text"],
    }
    rec.update(extra)
    return rec


def pending(slot, note, **extra):
    rec = {"slot": slot, "source_entry_id": None,
           "status": "pending_batch3", "note": note, "text": None}
    rec.update(extra)
    return rec


def main():
    chunks = load_chunks()
    stock = {k: v for k, v in chunks.items()
             if v.get("scenario") != "parent_escalation"}
    with open(FEATURES, encoding="utf-8") as f:
        features = json.load(f)

    records = []

    # ---- 1) script_cards: 12 槽 ----
    # 前 7 槽取 7 条 fes_* 且 audience=parent 的存量条目。
    card_map = [
        ("script_card_01", "fes_parent_restate_01", "复述家长的困扰，先不给办法。"),
        ("script_card_02", "fes_parent_script_01", "同一句提醒换个说法；含「不翻旧账」边界。"),
        ("script_card_03", "fes_parent_settle_01", "先降温的三步热身；contraindication_flag=caution。"),
        ("script_card_04", "fes_parent_pause_signal_01", "整晚停下的信号与专业转介；contraindication_flag=caution。"),
        ("script_card_05", "fes_parent_one_night_scope_01", "用「做完这几步就收」划今晚边界。"),
        ("script_card_06", "fes_parent_low_pressure_01", "只留一个小到能完成的任务。"),
        ("script_card_07", "fes_parent_single_scene_01", "只讲最近一次具体场景，不给通用建议。"),
    ]
    for slot, eid, desc in card_map:
        row = chunks[eid]
        assert row["audience"] == "parent", f"{eid} 不是 parent"
        records.append(mapped(
            slot, eid, chunks,
            f"逐字取自 {eid}.inject_text 全文（含步骤序列与可说/不可说句）；{desc}"
            f" text 未截断、未改写。scenario={row['scenario']}、type={row['type']}、"
            f"contraindication_flag={row['contraindication_flag']}。",
            group="script_cards",
        ))
    # 后 5 槽：批次 3 派生条目回填。逐字取自 chunks.jsonl，不手抄。
    for slot, eid in BATCH3_CARD_MAP:
        row = chunks[eid]
        assert row["scenario"] == "parent_escalation", f"{eid} 不是 parent_escalation"
        records.append(mapped(
            slot, eid, chunks,
            f"【批次 3 回填】逐字取自 {eid}.inject_text 全文；该条目由 "
            "03_agent编译/derive_batch3_entries.py 从现有 18 条逐句摘取重组，"
            "每句均为存量 inject_text 的逐字子串（parent_escalation_tests 独立复验）。"
            "scenario=parent_escalation、type=explanatory、when 三档全命中、"
            "条目级不做内容分档；语义边界见条目正文。",
            group="script_cards",
        ))

    # ---- 2) retreat_tiers: 3 档（批次 5：条目 when 单档化后按档位 mapped）----
    for slot, tier, eid, other in BATCH5_RETREAT_MAP:
        row = chunks[eid]
        assert row["scenario"] == "parent_escalation", f"{eid} 不是 parent_escalation"
        records.append(mapped(
            slot, eid, chunks,
            f"【批次 5 分档回填】取自 {tier} 档条目 {eid} 的 inject_text 全文（逐字）；"
            f"同档另有 {other}，按 id 字母序取第一条（可复现）。分档依据见条目 "
            f"front matter 的 deviation.reason（when 由 [low, mid, high] 收窄为单档，"
            "批次 5 关闭 D-06）。",
            group="retreat_tiers",
        ))

    # ---- 3) repair_card: 1 槽（批次 8：授权抓取来源接入后回填为 mapped）----
    for slot, eid in BATCH8_SLOT_MAP:
        if not slot.startswith("repair"):
            continue
        row = chunks[eid]
        assert row["scenario"] == "parent_escalation", f"{eid} 不是 parent_escalation"
        records.append(mapped(
            slot, eid, chunks,
            f"【批次 8 回填】逐字取自 {eid}.inject_text 全文；该条目由 "
            "03_agent编译/derive_batch8_entries.py 从授权抓取的 staging 原文"
            "逐句摘取（source_id 见条目 front matter），parent_escalation_tests "
            "⑥' 独立复验逐字可溯。scenario=parent_escalation、type=explanatory、"
            "when 三档全命中；语义边界见条目正文。",
            group="repair_card",
        ))

    # ---- 4) warning_signs: 5 行（批次 8：授权抓取来源接入后回填为 mapped）----
    for slot, eid in BATCH8_SLOT_MAP:
        if not slot.startswith("warning_signs"):
            continue
        cat = slot[len("warning_signs_"):]
        row = chunks[eid]
        assert row["scenario"] == "parent_escalation", f"{eid} 不是 parent_escalation"
        records.append(mapped(
            slot, eid, chunks,
            f"【批次 8 回填】逐字取自 {eid}.inject_text 全文；该条目由 "
            "03_agent编译/derive_batch8_entries.py 从授权抓取的 staging 原文"
            "（fhs_hk_anger_management）逐句摘取，parent_escalation_tests ⑥' "
            "独立复验逐字可溯。信号与动作分列，动作列逐字取自中文来源，"
            "不逐类编造。scenario=parent_escalation、when 三档全命中。",
            group="warning_signs", category=cat,
            columns=features["warning_signs"]["columns"],
        ))

    # ---- 5) ui.disclaimer_slot（批次 5：filled_constant，复用 server.py 中性免责）----
    disc_text = server_disclaimer()
    records.append({
        "slot": "disclaimer",
        "source_entry_id": None,
        "status": "filled_constant",
        "group": "ui",
        "note": "【批次 5 免责收口】复用 server.py 的 DISCLAIMER 中性文本"
                "（批次 4.5b 定稿，去批次号 D-07）。本脚本用 ast 从 server.py "
                "机械提取，不手抄；它不是知识库条目，故标 filled_constant 而非 "
                "mapped，避免混淆「知识库来源」与「常量填充」两种口径。"
                "parent-cool 原文到位后，与本常量及前端展示一并联动替换。",
        "text": disc_text,
    })

    # ---- 批次 3 复核留痕：所有仍 pending 的槽位追加统一说明 ----
    for r in records:
        if r["status"] == "pending_batch3":
            r["note"] = r["note"] + BATCH3_PENDING_NOTE

    # ---- meta.action_granularity（0c 判定，仍只看存量 7 条）----
    step_markers = ["①", "先", "再", "最后", "做完", "撤掉", "收工"]
    with_steps = [eid for _s, eid, _d in card_map
                  if any(m in stock[eid]["inject_text"] for m in step_markers)]
    granularity = "task_level" if len(with_steps) >= 6 else "cognitive_action_level"
    if granularity != "task_level":
        raise AssertionError("粒度判定异常，需人工复核")

    mapped_n = sum(1 for r in records if r["status"] == "mapped")
    pending_n = sum(1 for r in records if r["status"] == "pending_batch3")
    filled_n = sum(1 for r in records if r["status"] == "filled_constant")

    doc = {
        "meta": {
            "batch": 8,
            "generated_by": "09_家长端工具/parent_cool_clone/build_copy_mapping.py",
            "source_artifact": "03_agent编译/output/chunks.jsonl",
            "source_entry_count": len(chunks),
            "stock_entry_count": len(stock),
            "fes_parent_entry_count": 7,
            "no_original_text": True,
            "action_granularity": granularity,
            "action_granularity_basis": (
                "7/7 条 fes_* parent 话术的 inject_text 均含多步动作序列"
                "（①②③ / 先…再…最后…）与撤除条件（做完就收 / 连着两晚就撤），"
                "属任务级；没有一条是纯单句认知动作卡。"
                "该判定描述的是现有可复用文案的粒度，不是 parent-cool 原文粒度"
                "（原文不在手）；批次 3 建 parent_cool 接入卡时直接引用此值。"
            ),
            "cognitive_action_level_found": False,
            "slot_total": len(records),
            "mapped_count": mapped_n,
            "pending_batch3_count": pending_n,
            "filled_constant_count": filled_n,
            "batch3": {
                "derived_entries": 6,
                "backfilled_slots": [s for s, _ in BATCH3_CARD_MAP],
                "runtime_only_entry": BATCH3_RUNTIME_ONLY_ENTRY,
                "remaining_pending": pending_n,
                "pending_not_cleared_reason": (
                    "批次 3 时三档撤退 / 修复卡 / 五类身体预警 / 免责声明原文在现有 18 条"
                    "与 6 条派生条目中均无对应文案，如实保留占位；"
                    "批次 5 已将三档撤退（条目分档回填）与免责（常量填充）关闭，"
                    "剩余 pending 见下。"
                ),
                "no_fabrication_check": (
                    "6 条派生 inject_text 的每句均为存量 inject_text 的逐字子串，"
                    "由 derive_batch3_entries.py 与 parent_escalation_tests.py 双向校验。"
                ),
            },
            "batch5": {
                "goal": "条目级分档关闭 D-06 + pending 10 → 6",
                "tier_entries": {t: [e for _s, _t, e, _o in [m for m in BATCH5_RETREAT_MAP if m[1] == t]]
                                 for t in ("low", "mid", "high")},
                "retreat_backfill": [s for s, _t, _e, _o in BATCH5_RETREAT_MAP],
                "disclaimer": "filled_constant（ast 从 server.py 提取 DISCLAIMER）",
                "d06_evidence": "test_server.py test_10 + parent_escalation_tests ②'：三档 line 两两不同",
            },
            "batch8": {
                "goal": "pending 6 → 0：修复卡 + 五类预警授权抓取来源接入",
                "backfilled_slots": [s for s, _e in BATCH8_SLOT_MAP],
                "sources": "fhs_hk_anger_management / aiadhd_yell_repair（中文派生）；"
                           "nhs_inform / pkjcoaching / calmhome 仅 _staging 留痕参照",
                "no_fabrication_check": "6 条 inject_text 每句均为 staging 原文逐字子串，"
                                        "由 derive_batch8_entries.py 与 parent_escalation_tests ⑥' 双向校验。",
                "language_rule": "中文派生 + 英文留痕（用户批次 8 拍板）",
            },
            "record_contract": {
                "slot": "str", "source_entry_id": "str|null",
                "status": "mapped|pending_batch3|filled_constant", "note": "str",
                "text": "str|null — mapped/filled_constant 时逐字取自 inject_text / server.DISCLAIMER；"
                        "pending 时为 null",
            },
            "notes": [
                "ai_line.output（line + steps[3]）是运行时由 retrieve + assemble 生成的动态输出，"
                "不是静态文案槽位，不进本盘点表；见批次 2 server.py。",
                "script_cards 的 text 是整段 inject_text（含步骤与可说/不可说句），"
                "未截断未改写；前端按卡片展示全文。",
                "mapped 槽位的 source_entry_id 全部经 chunks.jsonl 存在性校验；"
                "text 由脚本直取，不经人工转录，可复跑比对。",
            ],
        },
        "records": records,
    }

    # ---- 验收断言 ----
    assert len(stock) == 18, f"存量条目应为 18，实际 {len(stock)}"
    assert set(features) == {"breathing", "script_cards", "ai_line", "retreat_tiers",
                             "warning_signs", "repair_card", "emotion_log", "ui"}
    assert len([r for r in records if r["group"] == "script_cards"]) == features["script_cards"]["slots"]
    assert len([r for r in records if r["group"] == "retreat_tiers"]) == len(features["retreat_tiers"])
    assert len([r for r in records if r["group"] == "repair_card"]) == features["repair_card"]["slots"]
    assert len([r for r in records if r["group"] == "warning_signs"]) == len(features["warning_signs"]["categories"])
    slots = [r["slot"] for r in records]
    assert len(slots) == len(set(slots)), "槽位名重复"
    for r in records:
        assert r["status"] in ("mapped", "pending_batch3", "filled_constant")
        assert isinstance(r["note"], str) and len(r["note"]) > 0, f"[{r['slot']}] 无说明"
        if r["status"] == "mapped":
            assert r["source_entry_id"] in chunks
            assert r["text"] == chunks[r["source_entry_id"]]["inject_text"], \
                f"[{r['slot']}] text 与 inject_text 不逐字一致"
            if r["slot"] in [s for s, _ in BATCH3_CARD_MAP]:
                assert "【批次 3 回填】" in r["note"]
            if r["slot"] in [s for s, _t, _e, _o in BATCH5_RETREAT_MAP]:
                assert "【批次 5 分档回填】" in r["note"]
        elif r["status"] == "filled_constant":
            assert r["source_entry_id"] is None
            assert r["text"] == server_disclaimer()
            for marker in ("批次", "batch", "派生"):
                assert marker not in r["text"], f"disclaimer 含批次标记：{marker}"
        else:
            assert r["source_entry_id"] is None and r["text"] is None
            assert "【批次 3 复核｜批次 5 更新】" in r["note"], f"[{r['slot']}] 缺复核留痕"
    # 批次 8 数字契约（可证伪；批次 5 为 mapped=15 / pending=6 / filled=1）
    assert mapped_n == 21 and pending_n == 0 and filled_n == 1, \
        f"批次 8 后应 mapped=21 / pending=0 / filled_constant=1，实际 {mapped_n}/{pending_n}/{filled_n}"
    # 三档撤退逐字来自对应档位条目（D-06 关闭的静态面证据）
    for slot, tier, eid, _other in BATCH5_RETREAT_MAP:
        rec = next(r for r in records if r["slot"] == slot)
        assert rec["source_entry_id"] == eid
        w = (chunks[eid].get("when") or {}).get("parent_affect_level")
        # chunks.jsonl 的 when 是编译后结构（op=in / values=[...]）
        vals = w["values"] if isinstance(w, dict) else w
        assert vals == [tier], f"[{slot}] 源条目 {eid} when={w}，应为 [{tier}]"
    assert len(chunks) == 30, f"chunks 应为 30 条，实际 {len(chunks)}（需先重跑 build.py）"
    assert BATCH3_RUNTIME_ONLY_ENTRY in chunks

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # ---- 同源 .js 包装（file:// 下 fetch 本地 JSON 会被 CORS 拦）----
    for name, payload in [("features.js", ("__PC_FEATURES__", features)),
                          ("copy_mapping.js", ("__PC_COPY__", doc))]:
        var, obj = payload
        p = os.path.join(DATA, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(f"window.{var} = ")
            json.dump(obj, f, ensure_ascii=False, indent=2)
            f.write(";\n")
        with open(p, encoding="utf-8") as f:
            raw = f.read()
        prefix = f"window.{var} = "
        assert raw.startswith(prefix) and raw.rstrip().endswith(";")
        assert json.loads(raw[len(prefix):].rstrip()[:-1]) == obj, f"{name} 与 JSON 不同源"

    # ---- 留痕报告 ----
    lines = [
        "# 阶段 B · 文案来源盘点结果（批次 0 盘点 + 批次 3 回填）",
        "",
        "生成脚本：`09_家长端工具/parent_cool_clone/build_copy_mapping.py`（可复跑）",
        "唯一文案来源：`03_agent编译/output/chunks.jsonl`（编译产物）",
        "",
        "## 汇总",
        "",
        f"- 槽位总数 **{len(records)}**；`mapped` **{mapped_n}**；"
        f"`pending_batch3` **{pending_n}**；`filled_constant` **{filled_n}**；空槽 0。",
        f"- 编译产物条目：存量 **{len(stock)}** + 批次 3 派生 **6** = **{len(chunks)}**。",
        f"- `action_granularity` = **{granularity}**（7/7 条含步骤序列，无纯单句认知动作）。",
        "- 逐字校验：每个 mapped 的 `text` 与 `inject_text` 全等（脚本直取，非人工转录）；"
        "`filled_constant`（免责）由 ast 从 server.py 机械提取 DISCLAIMER。",
        "",
        "## 分组明细",
        "",
        "| 组 | 槽位数 | mapped | pending_batch3 | filled_constant |",
        "|---|---|---|---|---|",
    ]
    for g in ["script_cards", "retreat_tiers", "repair_card", "warning_signs", "ui"]:
        rs = [r for r in records if r["group"] == g]
        lines.append(f"| {g} | {len(rs)} | {sum(1 for r in rs if r['status']=='mapped')} "
                     f"| {sum(1 for r in rs if r['status']=='pending_batch3')} "
                     f"| {sum(1 for r in rs if r['status']=='filled_constant')} |")
    lines += ["", "## 已映射槽位", "", "| slot | source_entry_id |", "|---|---|"]
    for r in records:
        if r["status"] == "mapped":
            lines.append(f"| {r['slot']} | `{r['source_entry_id']}` |")
    lines += ["", "## 批次 3 回填", "",
              "- 派生 6 条 `parent_escalation` 解释性条目，5 条回填 "
              "`script_card_08..12`；第 6 条 `pc_escalation_no_label_01` "
              "只作 `ai_line` 运行时检索候选，不占静态槽位（不为凑数硬塞）。",
              "- 6 条 `inject_text` 由 `derive_batch3_entries.py` 从存量 18 条逐句摘取重组，"
              "每句都是存量 `inject_text` 的逐字子串；`parent_escalation_tests.py` 独立复验。",
              "",
              "## 批次 5 分档与收口", "",
              "- 6 条 `parent_escalation` 条目 `when` 由 `[low, mid, high]` 收窄为单档"
              "（2/2/2：low=no_label/restate，mid=one_step/scope，high=stop/refer），"
              "每条显式记 `deviation: value_adjusted`（子集收窄，单列不进主偏离率），"
              "关闭 D-06（三档输出相同）。",
              "- 三档撤退 3 槽按档位回填为 mapped（同档多条按 id 序取第一条，note 留痕）；"
              "免责 1 槽改 `filled_constant`（ast 提取 server.py DISCLAIMER，非知识库来源）。",
              "- D-06 关闭证据：`test_server.py::test_10` 与 `parent_escalation_tests` ②'"
              "断言火气 1/3/5 的 line 两两不同；golden `tr_PE01..PE06` 与分档逐条一致。",
              "",
              "## 仍待补槽位（如实标注，不是漏做）", "", "| slot | 原因摘要 |", "|---|---|"]
    for r in records:
        if r["status"] == "pending_batch3":
            lines.append(f"| {r['slot']} | {r['note'][:60]}… |")
    lines += [
        "",
        "## 三处读实判断（批次 0，非机械映射）",
        "",
        "1. **存量 11 条 parent 条目未用于填满 12 张话术卡**：它们的 scenario 是 "
        "`attention_drift` / `wm_overload`，属学科辅导支架、面向孩子作业过程，"
        "不是家长火气急救话术。按「家长情绪 ≠ 孩子挫败」不硬塞。",
        "2. **三级撤退 3 槽批次 5 起为 mapped**：批次 3 时无分档来源；批次 5 将 6 条派生"
        "条目 `when` 单档化（关闭 D-06）后按档位回填，逐字取自对应档位条目，不再伪造分档语义。",
        "3. **五类预警表 5 行仍 pending**：家长身体预警 ≠ 孩子崩溃信号，"
        "现有 18 条与派生条目均无对应文案。",
        "",
        "## 口径差异留痕（与方案字面不一致处）",
        "",
        "- 批次 3 时方案验收写「`pending_batch3` 清零或如实标注剩余项」：走后者，剩余 10 槽。"
        "批次 5 关闭其中 4 槽（三档撤退 3 + 免责 1），剩余 6 槽（修复卡 1 + 五类预警 5）"
        "逐条带复核说明，原文本就不在手，按「不编造」纪律继续保留。",
        "- 批次 3 的「三档映射」指服务层 `ANGER_TIER`；批次 5 起升级为条目级内容分档"
        "（when 单档化），D-06 正式关闭。",
        "",
        "## 边界",
        "",
        "本脚本只写 `09_家长端工具/parent_cool_clone/` 目录；不推远程、"
        "不启用 Actions、不改 63 页 BookStack 正文、不改既有 chunk/metadata。",
    ]
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"[batch5] chunks={len(chunks)} (stock={len(stock)}) slots={len(records)} "
          f"mapped={mapped_n} pending={pending_n} filled_constant={filled_n} "
          f"granularity={granularity} OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
