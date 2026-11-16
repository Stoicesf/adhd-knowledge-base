---
id: fes_parent_script_01
type: explanatory
audience: parent
scenario: frustration_escalation
exec_target: 抑制控制
evidence_level: C
contraindication_flag: safe
last_reviewed: 2026-11-13
source_id: family_emotion_support
source_version: "0.10.0"
template_ref: PT_FRUSTRATION_01
when:
  attention_state: [drift, re-entry]
  ownership: [child-leading, parent-hinting]
  task_phase: [执行]
inject_text: |
  同一句提醒，换个说法，孩子接到的信息完全不同。「你怎么又走神了」是给他下一个结论；「这一行我们再看一次」是给他一个能做的动作。命令式和贴标签的话会把今晚的作业变成一场关于「他是什么样的人」的争论，而这类评价他在学校往往已经听了一整天，回家再听一次，起步的成本会更高。可照着说的句式是：先说你看到的具体动作（「笔停在这儿了」），再说一个下一步（「把第一句的关键词指给我」），最后停住，不追加评价和追问。不要说的是「你就是不专心」「你就是不认真」这类定性句。话术只解决当下这一句，不翻旧账、不预测明天。
---

# fes_parent_script_01

派生自：`family_emotion_support` B 版 0.10.0 逐字原文：
「给家长可直接说出口的话术，避免命令式和贴标签表达。」
「语气要支持家长，但不把孩子问题简单归因为懒或不听话」（质量检查 / Quality Checks）。

面向家长 · 解释性（检索块，无 callable）：解释「为什么命令式与贴标签表达会提高启动成本」，为程序性话术动作提供理由层。

- 动作粒度判定：`cognitive_action`，直接落微步骤卡片，无需过 `TT_*`。
- 场景映射：同 `fes_parent_restate_01`，映射到既有枚举 `frustration_escalation`，本批次不提 B 类。
- 模板：scenario 精确命中 `PT_FRUSTRATION_01`；`task_phase` 属高噪声字段（动作映射规范 §六 排除项），按既有 11 条口径不作为偏离登记。
