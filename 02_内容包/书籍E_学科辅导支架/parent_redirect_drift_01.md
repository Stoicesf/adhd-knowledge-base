---
id: parent_redirect_drift_01
type: procedural
audience: parent
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
  consecutive_failures: ">=2"
  ownership: [child-leading, parent-hinting]
exit_when:
  attention_state: [on-task]
  consecutive_successes: ">=2"
inject_text: |
  孩子走神时，先不要重复题目，也别连着甩出三条指令。可以指着当前这一步说：「你现在只需要看这一句话，找出一个已知数字。」把桌上其他东西收走，桌角放一个看得见的计时器。不要说的是：「你怎么又走神了」「刚才不是讲过了吗」。等他做完这一步、复述一遍，再说下一条。环境改简单，等于替他把抢注意力的待办提前删掉。
callable:
  name: redirect_low_affect
  params: {signal: "enum(drift, fidget, gaze_off)"}
  returns: {script: string, avoid: string}
  side_effect: none
---

# parent_redirect_drift_01

派生自：B01_写作业频繁离座（家庭环境调整的 5 个具体动作）·「指令一次一条 / 计时器可见 / 不要重复题目」

面向家长 · 走神重定向（低情绪）。作为 skill 主产物，inject_text 同时作为可调试文本 fallback。
