---
id: fes_parent_single_scene_01
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
deviation:
  kind: value_adjusted
  reason: "字段 ownership 取值较模板调整（[child-leading] → [parent-hinting]）：来源适用角色为家长，无家庭数据时由家长提示式描述场景，故按角色显式填值"
when:
  task_phase: [启动]
  attention_state: [on-task]
  ownership: [parent-hinting]
exit_when:
  attention_state: [on-task]
  consecutive_successes: ">=1"
inject_text: |
  手上没有记录、也不清楚今晚发生了什么时，别先给通用建议。①请家长只讲最近一次的具体场景：哪天的哪一科、孩子当时说了什么、你回了哪一句。②把这三样复述确认一遍——今天的任务、孩子的反应、你希望改善的一个点；不确认就不往下给建议。③只针对这一个场景给一个能在家里执行的动作，比如「把那道题的第一句再读一遍」。今晚不铺开到作业习惯、屏幕时间或家校沟通。可以说的是：「就说昨天那一次，其他的我们改天再看。」不要说的是：「你先把他整体情况讲一遍」「顺便把作息也调一调」。场景收得越窄，给的动作越能当场用上。
callable:
  name: fes_single_scene_scope
  params: {scene_fields: "enum(task, reaction, parent_goal)"}
  returns: {script: string, avoid: string}
  side_effect: none
---

# fes_parent_single_scene_01

派生自：`family_emotion_support` B 版 0.10.0「没有平台工具时 / Standalone Fallback」逐字原文
「没有家庭数据时，让家长描述一个最近发生的具体场景。」
「没有学习记录时，用"今天任务、孩子反应、家长目标"生成陪伴脚本。」
以及「质量检查 / Quality Checks」逐字「每次只解决一个家庭场景」「建议必须能在家里执行」。

面向家长 · 程序性（skill spec）：无家庭数据时的起步支架。

- 动作粒度判定：`task_level`（先描述场景 → 再确认三要素 → 最后只给一个动作），走 `TT_WARMUP` 同源思路：把「先讲一个具体场景」转成 warm-up 式的已知量确认序列（今天任务 / 孩子反应 / 家长目标），确认后才给动作；不预判情绪、不保留固定时长。
- 与 `fes_parent_low_pressure_01` 同场景，靠 `ownership` 取值互斥（child-leading ↔ parent-hinting），互不抢命中。
- 撤除：`EX_FULL_ONESHOT`（一次性，确认成功一次即撤）。
- 模板：scenario 精确命中 `PT_INITIATION_01`；`ownership` 取值调整已登记 `value_adjusted`（单列，不进主偏离率）。
