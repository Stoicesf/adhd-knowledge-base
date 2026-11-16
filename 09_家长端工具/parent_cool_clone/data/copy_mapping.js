window.__PC_COPY__ = {
  "meta": {
    "batch": 8,
    "generated_by": "09_家长端工具/parent_cool_clone/build_copy_mapping.py",
    "source_artifact": "03_agent编译/output/chunks.jsonl",
    "source_entry_count": 30,
    "stock_entry_count": 18,
    "fes_parent_entry_count": 7,
    "no_original_text": true,
    "action_granularity": "task_level",
    "action_granularity_basis": "7/7 条 fes_* parent 话术的 inject_text 均含多步动作序列（①②③ / 先…再…最后…）与撤除条件（做完就收 / 连着两晚就撤），属任务级；没有一条是纯单句认知动作卡。该判定描述的是现有可复用文案的粒度，不是 parent-cool 原文粒度（原文不在手）；批次 3 建 parent_cool 接入卡时直接引用此值。",
    "cognitive_action_level_found": false,
    "slot_total": 22,
    "mapped_count": 21,
    "pending_batch3_count": 0,
    "filled_constant_count": 1,
    "batch3": {
      "derived_entries": 6,
      "backfilled_slots": [
        "script_card_08",
        "script_card_09",
        "script_card_10",
        "script_card_11",
        "script_card_12"
      ],
      "runtime_only_entry": "pc_escalation_no_label_01",
      "remaining_pending": 0,
      "pending_not_cleared_reason": "批次 3 时三档撤退 / 修复卡 / 五类身体预警 / 免责声明原文在现有 18 条与 6 条派生条目中均无对应文案，如实保留占位；批次 5 已将三档撤退（条目分档回填）与免责（常量填充）关闭，剩余 pending 见下。",
      "no_fabrication_check": "6 条派生 inject_text 的每句均为存量 inject_text 的逐字子串，由 derive_batch3_entries.py 与 parent_escalation_tests.py 双向校验。"
    },
    "batch5": {
      "goal": "条目级分档关闭 D-06 + pending 10 → 6",
      "tier_entries": {
        "low": [
          "pc_escalation_no_label_01"
        ],
        "mid": [
          "pc_escalation_one_step_01"
        ],
        "high": [
          "pc_escalation_refer_01"
        ]
      },
      "retreat_backfill": [
        "retreat_low",
        "retreat_mid",
        "retreat_high"
      ],
      "disclaimer": "filled_constant（ast 从 server.py 提取 DISCLAIMER）",
      "d06_evidence": "test_server.py test_10 + parent_escalation_tests ②'：三档 line 两两不同"
    },
    "batch8": {
      "goal": "pending 6 → 0：修复卡 + 五类预警授权抓取来源接入",
      "backfilled_slots": [
        "repair_card_01",
        "warning_signs_呼吸",
        "warning_signs_肌肉",
        "warning_signs_声音",
        "warning_signs_胸口",
        "warning_signs_念头"
      ],
      "sources": "fhs_hk_anger_management / aiadhd_yell_repair（中文派生）；nhs_inform / pkjcoaching / calmhome 仅 _staging 留痕参照",
      "no_fabrication_check": "6 条 inject_text 每句均为 staging 原文逐字子串，由 derive_batch8_entries.py 与 parent_escalation_tests ⑥' 双向校验。",
      "language_rule": "中文派生 + 英文留痕（用户批次 8 拍板）"
    },
    "record_contract": {
      "slot": "str",
      "source_entry_id": "str|null",
      "status": "mapped|pending_batch3|filled_constant",
      "note": "str",
      "text": "str|null — mapped/filled_constant 时逐字取自 inject_text / server.DISCLAIMER；pending 时为 null"
    },
    "notes": [
      "ai_line.output（line + steps[3]）是运行时由 retrieve + assemble 生成的动态输出，不是静态文案槽位，不进本盘点表；见批次 2 server.py。",
      "script_cards 的 text 是整段 inject_text（含步骤与可说/不可说句），未截断未改写；前端按卡片展示全文。",
      "mapped 槽位的 source_entry_id 全部经 chunks.jsonl 存在性校验；text 由脚本直取，不经人工转录，可复跑比对。"
    ]
  },
  "records": [
    {
      "slot": "script_card_01",
      "source_entry_id": "fes_parent_restate_01",
      "status": "mapped",
      "note": "逐字取自 fes_parent_restate_01.inject_text 全文（含步骤序列与可说/不可说句）；复述家长的困扰，先不给办法。 text 未截断、未改写。scenario=frustration_escalation、type=explanatory、contraindication_flag=safe。",
      "text": "先别急着给办法。把家长刚才说的那句困扰照原样复述一遍：「你是说，今晚数学错题一多，他就趴下不写了，你不知道该不该让他继续，是这样吗？」这一步不是为了安慰，是为了把「任务太难」「能力还没跟上」「情绪已经上来」「两个人说岔了」这四种情况分开。它们长得像，处理方式完全不同：任务问题要拆小，能力问题要降要求，情绪问题要先降温，沟通问题要换说法。若不分辨就直接给学习动作，很容易在孩子已经绷不住的时候继续加题，或在只是没听懂指令时误以为他不配合。复述被家长确认后再往下走，每一步都只对应当晚这一个具体场景。",
      "group": "script_cards"
    },
    {
      "slot": "script_card_02",
      "source_entry_id": "fes_parent_script_01",
      "status": "mapped",
      "note": "逐字取自 fes_parent_script_01.inject_text 全文（含步骤序列与可说/不可说句）；同一句提醒换个说法；含「不翻旧账」边界。 text 未截断、未改写。scenario=frustration_escalation、type=explanatory、contraindication_flag=safe。",
      "text": "同一句提醒，换个说法，孩子接到的信息完全不同。「你怎么又走神了」是给他下一个结论；「这一行我们再看一次」是给他一个能做的动作。命令式和贴标签的话会把今晚的作业变成一场关于「他是什么样的人」的争论，而这类评价他在学校往往已经听了一整天，回家再听一次，起步的成本会更高。可照着说的句式是：先说你看到的具体动作（「笔停在这儿了」），再说一个下一步（「把第一句的关键词指给我」），最后停住，不追加评价和追问。不要说的是「你就是不专心」「你就是不认真」这类定性句。话术只解决当下这一句，不翻旧账、不预测明天。",
      "group": "script_cards"
    },
    {
      "slot": "script_card_03",
      "source_entry_id": "fes_parent_settle_01",
      "status": "mapped",
      "note": "逐字取自 fes_parent_settle_01.inject_text 全文（含步骤序列与可说/不可说句）；先降温的三步热身；contraindication_flag=caution。 text 未截断、未改写。scenario=frustration_escalation、type=procedural、contraindication_flag=caution。",
      "text": "今晚先不谈整页作业。①把本子合上，说一句：「先不急，我们把刚才卡住的那题看一眼就好。」②等他呼吸平了，只问一句「这题第一句在说什么」，让他自己说，不替他念。③把第一句里已经给的数圈出来，就算完成一步。这三步是热身，不算正式做题，所以不计时、不追加第二题。可以说的是：「你指一下，哪个数是已经给你的。」不要说的是：「别哭了，这么简单都不会」「快把这一页写完」。等他连着做完这一步、回到题目上，就把话收住，今晚只给这一个动作。区分不出是能力还是情绪时，按情绪先处理，不追问原因。\n",
      "group": "script_cards"
    },
    {
      "slot": "script_card_04",
      "source_entry_id": "fes_parent_pause_signal_01",
      "status": "mapped",
      "note": "逐字取自 fes_parent_pause_signal_01.inject_text 全文（含步骤序列与可说/不可说句）；整晚停下的信号与专业转介；contraindication_flag=caution。 text 未截断、未改写。scenario=frustration_escalation、type=explanatory、contraindication_flag=caution。",
      "text": "有一类信号出现时，今晚的学习动作要整个停下，而不是换个更小的任务继续：孩子明显崩溃、长时间哭到说不出话、说伤害自己的话，或家长自己已经压不住火。这时该做的只有两件——先把作业合上、离开书桌，再按来源边界去联系有处方权的医生或学校心理老师，把情况按时间顺序说清楚。这些不是「不配合」，是需要专业支持介入的信号；本库和任何 AI 话术都不能替代专业心理咨询、医学诊断或学校正式评估，也不该在孩子明显崩溃时继续加压学习。可以留一句：「今天先不做了，我们一起去问问专业的人。」复盘点等状态回来之后再定，不在当晚追问原因。",
      "group": "script_cards"
    },
    {
      "slot": "script_card_05",
      "source_entry_id": "fes_parent_one_night_scope_01",
      "status": "mapped",
      "note": "逐字取自 fes_parent_one_night_scope_01.inject_text 全文（含步骤序列与可说/不可说句）；用「做完这几步就收」划今晚边界。 text 未截断、未改写。scenario=frustration_escalation、type=procedural、contraindication_flag=safe。",
      "text": "别用「再写二十分钟」来划今晚的边界，钟点对坐不住的孩子是额外压力。改用「做完这几步就收」：①把今晚要做的写成本子上的三行短句，一行一个动作；②每做完一行，让他自己划掉；③三行划完就是今晚的终点，不再追加。第二天复盘点也写在同一个位置：「明晚先看第一行」，今晚只留这一句，不预告任务量。可以说的是：「划完这三行，今天就结束了。」不要说的是：「时间还早，再做一会儿」「写不完不许睡」。边界由「做完」而不是「到点」决定，孩子能看见终点在哪；连着两晚都能按这个收尾，就把它交还给他自己安排。\n",
      "group": "script_cards"
    },
    {
      "slot": "script_card_06",
      "source_entry_id": "fes_parent_low_pressure_01",
      "status": "mapped",
      "note": "逐字取自 fes_parent_low_pressure_01.inject_text 全文（含步骤序列与可说/不可说句）；只留一个小到能完成的任务。 text 未截断、未改写。scenario=task_initiation、type=procedural、contraindication_flag=safe。",
      "text": "今晚只留一个任务，标准是「他看一眼愿意开始、一个晚上能收尾」。做法：①从整页里挑一道他做过、有把握的同类题，只这一道；②把题目里要填的空圈出来，其余部分盖住；③做完这一道就停，当场说「好了，今天到这儿」。不追加第二道，不说明天要补回来。留一个第二天再说的小记号：在本子角上写「明天再看一眼这题」，今晚不展开。可以说的是：「就这一道，做完我们收工。」不要说的是：「趁状态好再多做两道」「今天必须补完」。任务压得比他预期的小，他才肯起步；起步成功一次，这个支架就撤掉。\n",
      "group": "script_cards"
    },
    {
      "slot": "script_card_07",
      "source_entry_id": "fes_parent_single_scene_01",
      "status": "mapped",
      "note": "逐字取自 fes_parent_single_scene_01.inject_text 全文（含步骤序列与可说/不可说句）；只讲最近一次具体场景，不给通用建议。 text 未截断、未改写。scenario=task_initiation、type=procedural、contraindication_flag=safe。",
      "text": "手上没有记录、也不清楚今晚发生了什么时，别先给通用建议。①请家长只讲最近一次的具体场景：哪天的哪一科、孩子当时说了什么、你回了哪一句。②把这三样复述确认一遍——今天的任务、孩子的反应、你希望改善的一个点；不确认就不往下给建议。③只针对这一个场景给一个能在家里执行的动作，比如「把那道题的第一句再读一遍」。今晚不铺开到作业习惯、屏幕时间或家校沟通。可以说的是：「就说昨天那一次，其他的我们改天再看。」不要说的是：「你先把他整体情况讲一遍」「顺便把作息也调一调」。场景收得越窄，给的动作越能当场用上。\n",
      "group": "script_cards"
    },
    {
      "slot": "script_card_08",
      "source_entry_id": "pc_escalation_restate_01",
      "status": "mapped",
      "note": "【批次 3 回填】逐字取自 pc_escalation_restate_01.inject_text 全文；该条目由 03_agent编译/derive_batch3_entries.py 从现有 18 条逐句摘取重组，每句均为存量 inject_text 的逐字子串（parent_escalation_tests 独立复验）。scenario=parent_escalation、type=explanatory、when 三档全命中、条目级不做内容分档；语义边界见条目正文。",
      "text": "先别急着给办法。把家长刚才说的那句困扰照原样复述一遍：「你是说，今晚数学错题一多，他就趴下不写了，你不知道该不该让他继续，是这样吗？」这一步不是为了安慰，是为了把「任务太难」「能力还没跟上」「情绪已经上来」「两个人说岔了」这四种情况分开。它们长得像，处理方式完全不同：任务问题要拆小，能力问题要降要求，情绪问题要先降温，沟通问题要换说法。复述被家长确认后再往下走，每一步都只对应当晚这一个具体场景。话术只解决当下这一句，不翻旧账、不预测明天。",
      "group": "script_cards"
    },
    {
      "slot": "script_card_09",
      "source_entry_id": "pc_escalation_stop_01",
      "status": "mapped",
      "note": "【批次 3 回填】逐字取自 pc_escalation_stop_01.inject_text 全文；该条目由 03_agent编译/derive_batch3_entries.py 从现有 18 条逐句摘取重组，每句均为存量 inject_text 的逐字子串（parent_escalation_tests 独立复验）。scenario=parent_escalation、type=explanatory、when 三档全命中、条目级不做内容分档；语义边界见条目正文。",
      "text": "有一类信号出现时，今晚的学习动作要整个停下，而不是换个更小的任务继续：孩子明显崩溃、长时间哭到说不出话、说伤害自己的话，或家长自己已经压不住火。今晚先不谈整页作业。这时该做的只有两件——先把作业合上、离开书桌，再按来源边界去联系有处方权的医生或学校心理老师，把情况按时间顺序说清楚。可以留一句：「今天先不做了，我们一起去问问专业的人。」复盘点等状态回来之后再定，不在当晚追问原因。",
      "group": "script_cards"
    },
    {
      "slot": "script_card_10",
      "source_entry_id": "pc_escalation_scope_01",
      "status": "mapped",
      "note": "【批次 3 回填】逐字取自 pc_escalation_scope_01.inject_text 全文；该条目由 03_agent编译/derive_batch3_entries.py 从现有 18 条逐句摘取重组，每句均为存量 inject_text 的逐字子串（parent_escalation_tests 独立复验）。scenario=parent_escalation、type=explanatory、when 三档全命中、条目级不做内容分档；语义边界见条目正文。",
      "text": "手上没有记录、也不清楚今晚发生了什么时，别先给通用建议。①请家长只讲最近一次的具体场景：哪天的哪一科、孩子当时说了什么、你回了哪一句。今晚不铺开到作业习惯、屏幕时间或家校沟通。场景收得越窄，给的动作越能当场用上。区分不出是能力还是情绪时，按情绪先处理，不追问原因。",
      "group": "script_cards"
    },
    {
      "slot": "script_card_11",
      "source_entry_id": "pc_escalation_one_step_01",
      "status": "mapped",
      "note": "【批次 3 回填】逐字取自 pc_escalation_one_step_01.inject_text 全文；该条目由 03_agent编译/derive_batch3_entries.py 从现有 18 条逐句摘取重组，每句均为存量 inject_text 的逐字子串（parent_escalation_tests 独立复验）。scenario=parent_escalation、type=explanatory、when 三档全命中、条目级不做内容分档；语义边界见条目正文。",
      "text": "今晚只留一个任务，标准是「他看一眼愿意开始、一个晚上能收尾」。改用「做完这几步就收」：①把今晚要做的写成本子上的三行短句，一行一个动作；②每做完一行，让他自己划掉；③三行划完就是今晚的终点，不再追加。不追加第二道，不说明天要补回来。等他连着做完这一步、回到题目上，就把话收住，今晚只给这一个动作。边界由「做完」而不是「到点」决定，孩子能看见终点在哪；连着两晚都能按这个收尾，就把它交还给他自己安排。",
      "group": "script_cards"
    },
    {
      "slot": "script_card_12",
      "source_entry_id": "pc_escalation_refer_01",
      "status": "mapped",
      "note": "【批次 3 回填】逐字取自 pc_escalation_refer_01.inject_text 全文；该条目由 03_agent编译/derive_batch3_entries.py 从现有 18 条逐句摘取重组，每句均为存量 inject_text 的逐字子串（parent_escalation_tests 独立复验）。scenario=parent_escalation、type=explanatory、when 三档全命中、条目级不做内容分档；语义边界见条目正文。",
      "text": "这些不是「不配合」，是需要专业支持介入的信号；本库和任何 AI 话术都不能替代专业心理咨询、医学诊断或学校正式评估，也不该在孩子明显崩溃时继续加压学习。可照着说的句式是：先说你看到的具体动作（「笔停在这儿了」），再说一个下一步（「把第一句的关键词指给我」），最后停住，不追加评价和追问。不要说的是「你就是不专心」「你就是不认真」这类定性句。话术只解决当下这一句，不翻旧账、不预测明天。」复盘点等状态回来之后再定，不在当晚追问原因。",
      "group": "script_cards"
    },
    {
      "slot": "retreat_low",
      "source_entry_id": "pc_escalation_no_label_01",
      "status": "mapped",
      "note": "【批次 5 分档回填】取自 low 档条目 pc_escalation_no_label_01 的 inject_text 全文（逐字）；同档另有 pc_escalation_restate_01，按 id 字母序取第一条（可复现）。分档依据见条目 front matter 的 deviation.reason（when 由 [low, mid, high] 收窄为单档，批次 5 关闭 D-06）。",
      "text": "同一句提醒，换个说法，孩子接到的信息完全不同。「你怎么又走神了」是给他下一个结论；「这一行我们再看一次」是给他一个能做的动作。命令式和贴标签的话会把今晚的作业变成一场关于「他是什么样的人」的争论，而这类评价他在学校往往已经听了一整天，回家再听一次，起步的成本会更高。可照着说的句式是：先说你看到的具体动作（「笔停在这儿了」），再说一个下一步（「把第一句的关键词指给我」），最后停住，不追加评价和追问。话术只解决当下这一句，不翻旧账、不预测明天。",
      "group": "retreat_tiers"
    },
    {
      "slot": "retreat_mid",
      "source_entry_id": "pc_escalation_one_step_01",
      "status": "mapped",
      "note": "【批次 5 分档回填】取自 mid 档条目 pc_escalation_one_step_01 的 inject_text 全文（逐字）；同档另有 pc_escalation_scope_01，按 id 字母序取第一条（可复现）。分档依据见条目 front matter 的 deviation.reason（when 由 [low, mid, high] 收窄为单档，批次 5 关闭 D-06）。",
      "text": "今晚只留一个任务，标准是「他看一眼愿意开始、一个晚上能收尾」。改用「做完这几步就收」：①把今晚要做的写成本子上的三行短句，一行一个动作；②每做完一行，让他自己划掉；③三行划完就是今晚的终点，不再追加。不追加第二道，不说明天要补回来。等他连着做完这一步、回到题目上，就把话收住，今晚只给这一个动作。边界由「做完」而不是「到点」决定，孩子能看见终点在哪；连着两晚都能按这个收尾，就把它交还给他自己安排。",
      "group": "retreat_tiers"
    },
    {
      "slot": "retreat_high",
      "source_entry_id": "pc_escalation_refer_01",
      "status": "mapped",
      "note": "【批次 5 分档回填】取自 high 档条目 pc_escalation_refer_01 的 inject_text 全文（逐字）；同档另有 pc_escalation_stop_01，按 id 字母序取第一条（可复现）。分档依据见条目 front matter 的 deviation.reason（when 由 [low, mid, high] 收窄为单档，批次 5 关闭 D-06）。",
      "text": "这些不是「不配合」，是需要专业支持介入的信号；本库和任何 AI 话术都不能替代专业心理咨询、医学诊断或学校正式评估，也不该在孩子明显崩溃时继续加压学习。可照着说的句式是：先说你看到的具体动作（「笔停在这儿了」），再说一个下一步（「把第一句的关键词指给我」），最后停住，不追加评价和追问。不要说的是「你就是不专心」「你就是不认真」这类定性句。话术只解决当下这一句，不翻旧账、不预测明天。」复盘点等状态回来之后再定，不在当晚追问原因。",
      "group": "retreat_tiers"
    },
    {
      "slot": "repair_card_01",
      "source_entry_id": "pc_repair_card_01",
      "status": "mapped",
      "note": "【批次 8 回填】逐字取自 pc_repair_card_01.inject_text 全文；该条目由 03_agent编译/derive_batch8_entries.py 从授权抓取的 staging 原文逐句摘取（source_id 见条目 front matter），parent_escalation_tests ⑥' 独立复验逐字可溯。scenario=parent_escalation、type=explanatory、when 三档全命中；语义边界见条目正文。",
      "text": "对不起，刚才妈妈/爸爸没有控制好自己的脾气，对你大吼大叫了。我感到很生气，但这不能成为我伤害你的理由。我爱你。對不起，即使我很生氣，我也不應該大聲罵你的。为您的\"行为\"而非您的\"情绪\"道歉。待雙方冷靜過後，向彼此說出自己的感受和想法。爱，并非意味着永不犯错，而是在风暴过后，永远有勇气回来，重新拥抱。",
      "group": "repair_card"
    },
    {
      "slot": "warning_signs_呼吸",
      "source_entry_id": "pc_warning_breath_01",
      "status": "mapped",
      "note": "【批次 8 回填】逐字取自 pc_warning_breath_01.inject_text 全文；该条目由 03_agent编译/derive_batch8_entries.py 从授权抓取的 staging 原文（fhs_hk_anger_management）逐句摘取，parent_escalation_tests ⑥' 独立复验逐字可溯。信号与动作分列，动作列逐字取自中文来源，不逐类编造。scenario=parent_escalation、when 三档全命中。",
      "text": "呼吸短而淺。心跳加速。慢慢地呼吸。平復心跳及呼吸的頻率，幫助放鬆。将手放在心脏的位置，做三次缓慢、深长的腹式呼吸。",
      "group": "warning_signs",
      "category": "呼吸",
      "columns": [
        "常见信号",
        "当场动作"
      ]
    },
    {
      "slot": "warning_signs_肌肉",
      "source_entry_id": "pc_warning_muscle_01",
      "status": "mapped",
      "note": "【批次 8 回填】逐字取自 pc_warning_muscle_01.inject_text 全文；该条目由 03_agent编译/derive_batch8_entries.py 从授权抓取的 staging 原文（fhs_hk_anger_management）逐句摘取，parent_escalation_tests ⑥' 独立复验逐字可溯。信号与动作分列，动作列逐字取自中文来源，不逐类编造。scenario=parent_escalation、when 三档全命中。",
      "text": "肌肉繃緊。手心出汗。慢慢地呼吸。在吸氣時心裡默念 1，呼氣時放鬆身體。分散注意力。",
      "group": "warning_signs",
      "category": "肌肉",
      "columns": [
        "常见信号",
        "当场动作"
      ]
    },
    {
      "slot": "warning_signs_声音",
      "source_entry_id": "pc_warning_voice_01",
      "status": "mapped",
      "note": "【批次 8 回填】逐字取自 pc_warning_voice_01.inject_text 全文；该条目由 03_agent编译/derive_batch8_entries.py 从授权抓取的 staging 原文（fhs_hk_anger_management）逐句摘取，parent_escalation_tests ⑥' 独立复验逐字可溯。信号与动作分列，动作列逐字取自中文来源，不逐类编造。scenario=parent_escalation、when 三档全命中。",
      "text": "聲線提高。面紅耳熱。離開現場，減少環境帶來的情緒刺激。分散注意力。我现在感觉非常生气，我需要去另一个房间冷静两分钟，我们稍后再谈。",
      "group": "warning_signs",
      "category": "声音",
      "columns": [
        "常见信号",
        "当场动作"
      ]
    },
    {
      "slot": "warning_signs_胸口",
      "source_entry_id": "pc_warning_chest_01",
      "status": "mapped",
      "note": "【批次 8 回填】逐字取自 pc_warning_chest_01.inject_text 全文；该条目由 03_agent编译/derive_batch8_entries.py 从授权抓取的 staging 原文（fhs_hk_anger_management）逐句摘取，parent_escalation_tests ⑥' 独立复验逐字可溯。信号与动作分列，动作列逐字取自中文来源，不逐类编造。scenario=parent_escalation、when 三档全命中。",
      "text": "胸悶。手心出汗。慢慢地呼吸。平復心跳及呼吸的頻率，幫助放鬆。用冷水冲洗一下手腕和脸部。",
      "group": "warning_signs",
      "category": "胸口",
      "columns": [
        "常见信号",
        "当场动作"
      ]
    },
    {
      "slot": "warning_signs_念头",
      "source_entry_id": "pc_warning_thought_01",
      "status": "mapped",
      "note": "【批次 8 回填】逐字取自 pc_warning_thought_01.inject_text 全文；该条目由 03_agent编译/derive_batch8_entries.py 从授权抓取的 staging 原文（fhs_hk_anger_management）逐句摘取，parent_escalation_tests ⑥' 独立复验逐字可溯。信号与动作分列，动作列逐字取自中文来源，不逐类编造。scenario=parent_escalation、when 三档全命中。",
      "text": "災難化。天啊！我永遠都教不好孩子！。仔細想一想情緒出現的原因。嘗試提出合理的證據來加以證實自己的一些不合理的想法。在我爆发的前一秒，我脑子里闪过的那个'热念头'是什么。",
      "group": "warning_signs",
      "category": "念头",
      "columns": [
        "常见信号",
        "当场动作"
      ]
    },
    {
      "slot": "disclaimer",
      "source_entry_id": null,
      "status": "filled_constant",
      "group": "ui",
      "note": "【批次 5 免责收口】复用 server.py 的 DISCLAIMER 中性文本（批次 4.5b 定稿，去批次号 D-07）。本脚本用 ast 从 server.py 机械提取，不手抄；它不是知识库条目，故标 filled_constant 而非 mapped，避免混淆「知识库来源」与「常量填充」两种口径。parent-cool 原文到位后，与本常量及前端展示一并联动替换。",
      "text": "本工具为家长情绪自助参考，不替代专业心理咨询、医学诊断或学校正式评估。\n如孩子出现持续情绪困扰或家庭冲突升级，请寻求专业帮助。"
    }
  ]
};
