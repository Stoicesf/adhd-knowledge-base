# -*- coding: utf-8 -*-
"""阶段 B 批次 8 · 书籍F 源条目派生脚本（修复卡 + 五类预警；逐字可溯、可证伪）

背景：6 个 pending_batch3 槽位（repair_card_01 + warning_signs_呼吸/肌肉/声音/
胸口/念头）在批次 3/5 均无来源。批次 8 用户授权走 B 路线：抓取外部来源逐字落
00_来源治理/_staging/ 留 SHA256，本脚本从中文来源逐字摘句生成 6 条 explanatory
源条目。

语言裁决（用户批次 8 拍板「中文派生 + 英文留痕」）：
  - 中文来源（fhs_hk_anger_management / aiadhd_yell_repair）→ 逐字派生；
  - 英文来源（nhs_inform / pkjcoaching / calmhome）→ 仅 _staging 留痕作参照，
    不派生（面向中文家长的工具，英文话术不直接进 inject_text）。

纪律（与 derive_batch3_entries.py 同源）：
  - 不编造：inject_text 的每一句必须是某份 staging 原文的逐字子串；
  - 不手写文案：只按 (来源文件, 逐字片段) 机械摘取，片段间用中文句号「。」拼接；
  - parent_escalation_tests.py 用独立的「不编造断言」再验一遍，可证伪。

用法：E:/ANACONDA/python.exe 03_agent编译/derive_batch8_entries.py
输出：02_内容包/书籍F_家长急救/*.md（6 条 explanatory 条目）
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT_DIR = os.path.join(ROOT, "02_内容包", "书籍F_家长急救")
STAGING = os.path.join(ROOT, "00_来源治理", "_staging")

SRC_FILES = {
    "fhs": "fhs_gov_hk_parent_anger_management_tc_2026-11-15.md",
    "aiadhd": "aiadhd_yell_repair_2026-11-15.md",
}

# 每条新条目：从中文来源摘哪几句（逐字子串，精确匹配）。
# 片段须是 staging 原文（规范化换行→空格后）的连续子串；片段间用「。」拼接。
DERIVATIONS = [
    {
        "id": "pc_repair_card_01",
        "slot": "repair_card_01",
        "source_id": "aiadhd_yell_repair",
        "flag": "safe",
        "title": "发火之后为行为道歉、不翻旧账",
        "boundary": "修复卡核心话术；逐字取 aiadhd 中文篇「为行为而非情绪道歉」+ fhs「为发怒行为道歉」。",
        "sentences": [
            ("aiadhd", "对不起，刚才妈妈/爸爸没有控制好自己的脾气，对你大吼大叫了。我感到很生气，但这不能成为我伤害你的理由。我爱你。"),
            ("fhs", "對不起，即使我很生氣，我也不應該大聲罵你的"),
            ("aiadhd", "为您的\"行为\"而非您的\"情绪\"道歉"),
            ("fhs", "待雙方冷靜過後，向彼此說出自己的感受和想法"),
            ("aiadhd", "爱，并非意味着永不犯错，而是在风暴过后，永远有勇气回来，重新拥抱。"),
        ],
    },
    {
        "id": "pc_warning_breath_01",
        "slot": "warning_signs_呼吸",
        "source_id": "fhs_hk_anger_management",
        "flag": "caution",
        "title": "呼吸预警：呼吸短浅时先慢慢呼吸",
        "boundary": "信号逐字取 fhs「呼吸短而淺」；动作逐字取 fhs「慢慢地呼吸」红绿灯建议。",
        "sentences": [
            ("fhs", "呼吸短而淺"),
            ("fhs", "心跳加速"),
            ("fhs", "慢慢地呼吸"),
            ("fhs", "平復心跳及呼吸的頻率，幫助放鬆"),
            ("aiadhd", "将手放在心脏的位置，做三次缓慢、深长的腹式呼吸"),
        ],
    },
    {
        "id": "pc_warning_muscle_01",
        "slot": "warning_signs_肌肉",
        "source_id": "fhs_hk_anger_management",
        "flag": "caution",
        "title": "肌肉预警：紧绷时先放松身体",
        "boundary": "信号逐字取 fhs「肌肉繃緊」；动作逐字取 fhs「慢慢地呼吸…放鬆身體」。",
        "sentences": [
            ("fhs", "肌肉繃緊"),
            ("fhs", "手心出汗"),
            ("fhs", "慢慢地呼吸"),
            ("fhs", "在吸氣時心裡默念 1，呼氣時放鬆身體"),
            ("fhs", "分散注意力"),
        ],
    },
    {
        "id": "pc_warning_voice_01",
        "slot": "warning_signs_声音",
        "source_id": "fhs_hk_anger_management",
        "flag": "caution",
        "title": "声音预警：声线提高时先离开现场",
        "boundary": "信号逐字取 fhs「聲線提高」；动作逐字取 fhs「離開現場…分散注意力」。",
        "sentences": [
            ("fhs", "聲線提高"),
            ("fhs", "面紅耳熱"),
            ("fhs", "離開現場，減少環境帶來的情緒刺激"),
            ("fhs", "分散注意力"),
            ("aiadhd", "我现在感觉非常生气，我需要去另一个房间冷静两分钟，我们稍后再谈。"),
        ],
    },
    {
        "id": "pc_warning_chest_01",
        "slot": "warning_signs_胸口",
        "source_id": "fhs_hk_anger_management",
        "flag": "caution",
        "title": "胸口预警：胸闷时缓慢呼吸平复",
        "boundary": "信号逐字取 fhs「胸悶」；动作逐字取 fhs「慢慢地呼吸…平復心跳」。",
        "sentences": [
            ("fhs", "胸悶"),
            ("fhs", "手心出汗"),
            ("fhs", "慢慢地呼吸"),
            ("fhs", "平復心跳及呼吸的頻率，幫助放鬆"),
            ("aiadhd", "用冷水冲洗一下手腕和脸部"),
        ],
    },
    {
        "id": "pc_warning_thought_01",
        "slot": "warning_signs_念头",
        "source_id": "fhs_hk_anger_management",
        "flag": "caution",
        "title": "念头预警：灾难化念头出现时先停下想一想",
        "boundary": "信号逐字取 fhs「災難化」；动作逐字取 fhs「想一想…提出合理的證據」。",
        "sentences": [
            ("fhs", "災難化"),
            ("fhs", "天啊！我永遠都教不好孩子！"),
            ("fhs", "仔細想一想情緒出現的原因"),
            ("fhs", "嘗試提出合理的證據來加以證實自己的一些不合理的想法"),
            ("aiadhd", "在我爆发的前一秒，我脑子里闪过的那个'热念头'是什么"),
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
last_reviewed: 2026-11-15
source_id: {source_id}
source_version: "2026-11-15"
template_ref: PT_PARENT_ESCALATION_01
proposal_ref: PROP-0007
when:
  parent_affect_level: [low, mid, high]
inject_text: |
{text}---
"""

