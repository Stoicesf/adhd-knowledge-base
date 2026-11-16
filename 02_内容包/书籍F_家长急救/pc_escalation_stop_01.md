---
id: pc_escalation_stop_01
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
  reason: "parent_affect_level 按档位收窄（[low, mid, high] → [high]，批次 5 关闭 D-06）：整个停下、合上作业、离开书桌、当天不再做，属紧急撤离，仅 high 档触发"
inject_text: |
  有一类信号出现时，今晚的学习动作要整个停下，而不是换个更小的任务继续：孩子明显崩溃、长时间哭到说不出话、说伤害自己的话，或家长自己已经压不住火。今晚先不谈整页作业。这时该做的只有两件——先把作业合上、离开书桌，再按来源边界去联系有处方权的医生或学校心理老师，把情况按时间顺序说清楚。可以留一句：「今天先不做了，我们一起去问问专业的人。」复盘点等状态回来之后再定，不在当晚追问原因。
---

# pc_escalation_stop_01

出现压不住火的信号就整个停下、离开书桌

- **字段依据**：`PROP-0004`（`parent_affect_level` 进 `when` 白名单）；
  **场景依据**：`PROP-0005`（`parent_escalation` + `PT_PARENT_ESCALATION_01`）。
  后者写在 `proposal_ref`，前者在本行留痕，双向可追溯。
- **来源**：`parent_cool` 接入卡（`project_internal`，原文不在手）。
  `inject_text` 的每一句逐字取自现有 18 条源条目，由
  `03_agent编译/derive_batch3_entries.py` 按句序号机械拼接，未改写、未概括、未新增。
- **槽位**：`script_card_09`（批次 3 回填为 mapped）
- **语义边界**：含专业转介边界；本句原文写的是「孩子明显崩溃…或家长自己已经压不住火」，未改写为家长身体预警。
  现有 18 条全为学科辅导支架，本条是「逐字摘句重组 + 新场景标签」，
  **不构成家长火气 1—5 分档内容**；分档话术、五类身体预警表、修复话术、
  免责声明原文均无来源，按不编造纪律在 `copy_mapping.json` 保留
  `pending_batch3` 占位。

## 逐句来源（可复跑比对）

| 句序 | 来源条目 | 原句序号 |
|---|---|---|
| 1 | `fes_parent_pause_signal_01` | [0] |
| 2 | `fes_parent_settle_01` | [0] |
| 3 | `fes_parent_pause_signal_01` | [1] |
| 4 | `fes_parent_pause_signal_01` | [3] |
| 5 | `fes_parent_pause_signal_01` | [4] |

- 类型 `explanatory`、无 `callable`、无 `exit_when`，只进 `chunks.jsonl`，
  不产 `skill_registry.json` 条目。
- `when` 批次 5 按档位收窄为 `[high]`（分档依据：整个停下、合上作业、离开书桌、当天不再做），
  相对模板为取值子集，条目显式记 `deviation: value_adjusted`（reason 见 front matter），
  单列不进主偏离率；关闭 D-06，三档分布 low=no_label/restate、mid=one_step/scope、
  high=stop/refer（各 2 条），与 golden `tr_PE01..PE06` 逐条一致。
