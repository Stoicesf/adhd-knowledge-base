---
id: fes_parent_restate_01
type: explanatory
audience: parent
scenario: frustration_escalation
exec_target: 情绪调节
evidence_level: C
contraindication_flag: safe
last_reviewed: 2026-11-13
source_id: family_emotion_support
source_version: "0.10.0"
template_ref: PT_FRUSTRATION_01
when:
  attention_state: [drift, re-entry]
  ownership: [child-leading, parent-hinting]
inject_text: |
  先别急着给办法。把家长刚才说的那句困扰照原样复述一遍：「你是说，今晚数学错题一多，他就趴下不写了，你不知道该不该让他继续，是这样吗？」这一步不是为了安慰，是为了把「任务太难」「能力还没跟上」「情绪已经上来」「两个人说岔了」这四种情况分开。它们长得像，处理方式完全不同：任务问题要拆小，能力问题要降要求，情绪问题要先降温，沟通问题要换说法。若不分辨就直接给学习动作，很容易在孩子已经绷不住的时候继续加题，或在只是没听懂指令时误以为他不配合。复述被家长确认后再往下走，每一步都只对应当晚这一个具体场景。
---

# fes_parent_restate_01

派生自：`family_emotion_support` B 版 0.10.0「推荐工作流 / Recommended Workflow」逐字原文：
「先复述家长的真实困扰，判断这是任务问题、能力问题、情绪问题还是沟通问题。」

面向家长 · 解释性（检索块，无 callable）：承载来源自带的**归因框架**，保留原貌、不压缩成标签、不强行对齐项目靶点。

- 动作粒度判定：`cognitive_action`（一句话一个可执行的认知动作），按动作映射规范 §二 直接落微步骤卡片，无需过 `TT_*`。
- 场景映射：来源「适用场景：亲子沟通 / 最适合的场景：亲子沟通」按本批次口径映射到既有枚举 `frustration_escalation`（情绪受挫/升级），**不新增 scenario**；B 类（新场景类型）判断见 `阶段三_首批派生留痕表.md`，本批次结论为「不提」。
- 模板：三段匹配第一段 scenario 精确命中 `PT_FRUSTRATION_01`（唯一）；排除 `task_phase` 后交叉校验实质交集 `{attention_state, ownership}` 非空。
