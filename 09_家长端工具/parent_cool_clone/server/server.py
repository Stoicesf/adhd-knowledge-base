# -*- coding: utf-8 -*-
"""阶段 B 批次 2 · 本地服务桥接（标准库 http.server，零新依赖）

接口：
  GET    /api/health                 -> {"status":"ok","version":"0.1"}
  POST   /api/calm_script
    body {"anger_level":1-5,"situation":str}
    -> {"line":str,"steps":[str,str,str],"disclaimer":str,
        "degraded":bool,"blocked":bool}
  OPTIONS 任意路径                    -> 204 + CORS 头（批次 4.5a）
  所有响应均带 Access-Control-Allow-Origin: * 等三个 CORS 头（仅本地回环使用）。

分层纪律（方案 §纪律与边界）：
  - 运行期入口 handle_parent_escalation() 只调 build.retrieve + guardrail_node.judge，
    **不调 router.route()**：家长情绪是独立 scenario，不与辅导状态机打架。
  - 批次 6D Q3（设计意图文档化）：**本工具不感知孩子状态**。入参只有家长火气
    1—5 与自由文本 situation（后者按批次 6A 审计不参与台词选择）；火气高时只给
    **家长自身的行动指令**（合上作业、离开书桌、联系专业支持），孩子状态由辅导端
    的共享状态机处理，两者不在此合流。这是批次 3 用户拍板的 B1 路线，不是遗漏；
    若将来需要家长火气 + 孩子状态联合输入，属 API 契约变更，另走提案。
    审计证据见 05_审核与运营/regression/批次6D_审计.md。
  - line 与 steps 三段**各自**过 guardrail_node.judge()，任一 block 即整单 fallback。
  - degraded（服务不在 / 条目未派生）与 blocked（guardrail 拦截）**分开**，不混用。
  - 免责声明（批次 4.5b）：原 parent-cool 原文不在手；占位串曾带批次号用户可见（D-07），
    已按批次 4.5 方案替换为中性免责文本（见 DISCLAIMER），原文到位后再联动替换。
  - 批次 2 时 parent_escalation 条目尚未派生 → retrieve 返回空 →
    degraded=True 是预期态；**批次 3 已派生 6 条 explanatory 条目**，
    正常路径不再 degraded，degraded 只由「服务不可用 / 条目被移除」触发，
    blocked 只由 guardrail 拦截触发，两者仍严格分开。

启动：python server.py [--port 8765]
"""
import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
CLONE = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(CLONE, "..", ".."))
COMPILE = os.path.join(ROOT, "03_agent编译")

# 复用编译管线的 retrieve 与 guardrail 判定器（同源契约，不复制实现）
sys.path.insert(0, COMPILE)
import build                     # noqa: E402
import guardrail_node            # noqa: E402

VERSION = "0.1"
PENDING = "文案待补充（批次 3 派生）"
# 免责声明（批次 4.5b 收口）：原 parent-cool 原文仍不在手，占位串带批次号用户可见（D-07），
# 按批次 4.5 方案给定的中性文本替换。原文到位后只替换本常量与
# data/copy_mapping.json 的 disclaimer 槽位（前端静态槽位当前仍显示「免责声明原文待补」，
# 与本运行时文案暂不一致，原文到位后统一）。
DISCLAIMER = ("本工具为家长情绪自助参考，不替代专业心理咨询、医学诊断或学校正式评估。\n"
              "如孩子出现持续情绪困扰或家庭冲突升级，请寻求专业帮助。")
DEGRADED_HINT = "AI 台词暂不可用，可先看下方撤退方案"
BLOCKED_HINT = "请先看撤退方案"

# 批次 4.5a：CORS 头。本地工具、仅监听回环、无认证无写操作，用 `*` 而非白名单
# （file:// 的 null 起源白名单写法不统一）；README 注明仅本地回环使用。
CORS_HEADERS = [
    ("Access-Control-Allow-Origin", "*"),
    ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
    ("Access-Control-Allow-Headers", "Content-Type"),
]

