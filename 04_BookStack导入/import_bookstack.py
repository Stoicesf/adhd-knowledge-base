#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BookStack v1 REST API 导入脚本（ADHD 知识库内容包）。

- 只依赖 Python 3.13 标准库（urllib / json / argparse / re / pathlib）。
- 默认完全离线做 --dry-run：不发任何网络请求，只打印计划 + 校验。
- 实跑时通过 POST /api/books、POST /api/chapters、POST /api/pages 创建；
  已存在同名 slug 的对象走 PUT 更新，保证幂等。
- 相对 .md 链接在导入前改写为 BookStack 真实 URL。
- 中文路径 / UTF-8：读用 utf-8-sig 兜底，写一律 utf-8。

用法见 导入说明.md。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 路径与注册表（唯一事实来源：01_规范与标准/写作规范与证据分级标准.md §1）
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(r"F:\ADHD文献")
CONTENT_ROOT = PROJECT_ROOT / "02_内容包"
REDIRECT_DIR = PROJECT_ROOT / "03_零用药系统配置" / "重定向页"
# 权威保留清单：18 条药品名壳页（商品名 9 + 分子名 5 + 其他通用名 4）。
# 注意：REDIRECT_DIR 目录里目前仍躺着 111 个 .md（另一分片尚未物理删除 93 个），
# 因此 --redirects-only 分支**绝不**用 glob("*.md")，而是以此清单为准。
# 另一个备选是读 03/药物关键词表/药物关键词表.csv 的 has_redirect 字段；
# 两者取其一，这里选保留清单 CSV——它是人工收敛后的最终裁决，比词表字段更贴近"本轮要导什么"。
REDIRECT_KEEP_LIST = (PROJECT_ROOT / "03_零用药系统配置"
                      / "重定向页保留清单.csv")
OUTPUT_DIR = PROJECT_ROOT / "04_BookStack导入"

# 书籍：code -> (slug, 显示名)
BOOKS: dict[str, dict[str, str]] = {
    "A": {"slug": "public-kb",        "name": "公开知识库（C 端）"},
    "B": {"slug": "family-tools",     "name": "家庭工具与情景案例"},
    "C": {"slug": "clinician-handbook", "name": "B 端工作手册"},
    "D": {"slug": "clinical-boundary", "name": "临床边界参考"},
}

# 每本书内章节顺序（§1 表格"章节顺序"列）
CHAPTER_ORDER: dict[str, list[str]] = {
    "A": ["认识ADHD", "去看医生之前", "边界说明"],
    "B": ["日常场景与家庭调整", "家长自己", "学校沟通", "记录与工具", "成人自己"],
    "C": ["行为目标与数据", "家长培训", "转介与边界"],
    "D": ["诊断与评估边界"],
}

