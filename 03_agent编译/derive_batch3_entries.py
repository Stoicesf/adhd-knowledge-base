# -*- coding: utf-8 -*-
"""阶段 B 批次 3 · 书籍F 源条目派生脚本（逐字可溯、可复跑、可证伪）

纪律（用户 2026-11-13 阶段 B 方案）：
  - 不依赖 parent-cool 原文；文案只从现有 18 条源条目取；
  - 映射不上的槽位标 pending_batch3，**不编造**。

本脚本因此不手写任何一句 inject_text：从 chunks.jsonl 现有 18 条的
inject_text 按「。」切句，按 DERIVATIONS 指定的 (来源条目, 句序号)
取原句，用「。」重新拼接。每条新 inject_text 的每一句都必定是某条
现有 inject_text 的逐字子串；parent_escalation_tests.py 会用独立的
「不编造断言」再验一遍，可证伪。

用法：E:/ANACONDA/python.exe 03_agent编译/derive_batch3_entries.py
输出：02_内容包/书籍F_家长急救/*.md（6 条 explanatory 条目）
"""
import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
CHUNKS = os.path.join(HERE, "output", "chunks.jsonl")
OUT_DIR = os.path.join(ROOT, "02_内容包", "书籍F_家长急救")
STOCK_SOURCES = {"project_original", "family_emotion_support"}

# (来源条目 id, 按「。」切分后的句序号)
DERIVATIONS = [
    {
        "id": "pc_escalation_restate_01",
        "slot": "script_card_08",
        "flag": "safe",
        "title": "火气上来时先复述，别急着给办法",
        "boundary": "复述与分辨四类情况；不宣称按火气 1—5 分档。",
        "sentences": [
            ("fes_parent_restate_01", 0),
            ("fes_parent_restate_01", 1),
            ("fes_parent_restate_01", 2),
            ("fes_parent_restate_01", 4),
            ("fes_parent_script_01", 5),
        ],
    },
    {
        "id": "pc_escalation_stop_01",
        "slot": "script_card_09",
        "flag": "caution",
        "title": "出现压不住火的信号就整个停下、离开书桌",
        "boundary": "含专业转介边界；本句原文写的是「孩子明显崩溃…或家长自己已经压不住火」，未改写为家长身体预警。",
        "sentences": [
            ("fes_parent_pause_signal_01", 0),
            ("fes_parent_settle_01", 0),
            ("fes_parent_pause_signal_01", 1),
            ("fes_parent_pause_signal_01", 3),
            ("fes_parent_pause_signal_01", 4),
        ],
    },
    {
        "id": "pc_escalation_scope_01",
        "slot": "script_card_10",
        "flag": "safe",
        "title": "只讲最近一次具体场景，不铺开到习惯与作息",
        "boundary": "场景收窄与按情绪先处理；不构成火气分级。",
        "sentences": [
            ("fes_parent_single_scene_01", 0),
            ("fes_parent_single_scene_01", 1),
            ("fes_parent_single_scene_01", 4),
            ("fes_parent_single_scene_01", 7),
            ("fes_parent_settle_01", 8),
        ],
    },
    {
        "id": "pc_escalation_one_step_01",
        "slot": "script_card_11",
        "flag": "safe",
        "title": "今晚只留一个能收尾的动作，做完就收",
        "boundary": "「做完就收」的边界；不替代三档撤退分级文案。",
        "sentences": [
            ("fes_parent_low_pressure_01", 0),
            ("fes_parent_one_night_scope_01", 1),
            ("fes_parent_low_pressure_01", 2),
            ("fes_parent_settle_01", 7),
            ("fes_parent_one_night_scope_01", 5),
        ],
    },
    {
        "id": "pc_escalation_refer_01",
        "slot": "script_card_12",
        "flag": "caution",
        "title": "专业支持边界与不贴标签的说法",
        "boundary": "沿用本库既有边界句；免责声明原文不在手，未自撰。",
        "sentences": [
            ("fes_parent_pause_signal_01", 2),
            ("fes_parent_script_01", 3),
            ("fes_parent_script_01", 4),
            ("fes_parent_script_01", 5),
            ("fes_parent_pause_signal_01", 4),
        ],
    },
    {
        "id": "pc_escalation_no_label_01",
        "slot": None,   # 纯运行时检索候选，不占静态槽位
        "flag": "safe",
        "title": "同一句提醒换个说法，不下结论不贴标签",
        "boundary": "第 6 条只服务 ai_line 动态检索，不映射到任何静态槽位，避免为凑数硬塞。",
        "sentences": [
            ("fes_parent_script_01", 0),
            ("fes_parent_script_01", 1),
            ("fes_parent_script_01", 2),
            ("fes_parent_script_01", 3),
            ("fes_parent_script_01", 5),
        ],
    },
]

