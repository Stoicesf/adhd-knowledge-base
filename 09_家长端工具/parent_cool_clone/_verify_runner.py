# -*- coding: utf-8 -*-
"""批次 2/3/4 共用：捕获 verify_all.py 输出到 utf-8 文件，避免 PowerShell 管道编码问题。"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SCRIPT = os.path.join(ROOT, "03_agent编译", "verify_all.py")
OUT = os.path.join(HERE, "data", "批次2_verify_all.txt")

env = dict(os.environ)
env["PYTHONIOENCODING"] = "utf-8"
r = subprocess.run([sys.executable, SCRIPT], cwd=ROOT, env=env,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
text = r.stdout.decode("utf-8", errors="replace")
with open(OUT, "w", encoding="utf-8") as f:
    f.write(text + f"\nEXIT={r.returncode}\n")
print(f"EXIT={r.returncode}  output={OUT}")
print("\n".join(text.strip().splitlines()[-12:]))