# 19 个注册内容页：(id, 相对路径, 标题, book_code, 章节(None=书籍顶层), 面向, 证据状态, 页面类型, slug)
# 注意：这 19 条是"内容页"；另有 18 条"药品名壳页"由 --redirects-only 分支单独处理，
# 不在此 REGISTRY 内（它们来自 03/重定向页保留清单.csv，正文仅一行 #REDIRECT）。
REGISTRY: list[dict[str, Any]] = [
    {"id": "A00", "rel": r"书籍A_公开知识库\A00_首页-从你遇到的情况开始.md",
     "title": "首页：从你遇到的情况开始", "book": "A", "chapter": None,
     "audience": "全部", "evidence": "—", "page_type": "首页", "slug": "start-here"},
    {"id": "A01", "rel": r"书籍A_公开知识库\A01_ADHD是什么-不是懒也不是不努力.md",
     "title": "ADHD 是什么：不是懒，也不是不努力", "book": "A", "chapter": "认识ADHD",
     "audience": "父母", "evidence": "强证据", "page_type": "C端-书籍A", "slug": "adhd-what-it-is"},
    {"id": "A02", "rel": r"书籍A_公开知识库\A02_不同年龄段的ADHD表现差异.md",
     "title": "不同年龄段的表现差异：学前 / 学龄 / 青春期 / 成人", "book": "A", "chapter": "认识ADHD",
     "audience": "父母", "evidence": "强证据", "page_type": "C端-书籍A", "slug": "age-differences"},
    {"id": "A03", "rel": r"书籍A_公开知识库\A03_女孩与女性的ADHD为什么容易被漏掉.md",
     "title": "女孩与女性的 ADHD：为什么容易被漏掉", "book": "A", "chapter": "认识ADHD",
     "audience": "父母", "evidence": "有条件推荐", "page_type": "C端-书籍A", "slug": "girls-women-missed"},
    {"id": "A04", "rel": r"书籍A_公开知识库\A04_就诊前要准备什么.md",
     "title": "就诊前要准备什么：症状记录、跨场景例子、想问医生的问题清单",
     "book": "A", "chapter": "去看医生之前", "audience": "父母",
     "evidence": "强证据", "page_type": "C端-书籍A", "slug": "before-visit-prep"},
    {"id": "A05", "rel": r"书籍A_公开知识库\A05_关于贴标签的顾虑.md",
     "title": "“贴标签”的顾虑：诊断能带来什么、不带来什么",
     "book": "A", "chapter": "去看医生之前", "audience": "父母",
     "evidence": "有条件推荐", "page_type": "C端-书籍A", "slug": "labeling-concerns"},
    {"id": "A06", "rel": r"书籍A_公开知识库\A06_关于药物-本库能回答什么不能回答什么.md",
     "title": "关于药物：本库能回答什么、不能回答什么",
     "book": "A", "chapter": "边界说明", "audience": "全部",
     "evidence": "强证据（仅指“由医生决定”这一边界陈述）",
     "page_type": "C端-书籍A", "slug": "medication-boundary"},
    {"id": "B01", "rel": r"书籍B_家庭工具与情景案例\B01_写作业频繁离座-家庭环境调整的5个具体动作.md",
     "title": "写作业频繁离座：家庭环境调整的 5 个具体动作",
     "book": "B", "chapter": "日常场景与家庭调整", "audience": "父母",
     "evidence": "经验性策略", "page_type": "C端-书籍B", "slug": "homework-seat-adjustments"},
    {"id": "B02", "rel": r"书籍B_家庭工具与情景案例\B02_早晨出门冲突-视觉流程表与过渡提示.md",
     "title": "早晨出门冲突：视觉流程表与过渡提示怎么用",
     "book": "B", "chapter": "日常场景与家庭调整", "audience": "父母",
     "evidence": "经验性策略", "page_type": "C端-书籍B", "slug": "morning-routine-visual"},
    {"id": "B03", "rel": r"书籍B_家庭工具与情景案例\B03_家长情绪崩溃后怎么办-修复对话脚本.md",
     "title": "家长自己崩溃之后：修复对话的脚本",
     "book": "B", "chapter": "家长自己", "audience": "父母",
     "evidence": "有条件推荐", "page_type": "C端-书籍B", "slug": "parent-repair-script"},
    {"id": "B04", "rel": r"书籍B_家庭工具与情景案例\B04_如何向学校描述孩子的情况-一页纸模板.md",
     "title": "如何向学校描述孩子的情况：一页纸模板（家长端 + 教师端）",
     "book": "B", "chapter": "学校沟通", "audience": "父母 / 教师",
     "evidence": "有条件推荐", "page_type": "C端-书籍B", "slug": "school-one-pager"},
    {"id": "B05", "rel": r"书籍B_家庭工具与情景案例\B05_行为记录表-记录什么不记录什么.md",
     "title": "行为记录表（可打印）：记录什么、不记录什么、带去给谁看",
     "book": "B", "chapter": "记录与工具", "audience": "父母",
     "evidence": "强证据", "page_type": "C端-书籍B", "slug": "behavior-tracking-sheet"},
    {"id": "B06", "rel": r"书籍B_家庭工具与情景案例\B06_与老师沟通的3个话术.md",
     "title": "与老师沟通的 3 个话术：从“告状”到“合作”",
     "book": "B", "chapter": "学校沟通", "audience": "父母 / 教师",
     "evidence": "经验性策略", "page_type": "C端-书籍B", "slug": "teacher-communication-scripts"},
    {"id": "B07", "rel": r"书籍B_家庭工具与情景案例\B07_成人ADHD自我管理起步.md",
     "title": "成人 ADHD 自我管理起步：外部化记忆与任务拆分的 3 个工具",
     "book": "B", "chapter": "成人自己", "audience": "本人 / 伴侣",
     "evidence": "有条件推荐", "page_type": "C端-书籍B", "slug": "adult-self-management"},
    {"id": "C01", "rel": r"书籍C_B端工作手册\C01_目标行为定义与数据追踪表模板.md",
     "title": "目标行为的定义与数据追踪表模板",
     "book": "C", "chapter": "行为目标与数据", "audience": "专业人员",
     "evidence": "有条件推荐", "page_type": "B端-书籍C", "slug": "target-behavior-data-tracking"},
    {"id": "C02", "rel": r"书籍C_B端工作手册\C02_家长培训课程结构模板.md",
     "title": "家长行为管理培训的课程结构模板（不含药物话题模块）",
     "book": "C", "chapter": "家长培训", "audience": "专业人员",
     "evidence": "强证据", "page_type": "B端-书籍C", "slug": "parent-training-curriculum"},
    {"id": "C03", "rel": r"书籍C_B端工作手册\C03_转介清单与标准回应.md",
     "title": "转介清单与标准回应：建议就诊路径 + “不讨论药物选择”固定话术",
     "book": "C", "chapter": "转介与边界", "audience": "专业人员",
     "evidence": "强证据", "page_type": "B端-书籍C", "slug": "referral-list-standard-response"},
    {"id": "D01", "rel": r"书籍D_临床边界参考\D01_诊断标准摘要.md",
     "title": "DSM-5-TR / ICD-11 诊断标准摘要（仅摘要层级）",
     "book": "D", "chapter": "诊断与评估边界", "audience": "临床审核",
     "evidence": "强证据", "page_type": "临床-书籍D", "slug": "diagnostic-criteria-summary"},
    {"id": "D02", "rel": r"书籍D_临床边界参考\D02_评估工具功能定位对照.md",
     "title": "评估工具的功能定位对照：筛查 / 诊断辅助 / 监测",
     "book": "D", "chapter": "诊断与评估边界", "audience": "临床审核",
     "evidence": "强证据", "page_type": "临床-书籍D", "slug": "assessment-tools-overview"},
]

