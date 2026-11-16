# -*- coding: utf-8 -*-
"""独立进程起真实 server.py + HTTP 实测，全部在一个脚本内自清理。"""
import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 18767
srv = os.path.join(HERE, "server.py")
p = subprocess.Popen([sys.executable, srv, "--port", str(PORT)],
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
lines = []
try:
    # 轮询等待端口就绪，最多 8 秒
    ready = False
    for _ in range(40):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/health", timeout=1) as r:
                h = json.loads(r.read().decode("utf-8"))
                if r.status == 200 and h.get("status") == "ok":
                    ready = True
                    lines.append(f"GET /api/health -> 200 {json.dumps(h, ensure_ascii=False)}")
                    break
        except Exception:
            time.sleep(0.2)
    if not ready:
        lines.append("FAIL: /api/health 未就绪")
    else:
        req = urllib.request.Request(
            f"http://127.0.0.1:{PORT}/api/calm_script",
            data=json.dumps({"anger_level": 5, "situation": "错题又错了"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=3) as r:
            b = json.loads(r.read().decode("utf-8"))
            lines.append(f"POST /api/calm_script -> 200 degraded={b['degraded']} "
                         f"blocked={b['blocked']} level={b['level']} steps={len(b['steps'])}")
            lines.append(f"line = {b['line']}")
    lines.append(f"RESULT={'OK' if ready else 'FAIL'}")
finally:
    p.terminate()
    try:
        p.wait(timeout=3)
    except subprocess.TimeoutExpired:
        p.kill()
    lines.append("server stopped (no orphan process)")

out = os.path.join(HERE, "..", "data", "批次2_服务实测.md")
with open(out, "w", encoding="utf-8") as f:
    f.write("# 阶段 B 批次 2 · 独立进程服务实测\n\n")
    f.write("命令：`python server.py --port 18767`，真实独立进程；结束后 terminate 自清理。\n\n")
    f.write("\n".join("- " + l for l in lines) + "\n")
print("\n".join(lines))
