---
id: pc_escalation_restate_01
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
  parent_affect_level: [low]
deviation:
  kind: value_adjusted
  reason: "parent_affect_level 按档位收窄（[low, mid, high] → [low]，批次 5 关闭 D-06）：先复述降温、不急于给办法，不要求暂停或离开现场，仅 low 档触发"
inject_text: |
  先别急着给办法。把家长刚才说的那句困扰照原样复述一遍：「你是说，今晚数学错题一多，他就趴下不写了，你不知道该不该让他继续，是这样吗？」这一步不是为了安慰，是为了把「任务太难」「能力还没跟上」「情绪已经上来」「两个人说岔了」这四种情况分开。它们长得像，处理方式完全不同：任务问题要拆小，能力问题要降要求，情绪问题要先降温，沟通问题要换说法。复述被家长确认后再往下走，每一步都只对应当晚这一个具体场景。话术只解决当下这一句，不翻旧账、不预测明天。
---

# pc_escalation_restate_01

火气上来时先复述，别急着给办法

- **字段依据**：`PROP-0004`（`parent_affect_level` 进 `when` 白名单）；
  **场景依据**：`PROP-0005`（`parent_escalation` + `PT_PARENT_ESCALATION_01`）。
  后者写在 `proposal_ref`，前者在本行留痕，双向可追溯。
- **来源**：`parent_cool` 接入卡（`project_internal`，原文不在手）。
  `inject_text` 的每一句逐字取自现有 18 条源条目，由
  `03_agent编译/derive_batch3_entries.py` 按句序号机械拼接，未改写、未概括、未新增。
- **槽位**：`script_card_08`（批次 3 回填为 mapped）
- **语义边界**：复述与分辨四类情况；不宣称按火气 1—5 分档。
  现有 18 条全为学科辅导支架，本条是「逐字摘句重组 + 新场景标签」，
  **不构成家长火气 1—5 分档内容**；分档话术、五类身体预警表、修复话术、
  免责声明原文均无来源，按不编造纪律在 `copy_mapping.json` 保留
  `pending_batch3` 占位。

## 逐句来源（可复跑比对）

| 句序 | 来源条目 | 原句序号 |
|---|---|---|
| 1 | `fes_parent_restate_01` | [0] |
| 2 | `fes_parent_restate_01` | [1] |
| 3 | `fes_parent_restate_01` | [2] |
| 4 | `fes_parent_restate_01` | [4] |
| 5 | `fes_parent_script_01` | [5] |

- 类型 `explanatory`、无 `callable`、无 `exit_when`，只进 `chunks.jsonl`，
  不产 `skill_registry.json` 条目。
- `when` 批次 5 按档位收窄为 `[low]`（分档依据：先复述降温、不急于给办法，不涉及暂停/离开），
  相对模板为取值子集，条目显式记 `deviation: value_adjusted`（reason 见 front matter），
  单列不进主偏离率；关闭 D-06，三档分布 low=no_label/restate、mid=one_step/scope、
  high=stop/refer（各 2 条），与 golden `tr_PE01..PE06` 逐条一致。
