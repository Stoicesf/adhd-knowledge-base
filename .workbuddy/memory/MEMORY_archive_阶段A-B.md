# MEMORY.md 归档（阶段 A → 阶段 B 批次 6-A 的历史快照）

> **本文件为历史记录，append-only，不回写。当前活状态见 `MEMORY.md`。**
> 精简执行：批次 7（2026-11-14）。段落归属审计见 `05_审核与运营/regression/MEMORY_审计.md`。
>
> **范围如实说明**：本文件是精简前 `.workbuddy/memory/MEMORY.md` 的**全文逐字快照**
> （87 行 / 22380 B，字节级复制，未压缩、未改写、未优化措辞）。其实际内容覆盖
> 阶段三～阶段六、阶段 A、阶段 B 批次 0～**6-A**；**批次 6-C / 6-D / 6-E 从未写入过
> MEMORY.md**，它们的完整历史在每日日志 `2026-11-14.md` §十 / §十一 / §十二（append-only，
> 本归档不搬运，避免制造两份历史）。文件名沿用批次 7 方案，不代表覆盖到 6E。
>
> **为什么是全文而非只搬历史段**：只搬「历史/过期」段会让活状态段的原始措辞永久丢失，
> 且切分搬运本身有改动字符的风险。全文快照保证历史、过期、活状态原文一行不漏。
> 分隔符以下的部分与精简前 MEMORY.md **逐字节一致**，可用 sha256 复核：
> `c5329964e4cf99696f1a1d2313b79e19bffe5601fe417d47dae4c984cc407be3`
>
> **段落归属索引**（行号指本文件分隔符以下的原始行号；判定标准=「下次会话不知道
> 这条会不会做出错误决策」；详细理由见 MEMORY_审计.md §二）：
> - 活状态（16 单元，精简后保留在 MEMORY.md）：L1-4, L6-10, L30, L33, L40, L46,
>   L49(B1 部分), L51-63, L66, L68, L70, L75(A/B/C 三路径部分), L78-80, L82-87
> - 历史（13 单元，仅本归档保留）：L13, L14-18, L19-23, L24-29, L31-36, L37-41,
>   L41(45060), L42, L45, L48, L72, L73, L74, L76
> - 过期（4 单元，被后续批次覆盖，精简后不再出现）：L47「唯一触发条件=原文到手 /
>   host 侧不产出改动」、L67 旧批次链、L69 基线 256141、L71 挂账 10 槽
> - 混合：L75（A/B/C 三路径活 + 「当前状态」/256142 过期）、L49（B1 活 + PROP 编号史）、
>   L22 旧链（过期）
> - 反向验证抽查：批次 4.5 见 L73、批次 5 见 L74、批次 6-A 见 L76；
>   批次 6-C 不在此归档，见 `2026-11-14.md` L184-224。

--- 以下为精简前 MEMORY.md 全文，逐字原样（分隔符本身不属于原文）---

# 项目记忆：ADHD 文献 AI语料层

## 项目定位
工程根 `F:/ADHD文献/`，核心工作区 `08_AI语料层/`。构建 63 页 ADHD 科普语料（BookStack 实例）的 AI 检索/应答质量保障体系：页面 metadata + chunk + 评测集三位一体。

## 全局约束（硬规则，除非用户显式裁决）
- 不改正文（不改源页面文字）
- 只报差异（扫描/对账只产出差异报告，不直接动文件）
- 不重切 chunk（chunk 切分一旦定稿不再重切）
- 不回填 metadata（除非显式裁决才回填）

