---
id: parent_wm_externalize_02
type: procedural
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
  reason: "字段 attention_state 取值超出模板（{'attention_state': ['drift', 're-entry']} → {'attention_state': ['drift', 'on-task']}）"
when:
  task_phase: [理解]
  attention_state: [drift, on-task]
  ownership: [child-leading, parent-hinting]
exit_when:
  attention_state: [on-task]
  consecutive_successes: ">=1"
inject_text: |
  你说完一件事，停 2 秒，不催。请他用自己的话复述一句：「你的意思是……」。你只答两种：「对，就是这个」或「差一点，是……」，不展开评价。一次只交代一件事，复述只用在重要的事上，不要每句话都让他背。复述是在对话里设一个注意力落点，比说「认真听」有效得多——后者只会让他内疚，什么都不改变。
callable:
  name: repeat_back
  params: {mode: "enum(confirm, written)"}
  returns: {script: string, avoid: string}
  side_effect: none
---

# parent_wm_externalize_02

派生自：B15_伴侣总被说没在听（对话中留复述动作）·「复述锚定注意力」。

面向家长 · 工作记忆外置（复述动作，对话中锚定注意力）。
