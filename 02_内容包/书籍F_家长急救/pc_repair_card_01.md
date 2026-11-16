---
id: pc_repair_card_01
type: explanatory
audience: parent
scenario: parent_escalation
exec_target: 情绪调节
evidence_level: C
contraindication_flag: safe
last_reviewed: 2026-11-15
source_id: aiadhd_yell_repair
source_version: "2026-11-15"
template_ref: PT_PARENT_ESCALATION_01
proposal_ref: PROP-0007
when:
  parent_affect_level: [low, mid, high]
inject_text: |
  对不起，刚才妈妈/爸爸没有控制好自己的脾气，对你大吼大叫了。我感到很生气，但这不能成为我伤害你的理由。我爱你。對不起，即使我很生氣，我也不應該大聲罵你的。为您的"行为"而非您的"情绪"道歉。待雙方冷靜過後，向彼此說出自己的感受和想法。爱，并非意味着永不犯错，而是在风暴过后，永远有勇气回来，重新拥抱。
---

# pc_repair_card_01

发火之后为行为道歉、不翻旧账

- **字段依据**：`PROP-0007`（批次 8 授权抓取来源接入）；
  **场景依据**：`PROP-0005`（`parent_escalation` + `PT_PARENT_ESCALATION_01`）。
  **来源**：`aiadhd_yell_repair` 接入卡。
  `inject_text` 的每一句逐字取自 `00_来源治理/_staging/` 对应中文原文，由
  `03_agent编译/derive_batch8_entries.py` 机械摘取，未改写、未概括、未新增。
- **槽位**：`repair_card_01`（批次 8 回填为 mapped）
- **语义边界**：修复卡核心话术；逐字取 aiadhd 中文篇「为行为而非情绪道歉」+ fhs「为发怒行为道歉」。
  本条目是「逐字摘句重组 + 家长火气场景标签」，只作五类预警/修复的
  参考文案；信号与动作分列，动作列逐字取自中文来源，不逐类编造。
  英文来源（NHS / PKJ / CalmHome）仅 _staging 留痕作参照，不派生。
- `when` 严格套模板三档 `[low, mid, high]`（不单档化，理由见 PROP-0007）；
  五类预警与修复卡是**火气上升/事后**的通用参考，不按火气 1—5 分档。

## 逐句来源（可复跑比对）

| 句序 | 来源 staging 文件 | 逐字片段 |
|---|---|---|
| 1 | `aiadhd_yell_repair_2026-11-15.md` | 对不起，刚才妈妈/爸爸没有控制好自己的脾气，对你大吼大叫了。我感到很生气，但这不 |
| 2 | `fhs_gov_hk_parent_anger_management_tc_2026-11-15.md` | 對不起，即使我很生氣，我也不應該大聲罵你的 |
| 3 | `aiadhd_yell_repair_2026-11-15.md` | 为您的"行为"而非您的"情绪"道歉 |
| 4 | `fhs_gov_hk_parent_anger_management_tc_2026-11-15.md` | 待雙方冷靜過後，向彼此說出自己的感受和想法 |
| 5 | `aiadhd_yell_repair_2026-11-15.md` | 爱，并非意味着永不犯错，而是在风暴过后，永远有勇气回来，重新拥抱。 |

- 类型 `explanatory`、无 `callable`、无 `exit_when`，只进 `chunks.jsonl`，
  不产 `skill_registry.json` 条目。
