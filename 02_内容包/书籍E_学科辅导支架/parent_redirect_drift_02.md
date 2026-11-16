---
id: parent_redirect_drift_02
type: procedural
audience: parent
scenario: attention_drift
exec_target: 启动
evidence_level: B
contraindication_flag: safe
last_reviewed: 2026-11-12
source_id: project_original
source_version: "2026-11"
template_ref: PT_DRIFT_01
when:
  task_phase: [执行]
  attention_state: [drift]
  ownership: [parent-hinting]
exit_when:
  attention_state: [on-task]
  consecutive_successes: ">=1"
inject_text: |
  把「专心写」换成「现在写第一题」。一次只说一条指令，等他做完、复述一遍，再说下一条，不要连着甩出三条。他负责启动任务的能力偏弱，任务切到一眼能看懂的一小步，他才迈得动第一步。你多提醒几遍，他越不需要自己启动，越依赖你催。先用行为记录表看离座次数有没有变化，再决定下一步。
callable:
  name: single_instruction
  params: {}
  returns: {script: string, avoid: string}
  side_effect: none
---

# parent_redirect_drift_02

派生自：B01_写作业频繁离座 ·「把专心写换成现在写第一题 / 指令一次一条 / 复述」

面向家长 · 走神时的单步指令策略。
