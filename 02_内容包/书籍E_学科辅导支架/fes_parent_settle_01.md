---
id: fes_parent_settle_01
type: procedural
audience: parent
scenario: frustration_escalation
exec_target: 情绪调节
evidence_level: C
contraindication_flag: caution
last_reviewed: 2026-11-13
source_id: family_emotion_support
source_version: "0.10.0"
template_ref: PT_FRUSTRATION_01
deviation:
  kind: value_adjusted
  reason: "字段 ownership 取值较模板收窄（[child-leading, parent-hinting] → [parent-hinting]）；consecutive_failures 为模板 params 声明的可调参数填值，不计偏离"
when:
  attention_state: [drift, re-entry]
  ownership: [parent-hinting]
  consecutive_failures: ">=2"
exit_when:
  attention_state: [on-task]
  consecutive_successes: ">=1"
inject_text: |
  今晚先不谈整页作业。①把本子合上，说一句：「先不急，我们把刚才卡住的那题看一眼就好。」②等他呼吸平了，只问一句「这题第一句在说什么」，让他自己说，不替他念。③把第一句里已经给的数圈出来，就算完成一步。这三步是热身，不算正式做题，所以不计时、不追加第二题。可以说的是：「你指一下，哪个数是已经给你的。」不要说的是：「别哭了，这么简单都不会」「快把这一页写完」。等他连着做完这一步、回到题目上，就把话收住，今晚只给这一个动作。区分不出是能力还是情绪时，按情绪先处理，不追问原因。
callable:
  name: fes_settle_then_one_step
  params: {warmup_steps: "enum(3, 2)"}
  returns: {script: string, avoid: string}
  side_effect: none
---

# fes_parent_settle_01

派生自：`family_emotion_support` B 版 0.10.0「推荐工作流 / Recommended Workflow」逐字原文：
「先稳定情绪，再区分能力问题和情绪问题，最后只给一个小到能完成的学习动作。」
以及「给家长可直接说出口的话术，避免命令式和贴标签表达。」

面向家长 · 程序性（skill spec）：把「先…再…最后…」的任务链落成可调度的一次性支架。

- 动作粒度判定：`task_level`（先…再…最后…的任务链，未涉及家长/儿童角色切换），需过 `TT_WARMUP`：「先做简单的热身」→「合上本子 → 读第一句 → 圈出已知量」warm-up 微步骤序列；不保留「稳定情绪」这类不可判定的情绪预判，改为可观察的三步动作。
- 撤除：`EX_FULL_ONESHOT`（一次性动作类：执行一次即完成，成功一次即撤）。
- 模板：scenario 精确命中 `PT_FRUSTRATION_01`；`ownership` 取值收窄已如实登记 `deviation.kind=value_adjusted`（单列，不进主偏离率）；`consecutive_failures` 属模板 `params` 可调参数填值。
