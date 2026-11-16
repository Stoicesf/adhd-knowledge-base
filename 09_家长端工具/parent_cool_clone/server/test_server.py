# -*- coding: utf-8 -*-
"""阶段 B 批次 2 验收（标准库 unittest，零新依赖）
   批次 3 联动复核：条目派生后 degraded 不再是默认态。

四条必测：
  ① 火气 1/3/5 → low/mid/high（并覆盖 2/4 边界）
  ② 无条目 → degraded=true（批次 3 后改为注入空 retrieve 的**负例**，
     同时加正例断言真实 retrieve 已命中、不再 degraded）
  ③ 构造会被 guardrail block 的文本 → blocked=true 且走 fallback
  ④ /api/health 正常返回（起真实 http.server 线程 + urllib）

另加两条防假绿：
  ⑤ steps 单独含违规词也必须被拦（证明 line 和 steps 各自过 judge）
  ⑥ 端到端 POST /api/calm_script + 非法入参 400

批次 3 联动说明：本文件两条「预期 degraded=true」断言在 6 条
parent_escalation 条目派生后必然转红，属预期联动，不是缺陷。
改法不是删断言或放宽，而是把 degraded 分支改成可注入的负例，
另加真实检索的正例，使两条分支都被覆盖（与阶段六 v1.1 回写口径一致）。
"""
import json
import os
import sys
import threading
import unittest
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import server  # noqa: E402

PORT = 18765


def _chunk(text):
    return {"id": "fake_escalation", "audience": "parent",
            "scenario": "parent_escalation", "inject_text": text}


