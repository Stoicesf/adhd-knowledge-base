---
id: parent_wm_explain_01
type: explanatory
audience: parent
scenario: wm_overload
exec_target: 工作记忆
evidence_level: B
contraindication_flag: safe
last_reviewed: 2026-11-12
source_id: project_original
source_version: "2026-11"
template_ref: PT_WM_01
deviation:
  kind: value_adjusted
  reason: "字段 wm_load 取值超出模板（{'wm_load': '>=2'} → {'wm_load': '>=1'}）"
when:
  task_phase: [理解, 计划, 执行]
  wm_load: ">=1"
  attention_state: [drift, re-entry]
  ownership: [child-leading, parent-hinting]
inject_text: |
  一个人脑子里同时挂好几件待办，等于同时当调度员和办事员——记不住不是不上心，是「记性工作」本就不该放在脑子里。外部提醒分工的核心，是把记忆从两个人的脑子里挪到外部系统。一处收口比工具高级重要：多处记等于没记。
---

# parent_wm_explain_01

派生自：B14_伴侣忘事不是态度问题（一周外部提醒分工）·「记忆挪到外部系统 / 一处收口」。

面向家长 · 解释性（检索块）：为什么工作记忆要外置。
