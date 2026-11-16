---
id: fes_parent_low_pressure_01
type: procedural
audience: parent
scenario: task_initiation
exec_target: 启动
evidence_level: C
contraindication_flag: safe
last_reviewed: 2026-11-13
source_id: family_emotion_support
source_version: "0.10.0"
template_ref: PT_INITIATION_01
proposal_ref: PROP-0003
when:
  task_phase: [启动]
  attention_state: [on-task]
  ownership: [child-leading]
exit_when:
  attention_state: [on-task]
  consecutive_successes: ">=1"
inject_text: |
  今晚只留一个任务，标准是「他看一眼愿意开始、一个晚上能收尾」。做法：①从整页里挑一道他做过、有把握的同类题，只这一道；②把题目里要填的空圈出来，其余部分盖住；③做完这一道就停，当场说「好了，今天到这儿」。不追加第二道，不说明天要补回来。留一个第二天再说的小记号：在本子角上写「明天再看一眼这题」，今晚不展开。可以说的是：「就这一道，做完我们收工。」不要说的是：「趁状态好再多做两道」「今天必须补完」。任务压得比他预期的小，他才肯起步；起步成功一次，这个支架就撤掉。
callable:
  name: fes_low_pressure_task
  params: {unit_size: "enum(single_item, single_step)"}
  returns: {script: string, avoid: string}
  side_effect: none
---

# fes_parent_low_pressure_01

派生自：`family_emotion_support` B 版 0.10.0「输出格式 / Output Format」第五项逐字原文「- 低压力任务」；配套「推荐工作流」逐字「最后只给一个小到能完成的学习动作。」与「把任务控制在一个晚上能完成的范围内，并留下第二天复盘点。」

面向家长 · 程序性（skill spec）：**阶段三首批派生暂停点产物**。

- 动作粒度判定：`task_level`（任务量级设计，未涉及家长/儿童角色切换）；走 `TT_LOW_PRESSURE`（`PROP-0003`，D 类 fast 通道），不硬塞进既有三个 `TT_*`。
- 转换结果：最小可完成单元（一道有把握的同类题）→ 做完即当晚收尾 → 固定位置留次日复盘点、今晚不展开。不保留固定时长、不预判情绪、不追加第二道、不写成撤除条件。
- 撤除：`EX_FULL_ONESHOT`（一次性动作类，成功一次即撤）。
- 模板：`PT_INITIATION_01` 严格套用（字段集与取值完全一致），零偏离；`proposal_ref` 按模板扩展提案流程 §五 双向留痕。
