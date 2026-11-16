# -*- coding: utf-8 -*-
"""批次 4 手动验收 · 服务在场景：health + POST 火气3 + 真实场景"""
import json
import sys
import urllib.request

BASE = "http://127.0.0.1:8765"

def get(path):
    with urllib.request.urlopen(BASE + path, timeout=5) as r:
        return r.status, json.loads(r.read().decode("utf-8"))

def post(payload):
    req = urllib.request.Request(BASE + "/api/calm_script",
                                 data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status, json.loads(r.read().decode("utf-8"))

s, h = get("/api/health")
print("health:", s, h)
assert s == 200 and h.get("status") == "ok"

s, d = post({"anger_level": 3, "situation": "孩子又摔笔了"})
print("calm_script:", s)
print(json.dumps(d, ensure_ascii=False, indent=2))
assert d["degraded"] is False and d["blocked"] is False
assert d["line"] and d["line"] != "文案待补充（批次 3 派生）"
print("E2E-UP: OK")
sys.exit(0)
