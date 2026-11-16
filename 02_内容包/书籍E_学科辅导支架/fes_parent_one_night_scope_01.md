---
id: fes_parent_one_night_scope_01
type: procedural
audience: parent
scenario: frustration_escalation
exec_target: 时间感知
evidence_level: C
contraindication_flag: safe
last_reviewed: 2026-11-13
source_id: family_emotion_support
source_version: "0.10.0"
template_ref: PT_FRUSTRATION_01
deviation:
  kind: value_adjusted
  reason: "字段 ownership 取值较模板收窄（[child-leading, parent-hinting] → [child-leading]）；consecutive_failures 为模板 params 声明的可调参数填值，不计偏离"
when:
  attention_state: [drift, re-entry]
  ownership: [child-leading]
  consecutive_failures: ">=1"
exit_when:
  attention_state: [on-task]
  consecutive_successes: ">=2"
inject_text: |
  别用「再写二十分钟」来划今晚的边界，钟点对坐不住的孩子是额外压力。改用「做完这几步就收」：①把今晚要做的写成本子上的三行短句，一行一个动作；②每做完一行，让他自己划掉；③三行划完就是今晚的终点，不再追加。第二天复盘点也写在同一个位置：「明晚先看第一行」，今晚只留这一句，不预告任务量。可以说的是：「划完这三行，今天就结束了。」不要说的是：「时间还早，再做一会儿」「写不完不许睡」。边界由「做完」而不是「到点」决定，孩子能看见终点在哪；连着两晚都能按这个收尾，就把它交还给他自己安排。
callable:
  name: fes_one_night_scope
  params: {step_lines: "enum(3, 2)"}
  returns: {script: string, avoid: string}
  side_effect: none
---

# fes_parent_one_night_scope_01

派生自：`family_emotion_support` B 版 0.10.0「推荐工作流 / Recommended Workflow」逐字原文：
「把任务控制在一个晚上能完成的范围内，并留下第二天复盘点。」

面向家长 · 程序性（skill spec）：把「一个晚上」这个时间边界结构化。

- 动作粒度判定：`task_level`（含多个步骤的任务链，未涉及角色切换）；走 `TT_TIMEBOX`：「N 分钟/N 道题就停」→「完成 M 个微步骤后收尾；不保留固定时长」。来源的「一个晚上」属固定时长信号，直接写进微步骤会变成额外压力，故转成「三行短句、划完即终点」。
- 「第二天复盘点」落成同一位置的次日短句，今晚不展开，避免把一个收尾动作扩成第二个任务。
- 撤除：`EX_FULL_SUSTAINED`（持续稳定类：连续两晚按此收尾、确认状态稳定后才撤）。
- 模板：scenario 精确命中 `PT_FRUSTRATION_01`；`ownership` 收窄已登记 `value_adjusted`（单列，不进主偏离率）。与 `fes_parent_settle_01` 同场景，靠 `ownership` 取值互斥，互不抢命中。
