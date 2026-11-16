---
id: parent_wm_externalize_01
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
when:
  task_phase: [理解, 计划, 执行]
  wm_load: ">=2"
  ownership: [parent-hinting, child-leading]
exit_when:
  wm_load: "<=1"
  consecutive_successes: ">=1"
inject_text: |
  把口头布置的作业拆成「第一题、第二题」两步说，不要一次性说完整页。作业量先减一半，允许他只做单数题，做完再追加，别当众说「你少做」。在他最有把握的题旁边写个箭头放最前面。书面比口头可靠，写在黑板固定一角，他不会漏听。用「选做题」的方式公开，他不觉得被特殊对待。
callable:
  name: chunk_homework
  params: {reduce_ratio: "enum(0.5, 0.3)"}
  returns: {script: string, avoid: string}
  side_effect: none
---

# parent_wm_externalize_01

派生自：B09_给ADHD孩子布置作业（降难度拆分改要求）。

面向家长 · 工作记忆外置（作业拆分降难度）。