class TestHandle(unittest.TestCase):
    def test_1_anger_tier_mapping(self):
        seen = []
        def fake_retrieve(audience, scenario, state):
            seen.append((audience, scenario, state["parent_affect_level"]))
            return []
        for n, expect in [(1, "low"), (2, "low"), (3, "mid"), (4, "mid"), (5, "high")]:
            r = server.handle_parent_escalation(n, "", retrieve_fn=fake_retrieve)
            self.assertEqual(r["level"], expect, f"anger={n}")
        self.assertEqual([x[2] for x in seen], ["low", "low", "mid", "mid", "high"])
        self.assertTrue(all(x[0] == "parent" and x[1] == "parent_escalation" for x in seen))
        for bad in [0, 6, 1.5, "3", None]:
            with self.assertRaises(ValueError):
                server.handle_parent_escalation(bad, "")

    def test_2_no_entries_degraded(self):
        # 负例（批次 3 复核）：注入空 retrieve，证明 degraded 分支仍可达，
        # 且仍与 blocked 严格分开，不是靠「服务碰巧有条目」蒙混过关。
        r = server.handle_parent_escalation(
            3, "错题又错了", retrieve_fn=lambda a, s, st: [])
        self.assertTrue(r["degraded"])
        self.assertFalse(r["blocked"])
        self.assertEqual(r["line"], server.PENDING)
        self.assertEqual(len(r["steps"]), 3)
        self.assertEqual(r["hint"], server.DEGRADED_HINT)
        self.assertEqual(r["disclaimer"], server.DISCLAIMER)

        # 正例（批次 3 新增）：条目已派生，真实 build.retrieve 不再返回空。
        r2 = server.handle_parent_escalation(3, "错题又错了")
        self.assertFalse(r2["degraded"], "条目已派生，不应再走 degraded")
        self.assertFalse(r2["blocked"])
        self.assertEqual(len(r2["steps"]), 3)
        self.assertNotEqual(r2["line"], server.PENDING)

    def test_3_block_text_falls_back(self):
        # 注入含「你就是ADHD」（guardrail_rules.yaml diagnosis_hint / block）的候选，
        # 用真实 guardrail_node.judge，证明护栏真接上，不是 mock 假绿。
        text = "你就是ADHD，先别急。把本子合上。等呼吸平了再说话。今晚到这里就好。"
        r = server.handle_parent_escalation(
            5, "", retrieve_fn=lambda a, s, st: [_chunk(text)])
        self.assertTrue(r["blocked"])
        self.assertFalse(r["degraded"])
        self.assertEqual(r["line"], server.PENDING)
        self.assertEqual(r["steps"], [server.PENDING] * 3)
        self.assertEqual(r["hint"], server.BLOCKED_HINT)
        self.assertNotIn("你就是ADHD", json.dumps(r, ensure_ascii=False))

    def test_5_step_only_block(self):
        # line 干净，第二步含「就是懒」（neurodiv_neg / block）
        text = "先停一下。他就是懒，得催着写。把第一句读一遍。今晚到这里。"
        r = server.handle_parent_escalation(
            2, "", retrieve_fn=lambda a, s, st: [_chunk(text)])
        self.assertTrue(r["blocked"], "steps 中的违规词也必须拦截")
        self.assertNotIn("就是懒", json.dumps(r, ensure_ascii=False))

    def test_rewrite_passes(self):
        # 仅命中绝对化表述（rewrite），不 block，输出应被缓和后放行
        text = "这一定能帮到他。先停一下。把第一句读一遍。今晚到这里。"
        r = server.handle_parent_escalation(
            1, "", retrieve_fn=lambda a, s, st: [_chunk(text)])
        self.assertFalse(r["blocked"])
        self.assertFalse(r["degraded"])
        self.assertIn("通常", r["line"])
        self.assertNotIn("一定能", r["line"])

    def test_4_health_and_post(self):
        srv = server.make_server(PORT)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/health", timeout=3) as resp:
                self.assertEqual(resp.status, 200)
                body = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(body, {"status": "ok", "version": server.VERSION})

            req = urllib.request.Request(
                f"http://127.0.0.1:{PORT}/api/calm_script",
                data=json.dumps({"anger_level": 4, "situation": "错题"}).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=3) as resp:
                self.assertEqual(resp.status, 200)
                body = json.loads(resp.read().decode("utf-8"))
                # 批次 3 联动：条目已派生，端到端不再 degraded
                self.assertFalse(body["degraded"])
                self.assertFalse(body["blocked"])
                self.assertEqual(body["level"], "mid")
                self.assertEqual(len(body["steps"]), 3)
                self.assertNotEqual(body["line"], server.PENDING)

            bad = urllib.request.Request(
                f"http://127.0.0.1:{PORT}/api/calm_script",
                data=json.dumps({"anger_level": 9}).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST")
            with self.assertRaises(urllib.error.HTTPError) as cm:
                urllib.request.urlopen(bad, timeout=3)
            self.assertEqual(cm.exception.code, 400)
            self.assertNotIn("Traceback", cm.exception.read().decode("utf-8"))
        finally:
            srv.shutdown()
            srv.server_close()
            t.join(timeout=3)


class TestCorsAndDisclaimer(unittest.TestCase):
    """批次 4.5：CORS 头与免责文案收口验收（6/6 → 9/9）。"""

    @classmethod
    def setUpClass(cls):
        cls.srv = server.make_server(PORT + 1)
        cls.t = threading.Thread(target=cls.srv.serve_forever, daemon=True)
        cls.t.start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()
        cls.t.join(timeout=3)

    def test_7_cors_options_preflight(self):
        req = urllib.request.Request(
            f"http://127.0.0.1:{PORT + 1}/api/calm_script", method="OPTIONS")
        with urllib.request.urlopen(req, timeout=3) as resp:
            self.assertEqual(resp.status, 204)
            self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "*")
            self.assertIn("OPTIONS", resp.headers.get("Access-Control-Allow-Methods", ""))
            self.assertIn("Content-Type", resp.headers.get("Access-Control-Allow-Headers", ""))

    def test_8_cors_headers_on_get_and_post(self):
        with urllib.request.urlopen(
                f"http://127.0.0.1:{PORT + 1}/api/health", timeout=3) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "*")
        req = urllib.request.Request(
            f"http://127.0.0.1:{PORT + 1}/api/calm_script",
            data=json.dumps({"anger_level": 3, "situation": "错题"}).encode("utf-8"),
            headers={"Content-Type": "application/json", "Origin": "null"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "*")
            self.assertEqual(resp.headers.get("Access-Control-Allow-Methods"),
                             "GET, POST, OPTIONS")

    def test_9_disclaimer_neutral(self):
        # 4.5b：disclaimer 不再带批次号（D-07 收口）
        req = urllib.request.Request(
            f"http://127.0.0.1:{PORT + 1}/api/calm_script",
            data=json.dumps({"anger_level": 3, "situation": "错题"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        d = body["disclaimer"]
        for marker in ["批次", "batch", "派生"]:
            self.assertNotIn(marker, d, f"disclaimer 不得含批次标记：{marker}")
        self.assertIn("专业", d)  # 中性免责文本的核心语义仍在

    def test_10_three_tier_lines_differ(self):
        # 批次 5：条目 when 单档化后，火气 1/3/5 的 line 必须两两不同（D-06 关闭证据）
        lines = {}
        for n in (1, 3, 5):
            r = server.handle_parent_escalation(n, "孩子又摔笔了")
            self.assertFalse(r["degraded"])
            self.assertFalse(r["blocked"])
            lines[r["level"]] = r["line"]
        self.assertEqual(len(set(lines.values())), 3,
                         f"三档 line 仍相同，分档未生效：{lines}")
        self.assertEqual(sorted(lines), ["high", "low", "mid"])

    def test_11_invalid_json_clear_error(self):
        # 批次 6C：无效 JSON → 400，且不再借道 ValueError（JSONDecodeError 是其子类）
        # 误报为「火气值须为 1-5 整数」
        req = urllib.request.Request(
            f"http://127.0.0.1:{PORT + 1}/api/calm_script",
            data=b"this is not json{{{",
            headers={"Content-Type": "application/json"}, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(req, timeout=3)
        self.assertEqual(cm.exception.code, 400)
        msg = cm.exception.read().decode("utf-8")
        self.assertIn("JSON", msg)
        self.assertNotIn("火气值", msg)

    def test_12_situation_validation(self):
        # 批次 6C.6：situation 类型与长度校验（6C.2 实测旧实现 200 放行任何值）
        for payload, want in [
            ({"anger_level": 3, "situation": 123}, "situation 必须是字符串"),
            ({"anger_level": 3, "situation": {"a": 1}}, "situation 必须是字符串"),
            ({"anger_level": 3, "situation": "摔" * 2001}, "situation 超长"),
            ([1, 2], "body 必须是 JSON 对象"),
        ]:
            req = urllib.request.Request(
                f"http://127.0.0.1:{PORT + 1}/api/calm_script",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST")
            with self.assertRaises(urllib.error.HTTPError) as cm:
                urllib.request.urlopen(req, timeout=3)
            self.assertEqual(cm.exception.code, 400, want)
            self.assertIn(want, cm.exception.read().decode("utf-8"))
        # 边界值：恰好 2000 字符应放行
        req = urllib.request.Request(
            f"http://127.0.0.1:{PORT + 1}/api/calm_script",
            data=json.dumps({"anger_level": 3, "situation": "摔" * 2000}).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)

    def test_13_content_length_guard(self):
        # 批次 6C.7：CL 缺失 / 声明超限 → 立即 400，不读 body、不卡线程
        # （守门若失效，CL=1MB 分支会 3 秒超时抛错而红）
        import socket as _socket

        def raw(req_bytes):
            s = _socket.create_connection(("127.0.0.1", PORT + 1), timeout=3)
            try:
                s.sendall(req_bytes)
                data = s.recv(4096)
                return data.split(b"\r\n", 1)[0].decode("utf-8", "replace")
            finally:
                s.close()

        line = raw(b"POST /api/calm_script HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n"
                   b'{"anger_level": 3}')
        self.assertIn("400", line)
        line = raw(b"POST /api/calm_script HTTP/1.1\r\nHost: 127.0.0.1\r\n"
                   b"Content-Length: 1048577\r\n\r\n" b'{"anger_l')
        self.assertIn("400", line)

    def test_14_missing_situation_not_500(self):
        # 批次 6C 补正：situation 缺省（_validate_request 按可选放行）必须在
        # do_POST 里按空串处理 → 200；旧实现 payload["situation"] 直取 KeyError →
        # 被兜底 except 吞成 500，与校验口径自相矛盾。
        req = urllib.request.Request(
            f"http://127.0.0.1:{PORT + 1}/api/calm_script",
            data=json.dumps({"anger_level": 3}).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            body = json.loads(resp.read().decode("utf-8"))
        self.assertFalse(body["degraded"], "缺 situation 不应降级")
        self.assertFalse(body["blocked"])
        self.assertEqual(body["level"], "mid")

    def test_15_stalled_body_timeout(self):
        # 批次 6C 补正：声明 CL=1000 却一字节不发，必须由 Handler.timeout 兜住，
        # 线程不得永久阻塞（ThreadingHTTPServer 每连接一线程，可被逐个堆叠）。
        # 用临时缩短的 timeout 让本断言 3 秒内可判，测完复原。
        import socket as _socket
        import time as _time

        old = server.Handler.timeout
        server.Handler.timeout = 0.6
        try:
            s = _socket.create_connection(("127.0.0.1", PORT + 1), timeout=4)
            try:
                s.sendall(b"POST /api/calm_script HTTP/1.1\r\nHost: 127.0.0.1\r\n"
                          b"Content-Length: 1000\r\n\r\n")
                t0 = _time.time()
                try:
                    data = s.recv(4096)
                    elapsed = _time.time() - t0
                    # 超时后 http.server 直接关连接：要么空包，要么已回错误行
                    self.assertLess(elapsed, 3.0,
                                    f"服务端未在超时上限内回收连接，挂起 {elapsed:.1f}s")
                    self.assertIsInstance(data, bytes)
                except _socket.timeout:
                    self.fail("服务端读线程仍被吊死（timeout 未生效）")
            finally:
                s.close()
        finally:
            server.Handler.timeout = old


if __name__ == "__main__":
    unittest.main(verbosity=2)