## 阶段状态（截至 2026-11-13）
- **阶段三 已结项**：跨页对账 241 有向边、术语库无硬矛盾、边界一致17(一致8/缺失1/矛盾0/语义一致6/未覆盖2)、矛盾检测20题否19/部分1/是0。角色差异4组：B42↔B43、B32↔B44组1(阈值B05↔A04)、B32↔B44组2(路径B03↔B22)、C03↔B10；B37↔B45 单列安全事件路由表述差异（非角色差异）。
- **阶段四 已结项（模拟检索评测）**：
  - 评测集 `阶段四_评测集草案_30题.csv`（30题，专项6+覆盖24）。
  - 结果 `阶段四_评测结果_30题.csv` + 报告 `阶段四_评测报告.md`。
  - **命中率两值并存**：原设定 27/30(90.0%)；修正设定 28/30(93.3%)。修正：Q11 必须A04→A07、Q22 必须A06→A09（均评测集设定错，非检索问题；A07/A09 本在top5）。Q6 必须B05 为真检索缺口（维持）。
  - 具体度 0/1/29（仅 Q6 为1）；越界召回缺失 1处(Q6)；B44 错用 0处。
- **阶段五 已结项（治理精简 + 检索层策略）**：
  - `06_治理/治理标准_v2.md`：三档（保留5/降级4/砍掉4），第七批起执行；四项硬规则（不改正文/只报差异/不重切chunk/不回填metadata）守边界。
  - `06_治理/校验记录模板_v2.md`：≤1 页四块（概况/评分表/差异清单/快照哈希），字数口径=甲'。
  - `09_检索层/检索层策略_v1.md`：七块落地到具体字段（召回输入/可独立检索·双向召回·前置依赖/案例声明/角色护栏 B44↔B32/证据状态/零用药 A06/生成层安全路由 B37·C03）。状态=规则先定、部署后实装。
  - 知识库侧本地工作收口；剩余全部挂部署后待办。
- **阶段六 已启动（P0+P1 本地收口，2026-11-12）**：用户采纳 P0-P4 方案中的 P0+P1 现在做，P2-P4 挂部署后；条目比例 程序性60%/解释性40%。
  - 新建 `schema/entry.yaml`（源条目 schema 冻结契约 v1）、`agent_manifest.yaml`（共享状态机 + 路由优先级 1/2/3 + 双视图 + 安全底线）。
  - 新建 `03_agent编译/`：build.py（单命令校验+双产物编译+retrieve+selftest）、validators/（schema_check / predicate_equiv / safety_scan / exit_exists 四条 CI 硬规则）、output/（chunks.jsonl + skill_registry.json）。
  - 新建 `05_审核与运营/guardrail_rules.yaml`（用药/诊断/绝对化/贬损 四类，由 C-PEMAT-P 转化）。
  - 新建 `02_内容包/书籍E_学科辅导支架/`：10 条源条目（6 程序性 + 4 解释性），从书籍 B（B01/B08/B09/B14/B15）派生重组，**未改正文**。
  - **验收全绿**：schema_check(10) / predicate_equiv(34560 状态点断言一致) / safety_scan(22) / exit_exists(6)；selftest 通过（10条 / 6+4 / 家长-儿童角色零泄漏 / 场景可达）。依赖 PyYAML（`03_agent编译/requirements.txt`）。
  - **架构决策（张力 #2 处理）**：`03_agent编译` 作**并行新层**；既有 `03_chunk/chunks_全量58页.csv` 与 `检索层策略_v1.md` 不动。新 chunks.jsonl/skill_registry.json 仅承载书籍E 条目；未来部署时再决定是否把全库重过新管线（挂决策点）。