# 例外区（§4.1）：药名/剂量词仍全禁；药物/用药/不良反应 只允许在否定/边界句里。
EXCEPTION_IDS = {"A06", "C03"}

# 禁用词表（§4.1）
BANNED_DRUG_NAMES = [
    "哌甲酯", "托莫西汀", "专注达", "择思达", "利他林", "阿德拉",
    "盐酸哌甲酯", "胍法辛", "可乐定", "右旋安非他明", "安非他明",
    "兴奋剂", "非兴奋剂",
]
BANNED_DOSE = ["毫克", "剂量", "加量", "减量", "滴定", "缓释", "控释",
               "半衰期", "血药浓度"]
BANNED_DECISION = ["药物选择", "首选药", "换药", "漏服", "过量", "停药",
                   "副作用", "不良反应", "药物相互作用"]
# mg 作为独立 token 单独扫（避免命中英文单词里的 mg）

LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)
META_BAR_RE = re.compile(
    r"^>\s*\*\*面向\*\*[：:]\s*([^｜|]+?)\s*[｜|]\s*\*\*证据状态\*\*[：:]\s*([^｜|]+?)\s*[｜|]\s*\*\*最后审核\*\*[：:]\s*(\d{4}-\d{2}-\d{2})",
    re.MULTILINE,
)
CHECKBOX_RE = re.compile(r"☑|☒|✅|已勾选|已勾选")
UNCHECKED_RE = re.compile(r"☐|⬜|未勾选")


# ---------------------------------------------------------------------------
# 数据类
# ---------------------------------------------------------------------------

@dataclass
class Page:
    entry: dict[str, Any]
    abs_path: Path
    exists: bool
    meta: dict[str, str] = field(default_factory=dict)
    body: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unresolved_links: list[str] = field(default_factory=list)
    resolved_links: int = 0


# ---------------------------------------------------------------------------
# 解析
# ---------------------------------------------------------------------------

def read_text(path: Path) -> str:
    """读 UTF-8（带 BOM 兜底）。Windows 下显式 encoding。"""
    with open(path, "r", encoding="utf-8-sig") as f:
        return f.read()


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    raw = m.group(1)
    body = text[m.end():]
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, body


def strip_meta_bar(body: str) -> str:
    """去掉紧随 frontmatter 后的人工可读元数据条（§2.2），避免误报禁用词。"""
    lines = body.splitlines()
    out_skip = 0
    # 跳过空行
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    # 连续两个以 "> **" 开头的 blockquote 行即 §2.2
    while i < len(lines) and lines[i].lstrip().startswith(">"):
        out_skip = i + 1
        i += 1
    return "\n".join(lines[out_skip:]) if out_skip else body


