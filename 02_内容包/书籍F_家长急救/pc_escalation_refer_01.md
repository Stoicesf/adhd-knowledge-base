---
id: pc_escalation_refer_01
type: explanatory
audience: parent
scenario: parent_escalation
exec_target: 情绪调节
evidence_level: C
contraindication_flag: caution
last_reviewed: 2026-11-14
source_id: parent_cool
source_version: "2026-11-13"
template_ref: PT_PARENT_ESCALATION_01
proposal_ref: PROP-0005
when:
  parent_affect_level: [high]
deviation:
  kind: value_adjusted
  reason: "parent_affect_level 按档位收窄（[low, mid, high] → [high]，批次 5 关闭 D-06）：孩子明显崩溃时不加压学习、转介专业支持，属当天停止加压，仅 high 档触发"
inject_text: |
  这些不是「不配合」，是需要专业支持介入的信号；本库和任何 AI 话术都不能替代专业心理咨询、医学诊断或学校正式评估，也不该在孩子明显崩溃时继续加压学习。可照着说的句式是：先说你看到的具体动作（「笔停在这儿了」），再说一个下一步（「把第一句的关键词指给我」），最后停住，不追加评价和追问。不要说的是「你就是不专心」「你就是不认真」这类定性句。话术只解决当下这一句，不翻旧账、不预测明天。」复盘点等状态回来之后再定，不在当晚追问原因。
---

# pc_escalation_refer_01

专业支持边界与不贴标签的说法

- **字段依据**：`PROP-0004`（`parent_affect_level` 进 `when` 白名单）；
  **场景依据**：`PROP-0005`（`parent_escalation` + `PT_PARENT_ESCALATION_01`）。
  后者写在 `proposal_ref`，前者在本行留痕，双向可追溯。
- **来源**：`parent_cool` 接入卡（`project_internal`，原文不在手）。
  `inject_text` 的每一句逐字取自现有 18 条源条目，由
  `03_agent编译/derive_batch3_entries.py` 按句序号机械拼接，未改写、未概括、未新增。
- **槽位**：`script_card_12`（批次 3 回填为 mapped）
- **语义边界**：沿用本库既有边界句；免责声明原文不在手，未自撰。
  现有 18 条全为学科辅导支架，本条是「逐字摘句重组 + 新场景标签」，
  **不构成家长火气 1—5 分档内容**；分档话术、五类身体预警表、修复话术、
  免责声明原文均无来源，按不编造纪律在 `copy_mapping.json` 保留
  `pending_batch3` 占位。

## 逐句来源（可复跑比对）

| 句序 | 来源条目 | 原句序号 |
|---|---|---|
| 1 | `fes_parent_pause_signal_01` | [2] |
| 2 | `fes_parent_script_01` | [3] |
| 3 | `fes_parent_script_01` | [4] |
| 4 | `fes_parent_script_01` | [5] |
| 5 | `fes_parent_pause_signal_01` | [4] |

- 类型 `explanatory`、无 `callable`、无 `exit_when`，只进 `chunks.jsonl`，
  不产 `skill_registry.json` 条目。
- `when` 批次 5 按档位收窄为 `[high]`（分档依据：孩子明显崩溃时不加压学习、转介专业支持），
  相对模板为取值子集，条目显式记 `deviation: value_adjusted`（reason 见 front matter），
  单列不进主偏离率；关闭 D-06，三档分布 low=no_label/restate、mid=one_step/scope、
  high=stop/refer（各 2 条），与 golden `tr_PE01..PE06` 逐条一致。