- **阶段六 P2/P3/P4 本地闭环已跑通（2026-11-12 晚）**：用户裁决「先不推 GitHub」（推远程=部署侧动作，与"部署条件不具备"冲突；半成品快照无意义），先做 P2/P3/P4 中可脱离运行时验证的纯函数部分。
  - **P2** `03_agent编译/router.py`：三态 skill/retrieve/none，优先级 0 撤除(exit_condition)→1 skill(注入静默)→2 检索→3 显式 none(no_scaffold，禁自由生成)；角色分离在 view=child|parent 的 audience 允许集合。`validators/router_tests.py` 6917 状态点全绿，角色泄漏 0。
  - **同源契约（用户点名最隐蔽的坑）**：`router.py` 用 `from build import eval_predicate`；断言 `router.eval_predicate is build.eval_predicate is _common.eval_predicate` 成立并进 CI。router 内无任何硬编码状态比较，封死"两套条件漂移"。
  - **P4** `05_审核与运营/regression/golden_trajectories.jsonl` 18 条(15 conformance+3 diagnostic) + `validators/regression.py` + `回归报告.md`：回写前基线 conformance 24/24、撤除率88.9%、过早介入1/6、角色泄漏0、恢复延迟1.00轮。**识别 3 个真实缺陷**：tr_D1/D3 过度介入（解释块 when 无知识缺口/ownership 约束）、tr_D2 撤除边界（exit_when 仅认 on-task，re-entry 中间态无归属）。
  - **P3** `guardrail_node.py`（pass/block/rewrite 独立节点，前后双节点）+ `guardrail_tests.py`：10 条违规全拦截漏放率0%、误拦率0%（基线）。**修掉规则表两处真实缺陷**：pattern 含 `*` 通配符永不命中（改字面量）、`"处方"` 误拦标准转介免责句"有处方权的医生"（精准化为 开处方/处方药/按处方）。`ci/agent-ci.yml` 写好但放 `03_agent编译/ci/` 且仅 workflow_dispatch，**未启用**。
  - **统一入口（回写前）** 9/9 组绿、41582 断言/状态点、0 失败。