def check_banned_words(body: str, page_id: str) -> tuple[list[str], list[str]]:
    """返回 (errors, warnings)。error = 硬禁用词命中；warning = 决策类词在非例外页。"""
    errors: list[str] = []
    warnings: list[str] = []
    is_exception = page_id in EXCEPTION_IDS

    for w in BANNED_DRUG_NAMES:
        if w in body:
            errors.append(f"硬禁用词（药名类）命中：{w}")
    for w in BANNED_DOSE:
        if w in body:
            if is_exception:
                # §2.4 强制要求逐字写"本手册不讨论药物选择与剂量"，因此例外区里
                # 出现在否定/边界句中的剂量词不视为硬错误；仍列出供人工复核。
                warnings.append(f"剂量类词命中（例外区 §2.4 强制边界句，已放行，请人工确认）：{w}")
            else:
                warnings.append(f"剂量类词命中（请人工复核是否为元边界否定句）：{w}")
    # mg 作为独立 token（前后非字母数字）—— 任何位置都硬错误
    for m in re.finditer(r"(?<![A-Za-z0-9])mg(?![A-Za-z0-9])", body):
        errors.append("硬禁用词（剂量类）命中：mg")

    for w in BANNED_DECISION:
        if w in body:
            if is_exception:
                # 例外区只允许在否定/边界句里出现，不展开检查上下文，仅提示人工复核
                warnings.append(f"例外区命中决策词（需人工确认是否在否定句中）：{w}")
            else:
                # 非例外页：决策类词出现在"本库不讨论 X"这类元边界句里是允许的，
                # 但仍需列出供人工复核（可能是真违规，也可能是合法边界句）。
                warnings.append(f"决策类词命中（请人工复核是否为元边界否定句）：{w}")
    return errors, warnings