ANGER_TIER = {1: "low", 2: "low", 3: "mid", 4: "mid", 5: "high"}


def _fallback(level, blocked=False):
    """静态撤退卡兜底。撤退文案在 copy_mapping 里仍是 pending，
    因此这里不编造撤退动作，只返回占位 + 指引，与前端占位口径一致。"""
    return {
        "line": PENDING,
        "steps": [PENDING, PENDING, PENDING],
        "disclaimer": DISCLAIMER,
        "degraded": not blocked,
        "blocked": blocked,
        "level": level,
        "hint": BLOCKED_HINT if blocked else DEGRADED_HINT,
    }


def assemble_line_and_steps(candidates):
    """把检索命中块组装成 1 句台词 + 3 步。
    本批次不做自由生成：逐字取 inject_text 的前若干句，避免「AI 编话术」。
    批次 6A 审计结论（05_审核与运营/regression/批次6A_审计.md）：每档固定返回
    candidates[0]（chunks.jsonl 顺序中该档第一条）；situation 不参与选择，
    用户输入是未来 LLM 化的上下文入口，不是检索排序依据。
    同档不同 situation 输出一致由 parent_escalation_tests 可证伪断言锁定；
    改动该行为视为行为变更，需走流程。
    """
    text = (candidates[0].get("inject_text") or "").strip()
    # 逐字切句，不改写、不概括。中文句号/分号/换行均作边界。
    parts = [p.strip() for p in text.replace("\n", "。").split("。") if p.strip()]
    line = (parts[0] if parts else PENDING) + ("。" if parts else "")
    steps = []
    for i in range(3):
        steps.append((parts[i + 1] + "。") if i + 1 < len(parts) else PENDING)
    return {"line": line, "steps": steps}


def handle_parent_escalation(anger_level, situation, retrieve_fn=None, judge_fn=None):
    """纯函数入口。retrieve_fn / judge_fn 可注入，便于 test_server.py 构造负例。"""
    # 严格整数校验：不可用 int() 强转——int(1.5) 会静默变 1、int("3") 会静默变 3，
    # 与前端 PCCore.angerTier 的 Number.isInteger 口径不一致（test_server 负例抓到）。
    if isinstance(anger_level, bool) or not isinstance(anger_level, int) \
            or anger_level not in ANGER_TIER:
        raise ValueError("anger_level 必须是 1-5 整数")
    level = ANGER_TIER[anger_level]

    retrieve = retrieve_fn or build.retrieve
    judge = judge_fn or guardrail_node.judge

    candidates = retrieve("parent", "parent_escalation",
                          {"parent_affect_level": level})
    if not candidates:
        # 预期态（批次 2）：条目未派生，链路先通、内容批次 3 补。
        return _fallback(level, blocked=False)

    draft = assemble_line_and_steps(candidates)
    verdicts = [judge(draft["line"])] + [judge(s) for s in draft["steps"]]
    if any(v["decision"] == "block" for v in verdicts):
        return _fallback(level, blocked=True)

    return {
        "line": verdicts[0]["output"],
        "steps": [v["output"] for v in verdicts[1:]],
        "disclaimer": DISCLAIMER,
        "degraded": False,
        "blocked": False,
        "level": level,
        "hint": "",
    }


def _validate_request(payload):
    """批次 6C.6 输入校验：在调用 handle_parent_escalation 前把边界输入挡在 400。
    返回错误信息字符串或 None。anger_level 的严格校验在 handle 内保留（双保险）。"""
    if not isinstance(payload, dict):
        return "body 必须是 JSON 对象"
    level = payload.get("anger_level")
    if not isinstance(level, int) or isinstance(level, bool) or level not in (1, 2, 3, 4, 5):
        return "anger_level 必须是 1—5 的整数"
    sit = payload.get("situation", "")
    if not isinstance(sit, str):
        return "situation 必须是字符串"
    if len(sit) > 2000:
        return "situation 超长（>2000 字符）"
    return None


