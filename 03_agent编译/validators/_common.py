# -*- coding: utf-8 -*-
"""阶段六 · 共享工具：加载 schema、遍历源条目、谓词编译/求值。
供 build.py 与 validators/ 下四个校验器共用。
"""
import os
import re
import yaml
import glob

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCHEMA_PATH = os.path.join(ROOT, "schema", "entry.yaml")

# ---------------------------------------------------------------------
# 源条目扫描（阶段 A · 2.5a，2026-11-13）：多目录支持
# 从「只扫 书籍E_学科辅导支架」改为「扫 02_内容包/*/ 下全部 .md」，
# 但只收 **源条目**：frontmatter 里含 source_id 的文件。
#
# 为什么要过滤（实测前提，不是猜测）：02_内容包/ 共 5 个目录 81 个 md，
# 其中书籍A/B/C/D 的 63 页 BookStack 正文**同样带 YAML frontmatter**，
# 字段是页面 metadata（面向 / 证据状态 / 书籍 / 章节…），不含 source_id。
# 若按字面 glob 全部收进来，schema_check / source_intake_check /
# template_conformance 会把它们判为缺字段的源条目而全红，manifest 也会
# 覆盖 63 页正文 —— 直接撞「不动 63 页正文」与「13/13 绿」两条边界。
# source_id 本就是 source_intake_check 的既有必填项，把它提到读取层不新增
# 契约约束，只是让「任意 02_内容包/*/ 可扫」与「只编译源条目」同时成立。
#
# 同源纪律：iter_entries() 与 build.py 的 write_manifest / verify_manifest
# 共用同一个 iter_entry_paths()，杜绝「条目进了 chunks 但 manifest 不覆盖」。
# 空目录、无 frontmatter、非源条目一律静默跳过，不报错。
# ---------------------------------------------------------------------
CONTENT_ROOT = os.path.join(ROOT, "02_内容包")
ENTRIES_GLOB = os.path.join(CONTENT_ROOT, "*", "*.md")
GUARDRAIL_PATH = os.path.join(ROOT, "05_审核与运营", "guardrail_rules.yaml")

INT_FIELDS = {"wm_load", "consecutive_failures", "consecutive_successes"}
ENUM_FIELDS = {"task_phase", "attention_state", "ownership"}
CMP_RE = re.compile(r"^(>=|<=|>|<|==|!=)\s*(\d+)$")


def load_schema():
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_guardrail():
    if not os.path.exists(GUARDRAIL_PATH):
        return {"rules": []}
    with open(GUARDRAIL_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_frontmatter(raw):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", raw, re.DOTALL)
    if not m:
        return None
    return yaml.safe_load(m.group(1))


def iter_entry_paths():
    """返回全部源条目路径（排序稳定、跨 02_内容包/*/ 所有书籍目录）。

    判定：文件有合法 YAML frontmatter 且含非空 source_id。
    63 页 BookStack 正文有 frontmatter 但无 source_id，故不进编译管线；
    新增书籍目录只要按 schema 写了 source_id 就会被自动扫到。
    """
    paths = []
    for p in sorted(glob.glob(ENTRIES_GLOB)):
        try:
            with open(p, encoding="utf-8") as f:
                raw = f.read()
        except (OSError, UnicodeDecodeError):
            continue
        fm = parse_frontmatter(raw)
        if isinstance(fm, dict) and fm.get("source_id"):
            paths.append(p)
    return paths


def iter_entries():
    """yield (path, fm, body) for each 源条目 under 02_内容包/*/。

    签名与返回值结构不变：(path, frontmatter_dict, body_string)。
    2.5a 起路径来源统一为 iter_entry_paths()，与 manifest 同源。
    """
    out = []
    for p in iter_entry_paths():
        with open(p, encoding="utf-8") as f:
            raw = f.read()
        fm = parse_frontmatter(raw)
        if fm is None:
            continue
        body = raw.split("---", 2)[2] if raw.count("---") >= 2 else ""
        out.append((p, fm, body))
    return out


def compile_predicate(when):
    """when → 规范化谓词（极小表达式子集）。
    列表值 → op=in（同字段 OR）；字符串 '>=2' → 比较；其余 → ==。"""
    out = {}
    if not when:
        return out
    for field, val in when.items():
        if isinstance(val, list):
            out[field] = {"op": "in", "values": list(val)}
        elif isinstance(val, str) and CMP_RE.match(val):
            op, num = CMP_RE.match(val).groups()
            out[field] = {"op": op, "value": int(num)}
        else:
            out[field] = {"op": "==", "value": val}
    return out


def eval_predicate(pred, state):
    """对给定 state 求值规范谓词。state 必须含谓词所有引用字段。"""
    for field, cond in pred.items():
        if field not in state:
            return False
        sv = state[field]
        op = cond["op"]
        if op == "in":
            if sv not in cond["values"]:
                return False
        else:
            try:
                svi, tv = int(sv), int(cond["value"])
            except Exception:
                return False
            table = {
                "==": svi == tv, "!=": svi != tv, ">": svi > tv,
                "<": svi < tv, ">=": svi >= tv, "<=": svi <= tv,
            }
            if not table[op]:
                return False
    return True