BODY_TMPL = """
# {id}

{title}

- **字段依据**：`PROP-0007`（批次 8 授权抓取来源接入）；
  **场景依据**：`PROP-0005`（`parent_escalation` + `PT_PARENT_ESCALATION_01`）。
  **来源**：`{source_id}` 接入卡。
  `inject_text` 的每一句逐字取自 `00_来源治理/_staging/` 对应中文原文，由
  `03_agent编译/derive_batch8_entries.py` 机械摘取，未改写、未概括、未新增。
- **槽位**：`{slot}`（批次 8 回填为 mapped）
- **语义边界**：{boundary}
  本条目是「逐字摘句重组 + 家长火气场景标签」，只作五类预警/修复的
  参考文案；信号与动作分列，动作列逐字取自中文来源，不逐类编造。
  英文来源（NHS / PKJ / CalmHome）仅 _staging 留痕作参照，不派生。
- `when` 严格套模板三档 `[low, mid, high]`（不单档化，理由见 PROP-0007）；
  五类预警与修复卡是**火气上升/事后**的通用参考，不按火气 1—5 分档。

## 逐句来源（可复跑比对）

| 句序 | 来源 staging 文件 | 逐字片段 |
|---|---|---|
{rows}

- 类型 `explanatory`、无 `callable`、无 `exit_when`，只进 `chunks.jsonl`，
  不产 `skill_registry.json` 条目。
"""


def load_staging():
    texts = {}
    for key, fn in SRC_FILES.items():
        p = os.path.join(STAGING, fn)
        with open(p, encoding="utf-8") as f:
            texts[key] = f.read()
    return texts


def norm(s):
    return s.replace("\n", " ").strip()


def main():
    texts = load_staging()
    os.makedirs(OUT_DIR, exist_ok=True)

    for d in DERIVATIONS:
        parts, rows = [], []
        for i, (src, seg) in enumerate(d["sentences"], 1):
            body = norm(texts[src])
            # 逐字可溯断言：片段必须是该 staging 原文（规范化后）的连续子串
            if seg not in body:
                print(f"[derive8] {d['id']} 第 {i} 句非逐字可溯：{seg[:40]}")
                return 1
            parts.append(seg)
            rows.append(f"| {i} | `{SRC_FILES[src]}` | {seg[:40]} |")

        # 拼接：片段若已以中文句号结尾则不重复加（避免「。。」瑕疵）
        inject_text = ""
        for part in parts:
            if inject_text and not inject_text.endswith("。"):
                inject_text += "。"
            inject_text += part
        if not inject_text.endswith("。"):
            inject_text += "。"
        inject_text += "\n"
        text_block = "".join("  " + ln + "\n" for ln in inject_text.rstrip("\n").split("\n"))
        fm = FM_TMPL.format(id=d["id"], flag=d["flag"],
                            source_id=d["source_id"], text=text_block)
        body = BODY_TMPL.format(
            id=d["id"], title=d["title"], slot=d["slot"],
            source_id=d["source_id"], boundary=d["boundary"],
            rows="\n".join(rows))
        path = os.path.join(OUT_DIR, d["id"] + ".md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(fm + body)
        print(f"  [OK] {d['id']}  句数={len(parts)}  slot={d['slot']}  src={d['source_id']}")

    print(f"[derive8] 6 条 explanatory 条目写出 → {OUT_DIR}；逐字可溯断言全通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
