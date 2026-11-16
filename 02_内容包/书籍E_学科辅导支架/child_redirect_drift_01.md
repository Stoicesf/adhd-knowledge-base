---
id: child_redirect_drift_01
type: procedural
audience: child
scenario: attention_drift
exec_target: 抑制控制
evidence_level: B
contraindication_flag: safe
last_reviewed: 2026-11-12
source_id: project_original
source_version: "2026-11"
template_ref: PT_DRIFT_01
when:
  task_phase: [执行]
  attention_state: [drift]
  ownership: [child-leading]
exit_when:
  attention_state: [on-task]
  consecutive_successes: ">=2"
inject_text: |
  微步骤：①把笔放下，看这一题的第一句话。②小声说出「我现在要做的是＿＿＿」。③圈出第一个要算的数。做完这步，举手说「好了」。不要同时想后面三题，一次只攻这一小步。
callable:
  name: child_self_anchor
  params: {}
  returns: {next_step: string, done_signal: string}
  side_effect: none
---

# child_redirect_drift_01

派生自：B01_写作业频繁离座 ·「任务切到一眼能看懂的一小步」的儿童端微步骤版。

面向儿童 · 走神时自我拉回（微步骤 + 完成信号）。
