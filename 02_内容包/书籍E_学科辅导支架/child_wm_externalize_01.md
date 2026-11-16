---
id: child_wm_externalize_01
type: procedural
audience: child
scenario: wm_overload
exec_target: 工作记忆
evidence_level: B
contraindication_flag: safe
last_reviewed: 2026-11-12
source_id: project_original
source_version: "2026-11"
template_ref: PT_WM_01
when:
  task_phase: [计划, 执行]
  wm_load: ">=2"
  ownership: [child-leading]
exit_when:
  wm_load: "<=1"
  consecutive_successes: ">=2"
inject_text: |
  微步骤：①把今天的作业写在纸条最上面，只写三件事。②做完一件，划掉一件。③卡住时，把「我现在卡在＿＿＿」说给家长听。不要全记在脑子里——脑子同时挂好几件待办会漏。一处收口比用很多 App 更靠谱。
callable:
  name: child_externalize_list
  params: {}
  returns: {next_step: string, done_signal: string}
  side_effect: none
---

# child_wm_externalize_01

派生自：B14_外部提醒分工（一处收口）/ B09（书面比口头可靠）的儿童端版。

面向儿童 · 工作记忆外置（外部清单，不靠脑子硬扛）。
