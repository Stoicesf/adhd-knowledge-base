---
id: fes_parent_pause_signal_01
type: explanatory
audience: parent
scenario: frustration_escalation
exec_target: 情绪调节
evidence_level: C
contraindication_flag: caution
last_reviewed: 2026-11-13
source_id: family_emotion_support
source_version: "0.10.0"
template_ref: PT_FRUSTRATION_01
when:
  attention_state: [drift, re-entry]
  ownership: [child-leading, parent-hinting]
  task_phase: [检查]
inject_text: |
  有一类信号出现时，今晚的学习动作要整个停下，而不是换个更小的任务继续：孩子明显崩溃、长时间哭到说不出话、说伤害自己的话，或家长自己已经压不住火。这时该做的只有两件——先把作业合上、离开书桌，再按来源边界去联系有处方权的医生或学校心理老师，把情况按时间顺序说清楚。这些不是「不配合」，是需要专业支持介入的信号；本库和任何 AI 话术都不能替代专业心理咨询、医学诊断或学校正式评估，也不该在孩子明显崩溃时继续加压学习。可以留一句：「今天先不做了，我们一起去问问专业的人。」复盘点等状态回来之后再定，不在当晚追问原因。
---

# fes_parent_pause_signal_01

派生自：`family_emotion_support` B 版 0.10.0「输出格式 / Output Format」逐字原文「- 需要暂停或求助的信号」；「质量检查 / Quality Checks」逐字「涉及明显心理/安全风险时提醒寻求专业帮助」；「不适合 / Not For」逐字「用 AI 替代专业心理支持，或在孩子明显崩溃时继续加压学习」。

面向家长 · 解释性（检索块，无 callable）：承载来源的**安全边界知识**，主产物为检索块，不生成新的调度动作。

- 动作粒度判定：`task_level`（信号识别 → 停 → 转介的动作链），走 `TT_STOP_SIGNAL`：「孩子烦躁就停」→ 把模糊情绪信号固化为「可观察的暂停信号 + 明确转介去向」，不写成不可判定的情绪预判，也不新建 guardrail 规则类别（E 类不在本批次范围）。
- 与项目既有安全底线一致：来源三条红线逐字照抄进接入卡，本条只做解释层转述，不改 `guardrail_rules.yaml`。
- `contraindication_flag: caution`：涉及明显心理/安全风险，触发后应走转介而非继续给学习支架。
- 模板：scenario 精确命中 `PT_FRUSTRATION_01`；`task_phase` 属高噪声字段，按既有口径不记偏离。
