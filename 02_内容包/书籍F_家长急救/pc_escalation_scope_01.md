---
id: pc_escalation_scope_01
type: explanatory
audience: parent
scenario: parent_escalation
exec_target: 情绪调节
evidence_level: C
contraindication_flag: safe
last_reviewed: 2026-11-14
source_id: parent_cool
source_version: "2026-11-13"
template_ref: PT_PARENT_ESCALATION_01
proposal_ref: PROP-0005
when:
  parent_affect_level: [mid]
deviation:
  kind: value_adjusted
  reason: "parent_affect_level 按档位收窄（[low, mid, high] → [mid]，批次 5 关闭 D-06）：今晚不铺开、按情绪先处理，属中断铺开式冲突的暂停收窄，仅 mid 档触发"
inject_text: |
  手上没有记录、也不清楚今晚发生了什么时，别先给通用建议。①请家长只讲最近一次的具体场景：哪天的哪一科、孩子当时说了什么、你回了哪一句。今晚不铺开到作业习惯、屏幕时间或家校沟通。场景收得越窄，给的动作越能当场用上。区分不出是能力还是情绪时，按情绪先处理，不追问原因。
---

# pc_escalation_scope_01

只讲最近一次具体场景，不铺开到习惯与作息

- **字段依据**：`PROP-0004`（`parent_affect_level` 进 `when` 白名单）；
  **场景依据**：`PROP-0005`（`parent_escalation` + `PT_PARENT_ESCALATION_01`）。
  后者写在 `proposal_ref`，前者在本行留痕，双向可追溯。
- **来源**：`parent_cool` 接入卡（`project_internal`，原文不在手）。
  `inject_text` 的每一句逐字取自现有 18 条源条目，由
  `03_agent编译/derive_batch3_entries.py` 按句序号机械拼接，未改写、未概括、未新增。
- **槽位**：`script_card_10`（批次 3 回填为 mapped）
- **语义边界**：场景收窄与按情绪先处理；不构成火气分级。
  现有 18 条全为学科辅导支架，本条是「逐字摘句重组 + 新场景标签」，
  **不构成家长火气 1—5 分档内容**；分档话术、五类身体预警表、修复话术、
  免责声明原文均无来源，按不编造纪律在 `copy_mapping.json` 保留
  `pending_batch3` 占位。

## 逐句来源（可复跑比对）

| 句序 | 来源条目 | 原句序号 |
|---|---|---|
| 1 | `fes_parent_single_scene_01` | [0] |
| 2 | `fes_parent_single_scene_01` | [1] |
| 3 | `fes_parent_single_scene_01` | [4] |
| 4 | `fes_parent_single_scene_01` | [7] |
| 5 | `fes_parent_settle_01` | [8] |

- 类型 `explanatory`、无 `callable`、无 `exit_when`，只进 `chunks.jsonl`，
  不产 `skill_registry.json` 条目。
- `when` 批次 5 按档位收窄为 `[mid]`（分档依据：今晚不铺开、按情绪先处理，中断铺开式冲突），
  相对模板为取值子集，条目显式记 `deviation: value_adjusted`（reason 见 front matter），
  单列不进主偏离率；关闭 D-06，三档分布 low=no_label/restate、mid=one_step/scope、
  high=stop/refer（各 2 条），与 golden `tr_PE01..PE06` 逐条一致。
