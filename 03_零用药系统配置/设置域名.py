# -*- coding: utf-8 -*-
"""
设置域名.py —— 把 03_零用药系统配置 下所有文件中的占位域名
https://wiki.example.org 批量替换为真实站点域名。

用法：
  python 设置域名.py --check                       # 只统计将影响的文件数，不改文件
  python 设置域名.py https://wiki.yourdomain.com   # 执行替换

规则：
  - 只处理 .md / .html / .json / .csv；.py 自身与 .bak 不动。
  - 替换前对每个将被修改的文件留一份 <原名>.bak（已存在则不覆盖首份备份）。
  - 新域名必须以 https:// 开头。
  - 幂等：替换完成后再运行一次，应报告 0 处改动。
"""
import os, sys, shutil

BASE = os.path.dirname(os.path.abspath(__file__))
OLD = "https://wiki.example.org"
EXTS = {".md", ".html", ".json", ".csv"}


def collect_files():
    hits = []
    for root, _dirs, files in os.walk(BASE):
        for name in files:
            ext = os.path.splitext(name)[1].lower()
            if ext not in EXTS:
                continue
            if name.endswith(".bak"):
                continue
            hits.append(os.path.join(root, name))
    return hits


def read_text(p):
    if p.lower().endswith(".csv"):
        with open(p, "r", encoding="utf-8-sig") as f:
            return f.read(), "utf-8-sig"
    with open(p, "r", encoding="utf-8") as f:
        return f.read(), "utf-8"


def write_text(p, text, enc):
    with open(p, "w", encoding=enc, newline="") as f:
        f.write(text)


def main():
    args = sys.argv[1:]
    files = collect_files()

    if args and args[0] == "--check":
        n_files, n_hits = 0, 0
        for p in files:
            text, _enc = read_text(p)
            c = text.count(OLD)
            if c > 0:
                n_files += 1
                n_hits += c
                print("将影响: %s （%d 处）" % (os.path.relpath(p, BASE), c))
        print("----")
        print("--check 预览：共 %d 个文件、%d 处将被替换。未做任何修改。" % (n_files, n_hits))
        return

    if not args:
        print("用法: python 设置域名.py --check")
        print("      python 设置域名.py https://你的真实域名")
        sys.exit(1)

    new = args[0].rstrip("/")
    if not new.startswith("https://"):
        print("错误：真实域名必须以 https:// 开头，例如 https://wiki.yourdomain.com")
        sys.exit(1)

    changed_files, changed_hits = 0, 0
    for p in files:
        text, enc = read_text(p)
        c = text.count(OLD)
        if c == 0:
            continue
        bak = p + ".bak"
        if not os.path.exists(bak):
            shutil.copy2(p, bak)
        write_text(p, text.replace(OLD, new), enc)
        changed_files += 1
        changed_hits += c
        print("已改: %s （%d 处，备份: %s）" % (os.path.relpath(p, BASE), c, os.path.basename(bak)))

    print("----")
    print("完成：共修改 %d 个文件、替换 %d 处。" % (changed_files, changed_hits))
    if changed_files == 0:
        print("（幂等确认：没有发现占位域名，无需改动。）")


if __name__ == "__main__":
    main()