class Handler(BaseHTTPRequestHandler):
    server_version = "ParentCool/" + VERSION
    # 批次 6C 补正（6C 收尾确认实测发现）：读超时。声明了 Content-Length 却一字节不发的
    # 半开请求会让 rfile.read(n) 永久阻塞，ThreadingHTTPServer 每连接一线程，可被逐个
    # 堆叠（仅本地回环可达，故按方案 6C.2「超时保护」处理，不回 400）。超时后
    # http.server 的 handle_one_request 捕获 socket.timeout 并 close_connection，线程回收。
    timeout = 5

    def _send(self, code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in CORS_HEADERS:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        # 批次 4.5a：跨源预检。204 无 body，只回 CORS 头
        self.send_response(204)
        for k, v in CORS_HEADERS:
            self.send_header(k, v)
        self.end_headers()

    def do_GET(self):
        if self.path.split("?")[0] == "/api/health":
            self._send(200, {"status": "ok", "version": VERSION})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path.split("?")[0] != "/api/calm_script":
            self._send(404, {"error": "not found"})
            return
        # 批次 6C.7 Content-Length 守门：缺失拒绝、非法拒绝、超 1MB 不读 body
        # （防「声明 1MB 只发 10 字节」把读线程吊死在 rfile.read 上——6C.2 实测坐实）
        cl_raw = self.headers.get("Content-Length")
        if cl_raw is None:
            self._send(400, {"error": "缺少 Content-Length 头"})
            return
        try:
            n = int(cl_raw)
        except ValueError:
            self._send(400, {"error": "Content-Length 不合法"})
            return
        if n < 0 or n > 1024 * 1024:
            self._send(400, {"error": "Content-Length 超出允许范围（≤1MB）"})
            return
        try:
            payload = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            # 批次 6C：JSONDecodeError 是 ValueError 子类，旧代码会借道
            # 下面的 ValueError 分支误报为「火气值须为 1-5 整数」——单独分流
            self._send(400, {"error": "body 不是有效 JSON"})
            return
        err = _validate_request(payload)
        if err:
            self._send(400, {"error": err})
            return
        try:
            # 批次 6C 补正：situation 缺失时取空串（_validate_request 已按
            # payload.get("situation","") 视为可选并放行，此处若用 [] 直取会
            # KeyError → 500，与校验口径自相矛盾；前端 api.js 默认补 '' 故
            # 仅手工请求可达，但 500 仍属输入健壮性缺陷）。
            result = handle_parent_escalation(payload["anger_level"],
                                              payload.get("situation", ""))
        except ValueError as e:
            # handle 内部严格校验的双保险；错误信息不暴露内部实现细节
            self._send(400, {"error": "参数不合法：火气值须为 1-5 整数"})
            return
        except Exception:
            # 批次 6C：真正意外的内部错误不再伪装成 degraded 200（旧行为把 bug
            # 掩盖成降级），如实回 500；前端 fetch 抛错后走既有降级 UI
            self._send(500, {"error": "服务内部错误"})
            return
        self._send(200, result)

    def log_request(self, code="-", size="-"):
        # 批次 6C.8 日志最小化：只记 4xx/5xx，成功请求与健康检查不刷 stderr
        # （请求行不含 body，situation 不会进日志；覆盖的是刷屏与日志积累）
        try:
            c = int(code)
        except (TypeError, ValueError):
            c = 500
        if c >= 400:
            super().log_request(code, size)

    def log_message(self, fmt, *args):
        sys.stderr.write("[parent-cool] %s - %s\n" % (self.address_string(), fmt % args))


def make_server(port=8765):
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    srv = make_server(a.port)
    print(f"parent-cool server http://127.0.0.1:{a.port}  version={VERSION}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