- **阶段六 v1.1 三处缺陷回写完成（2026-11-13）**：用户拍板 ①D1/D3 走**内容层**（改源条目 when，不走 router 静默）②D2 走**降级支架**（re-entry 给 light 支架，而非撤除/零支架）。推送仍需用户**显式改口**：跑通是必要非充分条件，"部署条件不具备"裁决未解除。
  - 拍板前读实发现三处与前提不符并回告：①`when` 白名单无 `consecutive_successes`，且 `!=` 对枚举在 `_common.eval_predicate` 下失效（非 in 比较走 `int(sv)`），故"知识缺口"只能用 `[drift, re-entry]` 代理 ②6 个 callable 的 `exit_condition` **已全部**带 `cs>=1/2` 稳定条件 ③router 在 re-entry 中间态本就落零支架，`exit_when satisfied` 与 `no_scaffold` 行为相同、只差 reason。
  - 回写：4 个解释性条目 `when` 加 `attention_state:[drift,re-entry]` + `ownership:[child-leading,parent-hinting]`；`schema/entry.yaml` 升 **v1.1** 增 `callable.scaffold_level(full|light)`；新增第 11 条 `parent_reentry_light_01.md`（re-entry 触发、cs>=2 撤除，从 B01/B09 派生未改正文）；`build.py` 产物带该字段、`router.py` **仅通用透传不新增任何状态判断**、`regression.py` 支持断言；`agent_manifest.yaml` 增 `scaffold_levels` 说明节但 routing 三态不变。
  - **产物哈希（P3 规则四）本地补齐**：`output/manifest.sha256` 覆盖 11 源条目+2 产物=13 项；`verify_all.py` 重编译前独立校验 + `hash_selftest` 2 负例可证伪。**抓到真缺陷**：`build.py` 的 `ROOT` 原多退一级算成 `F:\`，致 manifest 只记 2 产物、11 源条目全漏（假绿）；已修为退一级。
  - **验证**：`verify_all.py` → **11/11 组绿、45060 断言/状态点、0 失败**；conformance **29/29**、诊断案例 0、角色泄漏 0；撤除率 88.9%→**100%**、过早介入 1/6→**0/6**。联动期望仅 `tr_011`、`tr_012 turn2`（retrieve→none/no_scaffold）+ selftest 第5项输入 on-task→re-entry，逐条改前→改后见总报告 §四。
  - 本轮未推 GitHub、未启用 Actions、未动 63 页正文/chunk/metadata/08 既有结项产物/`guardrail_rules.yaml`。

## 阶段 A 已关闭 / 阶段 B 待启动（2026-11-13 收尾口径）
- **阶段 A（parent-cool 复刻地基）已关闭**，HEAD `14590b4`，三步 commit `f4ba129`(2.5a 多目录扫描+source_id 识别源条目) → `af7dfd0`(2.5b predicate_equiv 抽 `iter_states()` 单一状态源 + `parent_affect_level` 进维度) → `14590b4`(2.5c 空 `required_params` 须配 >20字 `exempt_reason` 才放行)。终态 `verify_all` **13/13 绿 / 193757 断言 / predicate_equiv 186624 / 偏离率 0.0%**；`params_exempt=0`。产物仍 18 chunks / 11 skills / 25 轨迹。
- **阶段 B 服务实现已拍板（非待定）**：本地服务用**标准库 `http.server`，零新依赖**，`/api/calm_script` + `/api/health` 接口与 `test_server.py` 完全不变；`09_家长端工具/parent_cool_clone/server/requirements.txt` 删掉或置空。**不要误删** `03_agent编译/requirements.txt`（PyYAML，编译管线依赖）。批次 2 直接按 `http.server` 实现，不再询问。
- **阶段 B 唯一真实触发条件 = parent-cool 原文到手**（本地路径，或 URL + 抓取许可 → 逐字落 `00_来源治理/_staging/` 留哈希）。原文到位后按批次 0→1→2→3→4 原子推进；**在此之前 host 侧不产出任何项目改动**。
- 批次 0 萃取时顺带判 `parent-cool` 接入卡 `action_granularity`（大概率 `task_level`，须确认有无「认知动作级」段落），结果直接写进卡、不单独问。火气值折中：日志存 1—5 原值、谓词压三档 `low/mid/high`（1—2/3—4/5）。
- 提案号续接：PROP-0003 已被 `low_pressure_task` 占用；阶段 B 从 **PROP-0004（A 类 parent_affect_level）/ PROP-0005（B 类 parent_escalation scenario）** 起。B1 路线：`handle_parent_escalation()` 只调 `build.retrieve` + `guardrail_node.judge`，**不走 `router.route()`**；条目仍进编译管线受 6 条硬规则约束。

## 部署后待办（挂账，不阻塞本地收口；部署条件具备后逐项启动）
1. Q6/B05 查询锚点补强（B05 增"到什么程度/该带去看医生/摔东西/连续不理人"）
2. B44 角色护栏实装（家长/亲子问法下降权或标注"成人本人版"，对齐 B32↔B44）
3. 真实向量检索补测（Q6 真缺口复核；同步复核 Q11/A07、Q22/A09）
4. Q11/Q22 修正留痕进部署后复核清单
5. C/D 书签核与切分
6. BookStack 实例验证（权限、导航、角色可见性）
7. §2 第3条逻辑边界核对：查 `chunks_全量58页.csv` 是否有"双向召回=是 且 可独立检索=是"的块；有则补规则（不进随附子块池，按可独立检索块处理），无则把"不论自身可独立检索取值"改为"可独立检索=否 的块"。
8. **阶段六 P2**：状态机与路由逻辑接入运行时（本地判定器已跑通；实际调度器桩与运行时接入挂部署后）。
9. **阶段六 P3**：CI 四条硬规则接入实际 GitHub Actions（当前为本地校验器 + build.py 内调用）；guardrail 作为独立节点（pass/block/rewrite）接入生成层前后。
10. ~~阶段六 P4 轨迹回归集~~ **已本地做（11-12 建、11-13 回写后重录基线）**：18 条 / 29 turn 全 conformance、诊断案例 0。剩余仅「真实 agent 轨迹采样」「不同模型做 judge 阈值门控」「Actions 实际执行」挂部署后。
11. **阶段六 待放行**：①~~三处诊断案例调整~~ **已回写并验证全绿（2026-11-13）** ②**推 GitHub 里程碑快照仍待用户显式改口**——跑通是必要非充分条件，"部署条件不具备"裁决未解除；推送需 gh api 动远程状态，不自动放行 ③未来部署时决定全库是否重过新编译管线。
- **已知小问题（不阻塞，顺手修）**：检索层策略 v1 §2 两处排版多空格（"父 块id"、"不论自身 可独立检索 取值"），下次编辑时修掉。

## 阶段 B（parent-cool 功能复刻）状态（2026-11-13 起，2026-11-14 收尾完成）
- **前提（用户改口，覆盖此前「阶段 B 唯一阻塞=parent-cool 原文」口径）**：不依赖原文；功能按七模块复刻；文案只从现有 18 条源条目逐字取；映射不上的标 `pending_batch3` 不编造。核心目录 `09_家长端工具/parent_cool_clone/`。
- 批次链（每批独立本地 commit，均未推远程 / 未启用 Actions）：`0875167`(0 功能契约+文案盘点) → `b07e6d3`(1 静态复刻) → `c916e40`(2 标准库 `http.server` 桥接) → **`55eb487`(3 内容侧落地)** → **`d620e84`(4 前端真接线+对照验收，阶段 B 复刻完成)**。
- 批次 3 契约：`schema/entry.yaml` **v1.2**（`scenario` 增 `parent_escalation`、`when` 增 `parent_affect_level=[low,mid,high]`）；`PT_PARENT_ESCALATION_01` 是唯一 `required_params: []` 豁免模板；`parent_cool` 卡为 **`project_internal`**（原文不在手，红线=项目内部约束，**不是原文卡**，日后拿到原文须另行接入）；书籍 F 6 条 explanatory 条目逐字摘句可溯；`regression.py` v1.3 增 `entry_via` 旁路分支。
- 验收基线：`verify_all` **14/14 绿 / 256141 断言**；24 chunks / 11 skills；conformance 46/46；偏离率 0.0%；三档命中 6/6/6。
- **契约口径硬事实（防再犯）**：① `params_exempt` 按**条目**计数 → 0→6，方案写的「0→1」是豁免模板种类；② 状态空间维度阶段 A 2.5b 已扩完（10368 点不变），186624→248832 是条目数增加；`diff_mode` 实跑 7872→10368 / added 2496 / scope unchanged；③ `schema_check.py` 不校验嵌套 `when.allowed_fields`，靠第 14 组兜住；④ 枚举字段必须写 list，`eval_predicate` 对 `==` 会 `int(sv)`；⑤ 全套模板三档全命中时三档输出相同，条目级内容分档需 `value_adjusted`，本批次未擅自引入。
- **挂账**：10 个 `pending_batch3` 静态槽位（3 撤退 / 1 修复 / 5 预警 / 1 免责）无来源、如实保留；家长火气 1—5 分档话术、身体预警表、修复话术、免责声明原文等原文到位后另走来源接入。
- **批次 4 已完成（2026-11-14，commit `d620e84`）**：api.js 真 fetch + 绝对 BASE `127.0.0.1:8765` + probeHealth + 3s 硬超时；app.js AI 区 degraded/blocked/正常三分支分开渲染、blocked 撤退区高亮、disclaimer 只取服务端字段、loading + 降级 3s 冷却；占位文案中性化（`PENDING_BY_GROUP`/`PENDING_BY_SLOT`，无批次号残留，status 仍 pending）；README 三栏清单 + 零依赖说明。验收：test_static 42/42、test_api 21/21、test_server 6/6、verify_all 14/14 与批次 3 完全一致（256141/248832/24·11/46·46）；服务在/不在端到端真实 HTTP 实测通过。
- **批次 4.5 已完成（2026-11-14，commit `811d649`，阶段 B 定稿）**：用户裁决 D-09 非可挂账项后收口三件事——①server.py 全响应加 `ACAO: *` 三头 + `do_OPTIONS` 204（仅本地回环）；②DISCLAIMER 占位串（带批次号）换方案给定的中性免责文本（`PENDING` 常量未动，前端置空不渲染；**留痕**：前端静态槽位仍「免责声明原文待补」，与运行时免责暂不一致，原文到位后统一）；③实机验证（浏览器自动化本轮恢复可用）：file:// 直开真接线返回真实台词+三步+新免责、停服降级提示+按钮 3 秒冷却恢复，**均实测通过**。验收：test_server **9/9**（+OPTIONS/ACAO/disclaimer 三测）、test_static 42/42、test_api 21/21、verify_all 14/14 与批次 4 一致。**两项如实保留未实机验**：guardrail blocked 分支（服务端只判知识库文本，situation 不进判定文本，实机不可触发；UI 分支由 mock 覆盖）、375px 视口（后端不支持视口模拟，维持静态断言）。D-07/D-08/D-09 全部关闭；开放挂账仅剩：10 pending 槽位、D-06 三档台词相同、自由文本深度归类、前端静态免责槽位与运行时文案的统一（待原文）。commit 链：`0875167` → `b07e6d3` → `c916e40` → `55eb487` → `d620e84` → `811d649`。详见 `.workbuddy/memory/2026-11-14.md` 与 `parent_cool_clone/README.md`。
- **批次 5 已完成（2026-11-14，commit `7776b22`，阶段 B 定稿批次）**：条目级分档关闭 D-06——①6 条 `parent_escalation` 条目 `when` 由 `[low,mid,high]` 收窄单档（2/2/2：low=no_label/restate、mid=one_step/scope、high=stop/refer，每条显式 `deviation: value_adjusted`，与 golden `tr_PE01..PE06` 逐条一致，回归 46/46 未动即过）；②copy_mapping 三档撤退 3 槽 mapped（同档按 id 序取第一条：no_label/one_step/refer）+ 免责 1 槽 `filled_constant`（新状态值，text 由生成器 ast 从 server.py 机械提取 DISCLAIMER；core.js resolveSlot 配套分支）→ **mapped 15 / pending 6 / filled_constant=1**；③测试联动：parent_escalation_tests 133→134（三档命中 2/2/2+每档集合断言+②'三档 line 两两不同）、test_server 9→10（test_10）、test_static 42/42 守住、test_api 21/21。**验收：verify_all 14/14 绿 / 256142 断言 / predicate_equiv 248832 / 24 chunks·11 skills / conformance 46/46 / 偏离率主口径 0.0%；实测火气 1/3/5 三档 line 两两不同（D-06 关闭实锤）**。两处方案口径偏差如实留痕：断言增量 +1（非方案预期 +2，test_server 不在 verify_all 组内）；`value_adjusted` 行 9→15（非方案写法「6→6」，批次 5 前已有 9 行历史 value_adjusted）。挂账更新：pending 10→6（修复卡 1+五类预警 5）；剩余=修复卡、五类预警、自由文本深度归类、原文到位后的分档话术复核。commit 链：`0875167` → `b07e6d3` → `c916e40` → `55eb487` → `d620e84` → `811d649` → `7776b22`。详见 `.workbuddy/memory/2026-11-14.md` §七。
- **阶段 B 当前状态（2026-11-14 批次 5 收口后，批次 6 方案已收）**：~~剩余挂账全部依赖 parent-cool 原文~~ **口径修正（批次 6 方案）**：真实依赖是**内容来源**而非原文本身（用户 11-13 已明确「文案使用知识库的，我只要它的功能」）——三条路径任一满足即可开工：A=parent-cool 原文（parent_cool 卡升级）/ B=授权抓取文献网页（建 literature 卡，逐字落 _staging 留哈希）/ C=用户直接给 6 条文案（建 `parent_escalation_content` 卡，project_internal，不声称外部来源）。批次 6 方案在 `F:\ADHD文献\批次6执行方案.md`（6a 接入卡→6b 派生 6 条→6c mapped 15→21/pending 6→0→6d 测试联动→6e 验收），**当前冻结等内容，不开工、不编造、不凑数**；pending 清零不是硬目标。方案附带可选项：自由文本深度归类的评估集构建（20—30 条标注集，不依赖外部内容，需用户一句话确认才做）。方案编写纪律：**写方案前先读当前 metrics 与偏离清单再填预期值**（批次 5 两处口径偏差=方案数字错误的裁决教训）。
- **批次 6-A 已完成（2026-11-14，commit `4e7885a`）**：`parent_escalation` 检索确定性审计与加固（等批次 6 内容的空窗期收掉批次 5 遗留行为灰区）。审计结论（`05_审核与运营/regression/批次6A_审计.md` + 可复跑脚本 `_batch6A_audit_print.py`）：①`candidates[0]`=chunks.jsonl 顺序该档第一条（no_label/one_step/refer），排序键 overlap（档位字符串字符集 vs 中文 inject_text）实测全 0 → 稳定排序退化为文件序；②**situation 不参与选择**——retrieve state 只含档位（server.py:105-106）、assemble 收 situation 参数但 body 不用（误导签名）、前端发的 situation 服务端未使用；每档第 2 条（restate/scope/stop）当前永不被选中（预留候选，非删除对象，被 golden tr_PE01..PE06 覆盖）。**处置走文档化不预设「修」**：overlap 对中文几乎无区分度，「修」=功能扩展应另开批次；assemble 去掉无效 situation 参数 + docstring 写明「每档固定第一条、situation 不参与选择」（handle 的 situation 入参保留=API 契约+未来 LLM 化上下文入口）；parent_escalation_tests +4→**138**（每档 first id×3 + 同档不同 situation 同输出×1 可证伪锚点：改选择逻辑必红、强制走行为变更流程）；README 挂账表把 blocked 实机不可触发升级为**明确设计说明**（judge 只判知识库文本 server.py:112）+ 375px 维持静态断言。验收：verify_all **14/14 绿 / 256146（+4，与方案预期逐字一致）**、test_server 10/10、test_static 42/42、test_api 21/21、conformance 46/46、偏离率 0.0%。挂账不变：批次 6 六槽位等内容（A/B/C 三路径）、深度归类评估集待确认。commit 链：… → `7776b22` → **`4e7885a`**。详见 `2026-11-14.md` §九。

## 治理标准生效
第七批起执行治理标准 v2；第六批及之前不回溯。部署条件具备前不开新批次。
- 部署条件具备后按"部署后待办"7 项逐项启动；优先 BookStack 实例 + 真实向量检索补测（Q6/B05、B44 护栏、§2 边界）。

## 仓库与 GitHub 上传通道（环境网络事实，跨会话有效）
- 远程：`git@github.com:Stoicesf/adhd-knowledge-base.git`（用户 2026-11-12 提供；本地 remote 已设为 SSH，本地分支已 `master`→`main` 对齐）。
- **环境网络约束**：本机经本地代理出网，代理**放行 `api.github.com`（gh CLI 可用，已登录账号 Stoicesf、有 push 权限），但封锁 `github.com` 的 git smart-HTTP（CONNECT 502）与 SSH（无 connect/nc/ncat/socat 隧道工具、代理不稳）**。因此 `git push` / `git fetch` / SSH 推送在当前环境**均不可行**。
- **可用的上传路径**：GitHub **Git Data REST API（经 `gh api`）**。2026-11-12 已用此法把 214 个跟踪文件（`.gitignore` 排除 `.workbuddy/` 与 `*.bak`）作为一个提交推到 `main`，提交 `17972d73ab5d13e09bd3b1b729c8362cb797bb79`（215 文件含保留的 README）。方法：先取远程 main 树 SHA 作 `base_tree`，按 ~30 文件分块 `POST /git/trees`（内联 base64 content 自动建 blob），链式叠加，末块树 `POST /git/commits`（parent=远程 HEAD）+ `PATCH /git/refs/heads/main`。
- 本地 `.git` 在历史已存（初始提交 + 上述对齐），仅远程同步走 API；未来若在可直连 GitHub 的环境，`git push -u origin main` 即可。
- 上传脚本因代理抖动曾遇 `git ls-files` 八进制转义坑：必须 `git -c core.quotePath=false ls-files` 取原始 UTF-8 路径；`gh api contents/<中文路径>` 需 URL 编码（否则 404 误报），核对请用 `git/trees?recursive=1` 过滤。
