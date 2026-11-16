---
id: pc_escalation_one_step_01
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
  reason: "parent_affect_level 按档位收窄（[low, mid, high] → [mid]，批次 5 关闭 D-06）：宣布今晚终点、做完就收，属中断升级的暂停动作，仅 mid 档触发"
inject_text: |
  今晚只留一个任务，标准是「他看一眼愿意开始、一个晚上能收尾」。改用「做完这几步就收」：①把今晚要做的写成本子上的三行短句，一行一个动作；②每做完一行，让他自己划掉；③三行划完就是今晚的终点，不再追加。不追加第二道，不说明天要补回来。等他连着做完这一步、回到题目上，就把话收住，今晚只给这一个动作。边界由「做完」而不是「到点」决定，孩子能看见终点在哪；连着两晚都能按这个收尾，就把它交还给他自己安排。
---

# pc_escalation_one_step_01

今晚只留一个能收尾的动作，做完就收

- **字段依据**：`PROP-0004`（`parent_affect_level` 进 `when` 白名单）；
  **场景依据**：`PROP-0005`（`parent_escalation` + `PT_PARENT_ESCALATION_01`）。
  后者写在 `proposal_ref`，前者在本行留痕，双向可追溯。
- **来源**：`parent_cool` 接入卡（`project_internal`，原文不在手）。
  `inject_text` 的每一句逐字取自现有 18 条源条目，由
  `03_agent编译/derive_batch3_entries.py` 按句序号机械拼接，未改写、未概括、未新增。
- **槽位**：`script_card_11`（批次 3 回填为 mapped）
- **语义边界**：「做完就收」的边界；不替代三档撤退分级文案。
  现有 18 条全为学科辅导支架，本条是「逐字摘句重组 + 新场景标签」，
  **不构成家长火气 1—5 分档内容**；分档话术、五类身体预警表、修复话术、
  免责声明原文均无来源，按不编造纪律在 `copy_mapping.json` 保留
  `pending_batch3` 占位。

## 逐句来源（可复跑比对）

| 句序 | 来源条目 | 原句序号 |
|---|---|---|
| 1 | `fes_parent_low_pressure_01` | [0] |
| 2 | `fes_parent_one_night_scope_01` | [1] |
| 3 | `fes_parent_low_pressure_01` | [2] |
| 4 | `fes_parent_settle_01` | [7] |
| 5 | `fes_parent_one_night_scope_01` | [5] |

- 类型 `explanatory`、无 `callable`、无 `exit_when`，只进 `chunks.jsonl`，
  不产 `skill_registry.json` 条目。
- `when` 批次 5 按档位收窄为 `[mid]`（分档依据：宣布今晚终点、做完就收，中断追加升级），
  相对模板为取值子集，条目显式记 `deviation: value_adjusted`（reason 见 front matter），
  单列不进主偏离率；关闭 D-06，三档分布 low=no_label/restate、mid=one_step/scope、
  high=stop/refer（各 2 条），与 golden `tr_PE01..PE06` 逐条一致。
