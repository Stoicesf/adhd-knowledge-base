---
id: parent_drift_explain_01
type: explanatory
audience: parent
scenario: attention_drift
exec_target: 抑制控制
evidence_level: B
contraindication_flag: safe
last_reviewed: 2026-11-12
source_id: project_original
source_version: "2026-11"
template_ref: PT_DRIFT_01
deviation:
  kind: value_adjusted
  reason: "字段 attention_state 取值超出模板（{'attention_state': ['drift']} → {'attention_state': ['drift', 're-entry']}）"
when:
  task_phase: [执行]
  attention_state: [drift, re-entry]
  ownership: [child-leading, parent-hinting]
inject_text: |
  孩子频繁离座，通常不是「不想坐住」，而是桌面上每一样多余的东西都在和作业抢注意力。一块橡皮、一张贴纸、旁边经过的人、同时出口的三条指令，对他来说都是新的待办事项。你把环境改简单，等于替他把这些待办提前删掉——需要他主动忍住的冲动变少了，椅子自然就坐得住。任务切到他一眼能看懂的一小步，他才迈得动第一步。
---

# parent_drift_explain_01

派生自：B01_写作业频繁离座 ·「为什么这样做有效」段落。

面向家长 · 解释性（检索块，无 callable）：解释走神/离座的执行功能机制。
