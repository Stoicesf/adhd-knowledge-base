---
id: parent_wm_explain_02
type: explanatory
audience: parent
scenario: wm_overload
exec_target: 启动
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
  task_phase: [启动, 计划, 执行]
  wm_load: ">=1"
  attention_state: [drift, re-entry]
  ownership: [child-leading, parent-hinting]
inject_text: |
  一整页 20 题、一段口头要求、一篇 300 字作文，在他眼里都是一团模糊的东西，他不知道从哪儿下第一笔，于是发呆、玩橡皮、离座。你把任务拆到一眼能看懂的一小步，他才迈得动第一步。作业量减一半不是纵容，是让他保留「我做完了」的体验——他长期在「我又没写完」里，最缺的就是这种体验。
---

# parent_wm_explain_02

派生自：B09_给ADHD孩子布置作业 ·「为什么这样做有效」段落。

面向家长 · 解释性（检索块）：拆解认知负荷与启动门槛的原理。
