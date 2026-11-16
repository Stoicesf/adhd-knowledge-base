# -*- coding: utf-8 -*-
"""阶段六 · P2 路由判定器（本地纯函数，不依赖运行时）

输入：状态快照 + skill_registry.json + chunks.jsonl
输出：skill / retrieve / none 三态决策

硬约束（本文件最重要的设计意图）：
  **谓词求值直接复用 build.py 顶层暴露的 eval_predicate 对象**，不另写条件判断。
  P1 已在 34560 个状态点上断言「注入过滤 ≡ skill 触发」；若 router 手写一套
  if/else，就是第三次「两套条件漂移」的起点。故：
      router.eval_predicate is build.eval_predicate is _common.eval_predicate
  由 validators/router_tests.py 断言，CI 可验。

路由优先级（agent_manifest.yaml::routing，硬编码，不允许各调用点自行决定）：
  0. active_skill 的 exit_condition 满足 → none（撤除，不重复注入）
  1. skill trigger_condition 命中 → skill 为主，该微步骤内注入通道静默
     （仅 audience=both 的边界解释可通过）
  2. 未命中 skill → 检索通道（结构化谓词过滤 → 命中 retrieve）
  3. 两者均未命中 → 显式 none（no_scaffold），不允许 LLM 自由生成辅导策略

角色护栏（P2 验收：角色泄漏率 = 0）：
  view=child  → 只允许 audience ∈ {child, both}
  view=parent → 只允许 audience ∈ {parent, both}
  所有 skill / chunk 在求值前按 view 硬过滤，角色分离发生在状态之上而非 prompt 层。

场景白名单（PROP-0006 / 阶段 B 批次 6-E）：
  scenario=None 不再表示「不收窄」，而是「只查辅导场景」，白名单单一来源为
  agent_manifest.yaml::coaching_scenarios。scenario 非 None 仍是精确匹配。
  场景判定只有 scenario_in_scope() 一份实现，skill 分支的 passthrough 与
  主 in_scope 共用，避免两处条件漂移（同 eval_predicate 的同源契约精神）。
"""
import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "validators"))

# ↓↓↓ 直接 import build.py 中已用的谓词求值函数（同一对象），不另写一套 ↓↓↓
from build import eval_predicate
from _common import eval_predicate as _common_eval_predicate
# ↑↑↑ 同源契约：router.eval_predicate is build.eval_predicate is _common.eval_predicate

OUT = os.path.join(HERE, "output")
SKILLS_PATH = os.path.join(OUT, "skill_registry.json")
CHUNKS_PATH = os.path.join(OUT, "chunks.jsonl")

ALLOWED_AUDIENCE = {
    "child": {"child", "both"},
    "parent": {"parent", "both"},
}

MANIFEST_PATH = os.path.join(os.path.dirname(HERE), "agent_manifest.yaml")
_COACHING_CACHE = {}


def load_coaching_scenarios(manifest_path=MANIFEST_PATH):
    """读取辅导场景白名单（唯一事实来源 = agent_manifest.yaml::coaching_scenarios）。

    模块级缓存：route() 每次只查内存 frozenset，不产生逐次文件 IO。
    缺键 / 非法值一律 fail loud（ValueError），**不静默回退**到旧语义
    「None = 不收窄」——静默回退会让白名条形同虚设而验收全绿（假合规）。
    """
    key = os.path.abspath(manifest_path)
    if key in _COACHING_CACHE:
        return _COACHING_CACHE[key]
    try:
        import yaml  # 延迟导入：仅首次加载 manifest 时需要
        with open(manifest_path, encoding="utf-8") as f:
            doc = yaml.safe_load(f) or {}
    except Exception as ex:
        raise ValueError(
            f"无法读取辅导场景白名单：{manifest_path}（{ex}）") from ex
    wl = doc.get("coaching_scenarios")
    if not (isinstance(wl, list) and wl
            and all(isinstance(x, str) and x for x in wl)):
        raise ValueError(
            "agent_manifest.yaml::coaching_scenarios 必须是非空字符串列表；"
            f"实得 {wl!r}。白名单缺失不得静默回退（PROP-0006 fail loud）")
    frozen = frozenset(wl)
    _COACHING_CACHE[key] = frozen
    return frozen


def scenario_in_scope(rec_scenario, scenario, coaching_scenarios):
    """场景收窄的**唯一实现**（PROP-0006）。

    scenario 非 None → 精确相等（与 6E 之前行为逐位相同）；
    scenario is None → 只命中辅导场景白名单，非辅导场景
    （当前为 parent_escalation）不再串入。
    in_scope 与 skill 分支的 passthrough 共用本函数，防两套条件漂移。
    """
    if scenario is not None:
        return rec_scenario == scenario
    return rec_scenario in coaching_scenarios