FM_TMPL = """---
id: {id}
type: explanatory
audience: parent
scenario: parent_escalation
exec_target: 情绪调节
evidence_level: C
contraindication_flag: {flag}
last_reviewed: 2026-11-13
source_id: parent_cool
source_version: "2026-11-13"
template_ref: PT_PARENT_ESCALATION_01
proposal_ref: PROP-0005
when:
  parent_affect_level: [low, mid, high]
inject_text: |
{text}---
"""

BODY_TMPL = """
# {id}

{title}

- **字段依据**：`PROP-0004`（`parent_affect_level` 进 `when` 白名单）；
  **场景依据**：`PROP-0005`（`parent_escalation` + `PT_PARENT_ESCALATION_01`）。
  后者写在 `proposal_ref`，前者在本行留痕，双向可追溯。
- **来源**：`parent_cool` 接入卡（`project_internal`，原文不在手）。
  `inject_text` 的每一句逐字取自现有 18 条源条目，由
  `03_agent编译/derive_batch3_entries.py` 按句序号机械拼接，未改写、未概括、未新增。
- **槽位**：{slot_line}
- **语义边界**：{boundary}
  现有 18 条全为学科辅导支架，本条是「逐字摘句重组 + 新场景标签」，
  **不构成家长火气 1—5 分档内容**；分档话术、五类身体预警表、修复话术、
  免责声明原文均无来源，按不编造纪律在 `copy_mapping.json` 保留
  `pending_batch3` 占位。

## 逐句来源（可复跑比对）

| 句序 | 来源条目 | 原句序号 |
|---|---|---|
{rows}

- 类型 `explanatory`、无 `callable`、无 `exit_when`，只进 `chunks.jsonl`，
  不产 `skill_registry.json` 条目。
- `when` 严格套模板零偏离；三档全命中，条目级不做内容分档
  （如需分档须收窄 `when` 并记 `value_adjusted`，见 PROP-0005 known_risk）。
"""


def load_stock_texts():
    """只取存量 18 条（排除本批次新增），作为唯一可引用文案池。"""
    texts = {}
    with open(CHUNKS, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            # chunks.jsonl 不含 source_id，用既知存量 id 前缀 + 场景过滤
            if row["scenario"] == "parent_escalation":
                continue
            texts[row["id"]] = row["inject_text"]
    return texts


def split_sentences(text):
    return [p.strip() for p in text.replace("\n", "").split("。")]


def main():
    stock = load_stock_texts()
    if len(stock) != 18:
        print(f"[derive] 存量文案池应为 18 条，实际 {len(stock)}")
        return 1
    os.makedirs(OUT_DIR, exist_ok=True)

    for d in DERIVATIONS:
        parts, rows = [], []
        for i, (src, idx) in enumerate(d["sentences"], 1):
            if src not in stock:
                print(f"[derive] {d['id']} 引用了不存在的来源条目 {src}")
                return 1
            segs = split_sentences(stock[src])
            if idx >= len(segs) or not segs[idx]:
                print(f"[derive] {d['id']} 句序号越界：{src}[{idx}]")
                return 1
            seg = segs[idx]
            # 逐字可溯断言：片段必是某条存量 inject_text 的连续子串
            if not any(seg in t for t in stock.values()):
                print(f"[derive] {d['id']} 第 {i} 句非逐字可溯：{seg[:40]}")
                return 1
            parts.append(seg)
            rows.append(f"| {i} | `{src}` | [{idx}] |")

        inject_text = "。".join(parts) + "。\n"
        text_block = "".join("  " + ln + "\n" for ln in inject_text.rstrip("\n").split("\n"))
        fm = FM_TMPL.format(id=d["id"], flag=d["flag"], text=text_block)
        slot_line = (f"`{d['slot']}`（批次 3 回填为 mapped）" if d["slot"]
                     else "无（纯运行时 `ai_line` 检索候选，不占静态槽位）")
        body = BODY_TMPL.format(
            id=d["id"], title=d["title"], slot_line=slot_line,
            boundary=d["boundary"], rows="\n".join(rows))
        path = os.path.join(OUT_DIR, d["id"] + ".md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(fm + body)

        # 回读校验：frontmatter 可解析、when 是列表、无 callable / exit_when
        sys.path.insert(0, os.path.join(HERE, "validators"))
        from _common import parse_frontmatter
        with open(path, encoding="utf-8") as f:
            got = parse_frontmatter(f.read())
        if not isinstance(got, dict) or got.get("scenario") != "parent_escalation":
            print(f"[derive] {d['id']} frontmatter 回读失败")
            return 1
        if not isinstance(got["when"]["parent_affect_level"], list):
            print(f"[derive] {d['id']} when 未写成列表（op=in）")
            return 1
        if "callable" in got or "exit_when" in got:
            print(f"[derive] {d['id']} 解释性条目不得含 callable / exit_when")
            return 1
        print(f"  [OK] {d['id']}  句数={len(parts)}  slot={d['slot'] or '—'}")

    print(f"[derive] 6 条 explanatory 条目写出 → {OUT_DIR}；逐字可溯断言全通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
