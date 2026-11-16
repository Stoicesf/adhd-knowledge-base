---
id: pc_escalation_no_label_01
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
  reason: "parent_affect_level 按档位收窄（[low, mid, high] → [low]，批次 5 关闭 D-06）：话术为换说法的温和提醒，不要求暂停或离开现场，仅 low 档触发"
inject_text: |
  同一句提醒，换个说法，孩子接到的信息完全不同。「你怎么又走神了」是给他下一个结论；「这一行我们再看一次」是给他一个能做的动作。命令式和贴标签的话会把今晚的作业变成一场关于「他是什么样的人」的争论，而这类评价他在学校往往已经听了一整天，回家再听一次，起步的成本会更高。可照着说的句式是：先说你看到的具体动作（「笔停在这儿了」），再说一个下一步（「把第一句的关键词指给我」），最后停住，不追加评价和追问。话术只解决当下这一句，不翻旧账、不预测明天。
---

# pc_escalation_no_label_01

同一句提醒换个说法，不下结论不贴标签

- **字段依据**：`PROP-0004`（`parent_affect_level` 进 `when` 白名单）；
  **场景依据**：`PROP-0005`（`parent_escalation` + `PT_PARENT_ESCALATION_01`）。
  后者写在 `proposal_ref`，前者在本行留痕，双向可追溯。
- **来源**：`parent_cool` 接入卡（`project_internal`，原文不在手）。
  `inject_text` 的每一句逐字取自现有 18 条源条目，由
  `03_agent编译/derive_batch3_entries.py` 按句序号机械拼接，未改写、未概括、未新增。
- **槽位**：无（纯运行时 `ai_line` 检索候选，不占静态槽位）
- **语义边界**：第 6 条只服务 ai_line 动态检索，不映射到任何静态槽位，避免为凑数硬塞。
  现有 18 条全为学科辅导支架，本条是「逐字摘句重组 + 新场景标签」，
  **不构成家长火气 1—5 分档内容**；分档话术、五类身体预警表、修复话术、
  免责声明原文均无来源，按不编造纪律在 `copy_mapping.json` 保留
  `pending_batch3` 占位。

## 逐句来源（可复跑比对）

| 句序 | 来源条目 | 原句序号 |
|---|---|---|
| 1 | `fes_parent_script_01` | [0] |
| 2 | `fes_parent_script_01` | [1] |
| 3 | `fes_parent_script_01` | [2] |
| 4 | `fes_parent_script_01` | [3] |
| 5 | `fes_parent_script_01` | [5] |

- 类型 `explanatory`、无 `callable`、无 `exit_when`，只进 `chunks.jsonl`，
  不产 `skill_registry.json` 条目。
- `when` 批次 5 按档位收窄为 `[low]`（分档依据：换说法的温和提醒，不涉及暂停/离开），
  相对模板为取值子集，条目显式记 `deviation: value_adjusted`（reason 见 front matter），
  单列不进主偏离率；关闭 D-06，三档分布 low=no_label/restate、mid=one_step/scope、
  high=stop/refer（各 2 条），与 golden `tr_PE01..PE06` 逐条一致。
