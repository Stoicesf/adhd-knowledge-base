---
id: pc_warning_muscle_01
type: explanatory
audience: parent
scenario: parent_escalation
exec_target: 情绪调节
evidence_level: C
contraindication_flag: caution
last_reviewed: 2026-11-15
source_id: fhs_hk_anger_management
source_version: "2026-11-15"
template_ref: PT_PARENT_ESCALATION_01
proposal_ref: PROP-0007
when:
  parent_affect_level: [low, mid, high]
inject_text: |
  肌肉繃緊。手心出汗。慢慢地呼吸。在吸氣時心裡默念 1，呼氣時放鬆身體。分散注意力。
---

# pc_warning_muscle_01

肌肉预警：紧绷时先放松身体

- **字段依据**：`PROP-0007`（批次 8 授权抓取来源接入）；
  **场景依据**：`PROP-0005`（`parent_escalation` + `PT_PARENT_ESCALATION_01`）。
  **来源**：`fhs_hk_anger_management` 接入卡。
  `inject_text` 的每一句逐字取自 `00_来源治理/_staging/` 对应中文原文，由
  `03_agent编译/derive_batch8_entries.py` 机械摘取，未改写、未概括、未新增。
- **槽位**：`warning_signs_肌肉`（批次 8 回填为 mapped）
- **语义边界**：信号逐字取 fhs「肌肉繃緊」；动作逐字取 fhs「慢慢地呼吸…放鬆身體」。
  本条目是「逐字摘句重组 + 家长火气场景标签」，只作五类预警/修复的
  参考文案；信号与动作分列，动作列逐字取自中文来源，不逐类编造。
  英文来源（NHS / PKJ / CalmHome）仅 _staging 留痕作参照，不派生。
- `when` 严格套模板三档 `[low, mid, high]`（不单档化，理由见 PROP-0007）；
  五类预警与修复卡是**火气上升/事后**的通用参考，不按火气 1—5 分档。

## 逐句来源（可复跑比对）

| 句序 | 来源 staging 文件 | 逐字片段 |
|---|---|---|
| 1 | `fhs_gov_hk_parent_anger_management_tc_2026-11-15.md` | 肌肉繃緊 |
| 2 | `fhs_gov_hk_parent_anger_management_tc_2026-11-15.md` | 手心出汗 |
| 3 | `fhs_gov_hk_parent_anger_management_tc_2026-11-15.md` | 慢慢地呼吸 |
| 4 | `fhs_gov_hk_parent_anger_management_tc_2026-11-15.md` | 在吸氣時心裡默念 1，呼氣時放鬆身體 |
| 5 | `fhs_gov_hk_parent_anger_management_tc_2026-11-15.md` | 分散注意力 |

- 类型 `explanatory`、无 `callable`、无 `exit_when`，只进 `chunks.jsonl`，
  不产 `skill_registry.json` 条目。
