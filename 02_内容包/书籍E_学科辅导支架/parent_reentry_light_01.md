---
id: parent_reentry_light_01
type: procedural
audience: parent
scenario: attention_drift
exec_target: 抑制控制
evidence_level: B
contraindication_flag: safe
last_reviewed: 2026-11-13
source_id: project_original
source_version: "2026-11"
template_ref: PT_DRIFT_01
deviation:
  kind: value_adjusted
  reason: "字段 attention_state 取值超出模板（{'attention_state': ['drift']} → {'attention_state': ['re-entry']}）"
when:
  task_phase: [执行]
  attention_state: [re-entry]
  ownership: [child-leading, parent-hinting]
exit_when:
  attention_state: [on-task, re-entry]
  consecutive_successes: ">=2"
inject_text: |
  孩子刚把注意力拉回来，这一步先别补讲，也别追加新指令。只给一个完成信号就好：「这一句你看完了，接着往下就行。」他停住时先等三秒，不重复题目，也不把刚才的走神翻出来说。可以说的是：「你接着做，我在这儿。」不要说的是：「你看，认真点不就会了吗」「刚才又走神了吧」。等他连着做完两步，就把话收住，让他自己往下走——刚回到任务的这几分钟，少一句提醒比多一句更稳。
callable:
  name: reentry_light_scaffold
  scaffold_level: light
  params: {}
  returns: {script: string, avoid: string}
  side_effect: none
---

# parent_reentry_light_01

派生自：B01_写作业频繁离座 ·「指令一次一条 / 不要重复题目」；B09_给ADHD孩子布置作业 ·「拆到一眼能看懂的一小步 / 保留做完了的体验」。

面向家长 · **降级支架**（`scaffold_level=light`）：`re-entry` 中间态只给完成信号，不补讲、不追加新指令；连续成功两次后按 `exit_when` 撤除。

设计约束：触发与撤除条件**只在本条目 `when` / `exit_when` 中维护**，`router.py` 不另写任何状态判断，只对产物字段做通用透传（同源契约）。
