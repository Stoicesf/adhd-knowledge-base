---
id: parent_drift_explain_02
type: explanatory
audience: parent
scenario: attention_drift
exec_target: 启动
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
  task_phase: [启动, 执行]
  attention_state: [drift, re-entry]
  ownership: [child-leading, parent-hinting]
inject_text: |
  ADHD 孩子负责启动任务、忍住冲动、估计时间的那套能力本身就偏弱。一整页 20 题、一段口头要求、一篇 300 字作文，在他眼里都是一团模糊的东西，他不知道从哪儿下第一笔，于是干脆发呆、玩橡皮、离座。任务切到他一眼能看懂的一小步，他才迈得动第一步。
---

# parent_drift_explain_02

派生自：B01 / B09 ·「为什么这样做有效」的执行功能机制段落。

面向家长 · 解释性（检索块）：启动困难与任务结构化的原理。
