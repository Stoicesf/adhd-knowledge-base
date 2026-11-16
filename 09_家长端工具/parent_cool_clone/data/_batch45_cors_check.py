# -*- coding: utf-8 -*-
"""批次 4.5 curl 等价验收：OPTIONS / GET / POST(Origin: null) 三连，打印原始响应头。"""
import http.client
import json

HOST, PORT = "127.0.0.1", 8765

def show(title, method, path, body=None, headers=None):
    print(f"=== {title} ===")
    c = http.client.HTTPConnection(HOST, PORT, timeout=5)
    c.request(method, path, body=body, headers=headers or {})
    r = c.getresponse()
    raw = r.read().decode("utf-8")
    print(f"{method} {path} -> {r.status} {r.reason}")
    for k, v in r.getheaders():
        if k.lower().startswith(("access-control", "content-type")):
            print(f"  {k}: {v}")
    print("  body:", raw[:300].replace("\n", " | "))
    c.close()
    print()
    return r, raw

r1, _ = show("OPTIONS 预检", "OPTIONS", "/api/calm_script")
assert r1.status == 204
r2, _ = show("GET health", "GET", "/api/health")
assert r2.status == 200
r3, raw3 = show("POST (Origin: null)", "POST", "/api/calm_script",
                body=json.dumps({"anger_level": 3, "situation": "孩子又摔笔了"}),
                headers={"Content-Type": "application/json", "Origin": "null"})
assert r3.status == 200
d = json.loads(raw3)["disclaimer"]
assert r3.getheader("Access-Control-Allow-Origin") == "*"
assert not any(m in d for m in ("批次", "batch", "派生")), d
assert json.loads(raw3)["degraded"] is False and json.loads(raw3)["blocked"] is False
print("ALL CURL-CHECKS OK；disclaimer =", d.replace("\n", " "))