def in_scope(rec, allowed, scenario, coaching_scenarios):
    """作用域判定：view 角色护栏 + 场景白名单。

    6E 之前为 route() 内闭包；提为模块级函数以便显式传参、
    让白名单成为可断言的契约，而非隐式捕获的局部变量。
    """
    return rec.get("audience") in allowed and scenario_in_scope(
        rec.get("scenario"), scenario, coaching_scenarios)


def load_artifacts(skills_path=SKILLS_PATH, chunks_path=CHUNKS_PATH):
    with open(skills_path, encoding="utf-8") as f:
        skills = json.load(f)
    chunks = []
    with open(chunks_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return skills, chunks


def _allowed(view):
    if view not in ALLOWED_AUDIENCE:
        raise ValueError(f"view 必须是 child|parent，收到 {view!r}")
    return ALLOWED_AUDIENCE[view]


def _decision(route, view, state, reason, skill=None, injected=None,
              retrieval_silent=False, scaffold_level=None):
    return {
        "route": route,
        "view": view,
        "state": dict(state),
        "skill": skill,
        "injected_chunks": injected or [],
        "retrieval_silent": retrieval_silent,
        # v1.1：仅通用透传产物字段（full|light|None），不含任何状态判断。
        # 降级条件写在源条目 when/exit_when，router 不另写第二套条件。
        "scaffold_level": scaffold_level,
        "reason": reason,
    }


def route(state, view, scenario=None, active_skill=None,
          skills=None, chunks=None):
    """单步路由判定（纯函数）。

    state        : 状态快照 dict，字段见 agent_manifest.yaml::state_schema，
                   另可含 consecutive_failures / consecutive_successes（谓词引用）
    view         : 'child' | 'parent'（决定 audience 允许集合）
    scenario     : 可选场景过滤。非 None → 精确匹配；
                   None → 只查 agent_manifest.yaml::coaching_scenarios
                   中的辅导场景（PROP-0006；6E 之前为「不收窄」）
    active_skill : 上一微步骤激活的 skill 名（用于 exit_when 撤除判定）
    skills/chunks: 编译产物；None 时从 output/ 读取
    """
    if skills is None or chunks is None:
        skills, chunks = load_artifacts()
    allowed = _allowed(view)
    coaching = load_coaching_scenarios()

    # ---- 0. 撤除：active_skill 的 exit_condition 满足 → none ----
    if active_skill:
        for s in skills:
            if s.get("name") == active_skill:
                exit_cond = s.get("exit_condition") or {}
                if exit_cond and eval_predicate(exit_cond, state):
                    return _decision(
                        "none", view, state,
                        reason="exit_when satisfied；按撤除条件停止支架，不重复注入",
                        retrieval_silent=True,
                    )
                break

    # ---- 1. skill 优先 ----
    for s in skills:
        if not in_scope(s, allowed, scenario, coaching):
            continue
        trig = s.get("trigger_condition") or {}
        if trig and eval_predicate(trig, state):
            # 该微步骤内注入通道静默：仅 audience=both 的边界解释可通过
            passthrough = [
                c["id"] for c in chunks
                if c.get("audience") == "both" and c.get("type") == "boundary"
                and scenario_in_scope(c.get("scenario"), scenario, coaching)
            ]
            return _decision(
                "skill", view, state,
                reason="skill trigger_condition 命中；该微步骤注入通道静默（防重复支持）",
                skill=s.get("name"),
                injected=passthrough,
                retrieval_silent=True,
                # 通用透传产物字段，不做状态判断（条件只在源条目里）
                scaffold_level=s.get("scaffold_level", "full"),
            )

    # ---- 2. 检索通道（结构化谓词过滤）----
    hits = []
    for c in chunks:
        if not in_scope(c, allowed, scenario, coaching):
            continue
        cond = c.get("when") or {}
        if cond and eval_predicate(cond, state):
            hits.append(c["id"])
    if hits:
        return _decision(
            "retrieve", view, state,
            reason="未命中 skill；结构化谓词过滤命中检索块",
            injected=hits,
        )

    # ---- 3. 显式无支架 ----
    return _decision(
        "none", view, state,
        reason="no_scaffold：skill 与检索均未命中，显式无支架；不允许 LLM 自由生成辅导策略",
        retrieval_silent=True,
    )


def run():
    """P2 最小验收（返回 ok / errors / checked），供 CI 与 verify_all 调用。"""
    from router_tests import run as run_tests
    return run_tests()


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", help="JSON 字符串形式的状态快照")
    ap.add_argument("--view", choices=["child", "parent"], default="parent")
    ap.add_argument("--scenario", default=None)
    ap.add_argument("--active-skill", default=None)
    args = ap.parse_args()
    st = json.loads(args.state) if args.state else {
        "task_phase": "执行", "wm_load": 2, "attention_state": "drift",
        "affect": "neutral", "ownership": "child-leading",
        "consecutive_failures": 2, "consecutive_successes": 0,
    }
    print(json.dumps(route(st, args.view, args.scenario, args.active_skill),
                     ensure_ascii=False, indent=2))
