# 批次 6C.2 边界输入实测：起真实服务（随机端口），逐类打边界请求，记录实际行为。
# 只读审计工具，可复跑；不修改任何服务代码。
import http.client
import json
import socket
import sys
import threading
import time

import os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "server")))
import server as srvmod  # noqa: E402

PORT = 18999


def post(body_bytes, cl=None, timeout=3):
    conn = http.client.HTTPConnection("127.0.0.1", PORT, timeout=timeout)
    try:
        headers = {"Content-Type": "application/json"}
        if cl is not None:
            headers["Content-Length"] = str(cl)
        elif body_bytes is not None:
            headers["Content-Length"] = str(len(body_bytes))
        conn.request("POST", "/api/calm_script", body=body_bytes, headers=headers)
        resp = conn.getresponse()
        data = resp.read().decode("utf-8")
        return resp.status, data[:120]
    except (socket.timeout, http.client.HTTPException, OSError) as e:
        return "TIMEOUT/ERR", f"{type(e).__name__}: {e}"[:120]
    finally:
        conn.close()


def case(label, body_bytes, cl=None, timeout=3):
    st, msg = post(body_bytes, cl=cl, timeout=timeout)
    print(f"{label:<38} -> {st}  {msg}")


def raw_case(label, raw_bytes, timeout=3):
    """原始 socket 发包：用于缺 CL 头 / CL 与实际不符的场景。"""
    s = socket.create_connection(("127.0.0.1", PORT), timeout=timeout)
    try:
        s.sendall(raw_bytes)
        s.settimeout(timeout)
        data = s.recv(4096)
        if not data:
            print(f"{label:<38} -> 连接关闭无响应")
            return
        head = data.split(b"\r\n", 1)[0].decode("utf-8", "replace")
        print(f"{label:<38} -> {head[:100]}")
    except (socket.timeout, OSError) as e:
        print(f"{label:<38} -> TIMEOUT/ERR  {type(e).__name__}: {e}"[:120])
    finally:
        s.close()


def main():
    httpd = srvmod.make_server(PORT)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    time.sleep(0.5)
    try:
        ok = json.dumps({"anger_level": 3, "situation": "孩子又摔笔了"}).encode()
        case("正常请求（对照组）", ok)
        case("anger_level=0", json.dumps({"anger_level": 0}).encode())
        case("anger_level=6", json.dumps({"anger_level": 6}).encode())
        case('anger_level="3"（字符串）', b'{"anger_level": "3"}')
        case("anger_level=null", b'{"anger_level": null}')
        case("situation=100KB 字符串",
             json.dumps({"anger_level": 3, "situation": "摔" * 102400}).encode(),
             timeout=5)
        case("situation=数字（非字符串）", b'{"anger_level": 3, "situation": 123}')
        case("situation=对象（非字符串）", b'{"anger_level": 3, "situation": {"a": 1}}')
        case("body 无效 JSON", b"this is not json{{{")
        case("body 空字节流", b"")
        raw_case("缺 Content-Length 头（带 body）",
                 b"POST /api/calm_script HTTP/1.1\r\nHost: 127.0.0.1\r\n"
                 b"Content-Type: application/json\r\n\r\n"
                 b'{"anger_level": 3}')
        raw_case("CL 声明 1MB+1 只发 10 字节",
                 b"POST /api/calm_script HTTP/1.1\r\nHost: 127.0.0.1\r\n"
                 b"Content-Type: application/json\r\nContent-Length: 1048577\r\n\r\n"
                 b'{"anger_l')
    finally:
        httpd.shutdown()
        httpd.server_close()
    print("probe done")


if __name__ == "__main__":
    main()