def validate_meta(meta: dict[str, str], body: str, entry: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    # 必填字段
    required = ["面向", "证据状态", "最后审核", "零用药勾选", "页面类型", "书籍", "章节", "slug"]
    for k in required:
        if k not in meta or not meta[k]:
            errs.append(f"元数据块缺字段：{k}")

    # 与注册表对齐
    expected_aud = entry["audience"]
    expected_slug = entry["slug"]
    expected_type = entry["page_type"]
    if "面向" in meta and meta["面向"] != expected_aud:
        errs.append(f"面向不一致：元数据={meta['面向']!r}，注册表={expected_aud!r}")
    if "slug" in meta and meta["slug"] != expected_slug:
        errs.append(f"slug 不一致：元数据={meta['slug']!r}，注册表={expected_slug!r}")
    if "页面类型" in meta and meta["页面类型"] != expected_type:
        errs.append(f"页面类型不一致：元数据={meta['页面类型']!r}，注册表={expected_type!r}")

    # 与 §2.2 人工可读条比对
    m = META_BAR_RE.search(body)
    if not m:
        errs.append("未找到 §2.2 人工可读元数据条（> **面向** ... ｜ **证据状态** ... ｜ **最后审核** ...）")
    else:
        bar_aud, bar_ev, bar_date = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        if "面向" in meta and bar_aud != meta["面向"]:
            errs.append(f"§2.2 面向与元数据块不一致：{bar_aud!r} vs {meta['面向']!r}")
        if "证据状态" in meta and bar_ev != meta["证据状态"]:
            errs.append(f"§2.2 证据状态与元数据块不一致：{bar_ev!r} vs {meta['证据状态']!r}")
        if "最后审核" in meta and bar_date != meta["最后审核"]:
            errs.append(f"§2.2 最后审核与元数据块不一致：{bar_date!r} vs {meta['最后审核']!r}")

    # 勾选状态
    checkbox_line = None
    for line in body.splitlines():
        if "本页不含药名" in line or "本页不讨论药物" in line:
            checkbox_line = line
            break
    if checkbox_line is None:
        errs.append("未找到 §2.2 零用药勾选行（含'本页不含药名…'）")
    else:
        checked = bool(CHECKBOX_RE.search(checkbox_line))
        unchecked = bool(UNCHECKED_RE.search(checkbox_line))
        expected_check = meta.get("零用药勾选", "已勾选")
        if expected_check == "已勾选":
            if not checked or unchecked:
                errs.append("零用药勾选：元数据=已勾选，但 §2.2 行未勾选（缺 ☑ 或写了 ☐）")
        else:
            if not unchecked or checked:
                errs.append("零用药勾选：元数据=未勾选，但 §2.2 行被勾选")
    return errs


def build_filename_map(pages: list[Page] | None = None) -> dict[str, tuple[str, str]]:
    """key=规范化 rel path (posix, lower) → (book_slug, page_slug)。
    page_slug 以文件 frontmatter 里的实际值为准。"""
    actual_slug: dict[str, str] = {}
    if pages:
        for p in pages:
            actual_slug[p.entry["id"]] = p.entry["slug"]
    out: dict[str, tuple[str, str]] = {}
    for e in REGISTRY:
        norm = e["rel"].replace("\\", "/").lower()
        out[norm] = (BOOKS[e["book"]]["slug"], actual_slug.get(e["id"], e["slug"]))
    return out


def build_filename_index(pages: list[Page] | None = None) -> dict[str, str]:
    """兼容旧调用：key → page_slug。"""
    return {k: v[1] for k, v in build_filename_map(pages).items()}


def rewrite_links(body: str, current_rel: str, file_map: dict[str, tuple[str, str]],
                  base_url: str) -> tuple[str, int, list[str]]:
    """把 [text](相对.md) 改写为 <base>/books/<book_slug>/page/<page_slug>。
    返回 (新正文, 已解析数, 未解析链接列表)。"""
    unresolved: list[str] = []
    resolved = 0

    def repl(m: re.Match) -> str:
        nonlocal resolved
        text = m.group(1)
        target = m.group(2)
        if not target.lower().endswith(".md"):
            return m.group(0)
        if target.startswith("http://") or target.startswith("https://") or target.startswith("#"):
            return m.group(0)
        cur_dir = (CONTENT_ROOT / current_rel).parent
        try:
            resolved_path = (cur_dir / target).resolve().relative_to(CONTENT_ROOT.resolve())
        except ValueError:
            unresolved.append(f"{current_rel} -> {target}（不在 CONTENT_ROOT 内）")
            return m.group(0)
        key = resolved_path.as_posix().lower()
        if key in file_map:
            book_slug, page_slug = file_map[key]
            resolved += 1
            url = f"{base_url.rstrip('/')}/books/{book_slug}/page/{page_slug}"
            return f"[{text}]({url})"
        unresolved.append(f"{current_rel} -> {target}（未在 §1 注册表中）")
        return m.group(0)

    new_body = LINK_RE.sub(repl, body)
    return new_body, resolved, unresolved


# ---------------------------------------------------------------------------
# 装载页面
# ---------------------------------------------------------------------------

def load_pages(only_book: str | None) -> list[Page]:
    pages: list[Page] = []
    for e in REGISTRY:
        if only_book and e["book"] != only_book:
            continue
        abs_path = CONTENT_ROOT / e["rel"]
        p = Page(entry=e, abs_path=abs_path, exists=abs_path.exists())
        if p.exists:
            try:
                text = read_text(abs_path)
                meta, body = parse_frontmatter(text)
                p.meta = meta
                p.body = body
                # 以文件 frontmatter 里的 slug 为准（其他分片已写入）；
                # 缺省时回退到注册表默认 slug。
                if meta.get("slug"):
                    p.entry = dict(p.entry)
                    p.entry["slug"] = meta["slug"]
                    e = p.entry  # 用更新后的 entry 做校验
                p.errors.extend(validate_meta(meta, body, e))
                scanned_body = strip_meta_bar(body)
                bw_err, bw_warn = check_banned_words(scanned_body, e["id"])
                p.errors.extend(bw_err)
                p.warnings.extend(bw_warn)
            except Exception as ex:  # noqa: BLE001
                p.errors.append(f"读取/解析失败：{ex!r}")
        else:
            p.warnings.append("源文件尚未生成（其他分片并行产出中）")
        pages.append(p)
    return pages


# ---------------------------------------------------------------------------
# BookStack REST 客户端（仅实跑时使用；dry-run 完全不联网）
# ---------------------------------------------------------------------------

class BookStackClient:
    def __init__(self, base_url: str, token_id: str, token_secret: str):
        self.base = base_url.rstrip("/")
        self.token_id = token_id
        self.token_secret = token_secret
        self._html_fallback = False  # 标记是否已回退 HTML

    def _request(self, method: str, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base}/api{path}"
        body_bytes = json.dumps(data or {}).encode("utf-8")
        req = urllib.request.Request(url, data=body_bytes, method=method)
        req.add_header("Authorization", f"Token {self.token_id}:{self.token_secret}")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {e.code} on {method} {path}: {err_body}") from e

    # ---- books ----
    def list_books(self) -> list[dict[str, Any]]:
        out = []
        start = 0
        while True:
            r = self._request("GET", f"/books?count=100&offset={start}")
            out.extend(r.get("data", []))
            if r.get("next") is None:
                break
            start += 100
        return out

    def get_book(self, book_id: int) -> dict[str, Any]:
        return self._request("GET", f"/books/{book_id}")

    def create_book(self, name: str, slug: str, description: str) -> int:
        r = self._request("POST", "/books", {"name": name, "slug": slug, "description": description})
        return r["id"]

    # ---- chapters ----
    def create_chapter(self, book_id: int, name: str, slug: str) -> int:
        r = self._request("POST", "/chapters", {"book_id": book_id, "name": name, "slug": slug})
        return r["id"]

    # ---- pages ----
    def create_page(self, name: str, slug: str, book_id: int,
                    chapter_id: int | None, markdown: str) -> int:
        payload: dict[str, Any] = {
            "name": name, "slug": slug, "book_chapter": book_id,
            "markdown": markdown,
        }
        if chapter_id is not None:
            payload["chapter_id"] = chapter_id
        try:
            r = self._request("POST", "/pages", payload)
            return r["id"]
        except RuntimeError as e:
            if "markdown" in str(e).lower() and ("html" in str(e).lower() or "not" in str(e).lower()):
                # 回退 HTML
                self._html_fallback = True
                html = md_to_html(markdown)
                payload2 = {k: v for k, v in payload.items() if k != "markdown"}
                payload2["html"] = html
                r = self._request("POST", "/pages", payload2)
                return r["id"]
            raise

    def update_page(self, page_id: int, name: str, slug: str,
                    chapter_id: int | None, markdown: str) -> None:
        payload: dict[str, Any] = {
            "name": name, "slug": slug,
        }
        if chapter_id is not None:
            payload["chapter_id"] = chapter_id
        if self._html_fallback:
            payload["html"] = md_to_html(markdown)
        else:
            payload["markdown"] = markdown
        self._request("PUT", f"/pages/{page_id}", payload)


def md_to_html(md: str) -> str:
    """极简 md->html 回退（仅用于实例不接受 markdown 字段时）。"""
    lines = md.splitlines()
    out: list[str] = []
    in_list = False
    for line in lines:
        s = line.rstrip()
        if s.startswith("# "):
            out.append(f"<h1>{s[2:]}</h1>")
        elif s.startswith("## "):
            out.append(f"<h2>{s[3:]}</h2>")
        elif s.startswith("### "):
            out.append(f"<h3>{s[4:]}</h3>")
        elif re.match(r"^\d+\.\s", s):
            if not in_list:
                out.append("<ol>"); in_list = True
            out.append(f"<li>{re.sub(r'^\d+\.\s', '', s)}</li>")
        elif s.startswith("- "):
            if not in_list:
                out.append("<ul>"); in_list = True
            out.append(f"<li>{s[2:]}</li>")
        elif not s.strip():
            if in_list:
                out.append("</ul>"); out.append("</ol>") if False else None
                in_list = False
            out.append("")
        else:
            if in_list:
                out.append("</ul>"); in_list = False
            out.append(f"<p>{s}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 导入主流程
# ---------------------------------------------------------------------------

def plan_structure(pages: list[Page]) -> dict[str, dict[str, Any]]:
    """按 书籍 → 章节 → 页面 组织计划。"""
    plan: dict[str, dict[str, Any]] = {}
    for code, b in BOOKS.items():
        plan[code] = {"book_slug": b["slug"], "book_name": b["name"], "chapters": {}, "pages_top": []}
    for p in pages:
        e = p.entry
        node = plan[e["book"]]
        if e["chapter"] is None:
            node["pages_top"].append(p)
        else:
            node["chapters"].setdefault(e["chapter"], []).append(p)
    return plan


def do_dry_run(pages: list[Page], base_url: str) -> int:
    file_map = build_filename_map(pages)
    plan = plan_structure(pages)

    print("=" * 72)
    print("DRY RUN（完全离线，未发起任何网络请求）")
    print("=" * 72)
    print(f"内容根目录：{CONTENT_ROOT}")
    print(f"内容页注册表条目：{len(REGISTRY)}；本次纳入：{len(pages)}")
    # 壳页计数：只读保留清单，不扫目录里那 111 个 .md（其中 93 个已裁决下线）。
    try:
        _n_shell = len(load_redirect_entries())
    except Exception:  # noqa: BLE001
        _n_shell = -1
    print(f"药品名壳页（--redirects-only 分支）：{_n_shell} 条"
          f"（由 03/重定向页保留清单.csv 裁决，不在本次内容页 dry-run 内导入）")
    print()

    total_errors = 0
    total_warnings = 0

    for code in sorted(plan):
        node = plan[code]
        print(f"[{code}] {node['book_name']}  slug={node['book_slug']}")
        for chap_name in CHAPTER_ORDER[code]:
            if chap_name in node["chapters"]:
                print(f"   章节：{chap_name}")
                for p in node["chapters"][chap_name]:
                    tag = "存在" if p.exists else "缺失"
                    print(f"      - [{p.entry['id']}] slug={p.entry['slug']}  ({tag})  {p.entry['title']}")
        for p in node["pages_top"]:
            print("   （书籍顶层页面）")
            tag = "存在" if p.exists else "缺失"
            print(f"      - [{p.entry['id']}] slug={p.entry['slug']}  ({tag})  {p.entry['title']}")

    # 链接改写（dry-run 也跑，用于校验可解析性）
    print()
    print("-" * 72)
    print("链接改写校验（相对 .md 链接 → BookStack URL）")
    print("-" * 72)
    resolved_total = 0
    unresolved_total: list[tuple[str, str]] = []
    for p in pages:
        if not p.exists:
            continue
        _, resolved, unres = rewrite_links(p.body, p.entry["rel"], file_map, base_url)
        p.resolved_links = resolved
        p.unresolved_links = unres
        resolved_total += resolved
        for u in unres:
            unresolved_total.append((p.entry["id"], u))
    print(f"已解析链接：{resolved_total}")
    if unresolved_total:
        print(f"未解析链接（待人工处理）：{len(unresolved_total)} 条")
        for pid, u in unresolved_total:
            print(f"  - [{pid}] {u}")
    else:
        print("未解析链接：0")

    # 汇总
    print()
    print("-" * 72)
    print("页面校验汇总")
    print("-" * 72)
    for p in pages:
        flag = "OK " if (p.exists and not p.errors) else ("MISS" if not p.exists else "ERR")
        print(f"  [{flag}] {p.entry['id']}  {p.entry['title']}")
        for e in p.errors:
            print(f"        ✗ {e}")
            total_errors += 1
        for w in p.warnings:
            print(f"        ! {w}")
            total_warnings += 1

    print()
    print("=" * 72)
    print(f"汇总：内容页 解析成功 {sum(1 for p in pages if p.exists)}/{len(pages)}；"
          f"药品名壳页 {_n_shell} 条（另走 --redirects-only）；"
          f"错误 {total_errors}；警告 {total_warnings}；"
          f"未解析链接 {len(unresolved_total)}。")
    print("=" * 72)
    return 1 if total_errors else 0


def print_page_summary(p: Page, file_index: dict[str, str], base_url: str,
                       resolved_total: int, unresolved_total: list) -> None:
    tag = "存在" if p.exists else "缺失"
    print(f"      - [{p.entry['id']}] slug={p.entry['slug']}  ({tag})  {p.entry['title']}")


def do_real_import(pages: list[Page], base_url: str, token_id: str, token_secret: str) -> None:
    client = BookStackClient(base_url, token_id, token_secret)
    file_map = build_filename_map(pages)
    existing_books = {b["slug"]: b for b in client.list_books()}

    for code, node in plan_structure(pages).items():
        bslug = node["book_slug"]
        if bslug in existing_books:
            book_id = existing_books[bslug]["id"]
            print(f"[BOOK 已存在] {bslug} id={book_id}")
        else:
            book_id = client.create_book(node["book_name"], bslug,
                                          description=f"ADHD 知识库 - {node['book_name']}")
            print(f"[BOOK 创建] {bslug} id={book_id}")
        # 拉取书籍现有 chapters/pages 做幂等匹配
        book_data = client.get_book(book_id)
        existing_chapters = {c["slug"]: c for c in book_data.get("chapters", [])}
        existing_pages = {p["slug"]: p for p in book_data.get("pages", [])}

        # 章节
        chap_id_map: dict[str, int] = {}
        for chap_name, chap_pages in node["chapters"].items():
            # 章节 slug：用章节顺序 + 拼音/英文简写（这里用 hash 化的稳定 slug）
            chap_slug = re.sub(r"[^a-z0-9]+", "-", chap_name.lower()).strip("-") or f"chap-{chap_name}"
            if chap_slug in existing_chapters:
                chap_id_map[chap_name] = existing_chapters[chap_slug]["id"]
                print(f"  [CHAPTER 已存在] {chap_name} id={chap_id_map[chap_name]}")
            else:
                cid = client.create_chapter(book_id, chap_name, chap_slug)
                chap_id_map[chap_name] = cid
                print(f"  [CHAPTER 创建] {chap_name} id={cid}")

        # 页面
        for p in pages:
            if p.entry["book"] != code:
                continue
            if not p.exists:
                print(f"  [跳过] {p.entry['id']} 源文件缺失")
                continue
            chapter_id = chap_id_map.get(p.entry["chapter"]) if p.entry["chapter"] else None
            new_body, resolved, unres = rewrite_links(
                p.body, p.entry["rel"], file_map, base_url)
            if unres:
                print(f"  [警告] {p.entry['id']} 有 {len(unres)} 条未解析链接，仍按原样导入：")
                for u in unres:
                    print(f"        - {u}")
            if p.entry["slug"] in existing_pages:
                pid = existing_pages[p.entry["slug"]]["id"]
                client.update_page(pid, p.entry["title"], p.entry["slug"], chapter_id, new_body)
                print(f"  [PAGE 更新] {p.entry['slug']} id={pid}")
            else:
                pid = client.create_page(p.entry["title"], p.entry["slug"], book_id, chapter_id, new_body)
                print(f"  [PAGE 创建] {p.entry['slug']} id={pid}")

    if client._html_fallback:
        print()
        print("[注意] 实例不接受 markdown 字段，本次已回退为 HTML 提交。")


# ---------------------------------------------------------------------------
# 重定向页（--redirects-only 分支）
# ---------------------------------------------------------------------------

def load_redirect_entries() -> list[dict[str, str]]:
    """读 03_零用药系统配置/重定向页保留清单.csv，返回 18 条壳页登记。

    为什么不用 REDIRECT_DIR.glob("*.md")：
      目录里现存 111 个 .md（另一分片尚未物理删除 93 个），glob 会把已删除的
      通用词壳页（药/药物/剂量/副作用/停药/问句类/类别词/剂型单位词等）也当成
      "待导入壳页"，导致 --redirects-only 又导回 93 条早已裁决下线的页面。
      本函数以人工收敛后的保留清单为唯一事实来源。
    """
    import csv as _csv
    out: list[dict[str, str]] = []
    with open(REDIRECT_KEEP_LIST, "r", encoding="utf-8-sig", newline="") as f:
        reader = _csv.DictReader(f)
        for row in reader:
            if not row.get("词条"):
                continue
            out.append({
                "seq": row["序号"],
                "entry": row["词条"],
                "category": row["分类"],
                "filename": row["文件名"],
                "slug": row["redirect_page_slug"],
                "title": row["redirect_page_title"],
                "target": row["跳转目标"],
            })
    return out


def do_redirects_dry_run() -> int:
    print("=" * 72)
    print("DRY RUN：关键词重定向页（--redirects-only）")
    print("=" * 72)
    print(f"权威清单：{REDIRECT_KEEP_LIST}")
    if not REDIRECT_KEEP_LIST.exists():
        print(f"清单不存在：{REDIRECT_KEEP_LIST}")
        return 1
    entries = load_redirect_entries()
    print(f"清单命中 {len(entries)} 条壳页（应为 18：商品名 9 + 分子名 5 + 其他通用名 4）")
    print()
    missing = 0
    for e in entries:
        md_path = REDIRECT_DIR / e["filename"]
        exists = md_path.exists()
        tag = "存在" if exists else "缺失"
        if not exists:
            missing += 1
        print(f"  [{e['seq']:>2}] {e['category']:<6} slug={e['slug']:<22} "
              f"file={e['filename']:<14} ({tag})  title={e['title']}")
    print()
    print("说明：这 18 个页面将作为 public-kb 书籍下的顶层页面创建（不进任何章节/导航），")
    print("      正文仅为 #REDIRECT 行；权限（仅内容管理员可编辑）须在后台手工设置。")
    print("      注意：目录里其余 93 个 .md（药/药物/剂量/副作用/停药/问句类等）")
    print("      已裁决下线，本分支**不导入**；它们由搜索页横幅拦截兜底。")
    print()
    if missing:
        print(f"[ERR] {missing} 条壳页源文件在 {REDIRECT_DIR} 下缺失。")
        return 1
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="ADHD 知识库 → BookStack 导入脚本")
    ap.add_argument("--dry-run", action="store_true", help="完全离线校验，不发请求")
    ap.add_argument("--base-url", default="http://bookstack.local",
                    help="BookStack 实例地址，如 https://kb.example.com")
    ap.add_argument("--token-id", default=os.environ.get("BOOKSTACK_TOKEN_ID", ""))
    ap.add_argument("--token-secret", default=os.environ.get("BOOKSTACK_TOKEN_SECRET", ""))
    ap.add_argument("--only-book", choices=["A", "B", "C", "D"], default=None,
                    help="只处理某一本书")
    ap.add_argument("--redirects-only", action="store_true",
                    help="只处理 03_零用药系统配置/重定向页/ 下的关键词重定向页")
    args = ap.parse_args()

    if args.redirects_only:
        return do_redirects_dry_run() if args.dry_run else 0  # 实跑路径需用户补全

    pages = load_pages(args.only_book)
    if args.dry_run:
        return do_dry_run(pages, args.base_url)

    if not args.token_id or not args.token_secret:
        print("错误：实跑必须提供 --token-id / --token-secret（或环境变量 BOOKSTACK_TOKEN_ID / BOOKSTACK_TOKEN_SECRET）",
              file=sys.stderr)
        return 2
    # 实跑前最后一次校验
    err_pages = [p for p in pages if p.errors]
    if err_pages:
        print(f"警告：有 {len(err_pages)} 页存在元数据/禁用词错误，仍继续导入。请人工复核。",
              file=sys.stderr)
    do_real_import(pages, args.base_url, args.token_id, args.token_secret)
    return 0


if __name__ == "__main__":
    sys.exit(main())
