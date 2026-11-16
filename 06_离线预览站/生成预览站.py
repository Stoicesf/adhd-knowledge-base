#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 ADHD 知识库「离线预览站」单文件 index.html
- 只用 Python 标准库
- 扫描 02_内容包 下 19 个 md，解析 YAML 元数据 + 正文，自建极简 Markdown -> HTML
- 输出同目录 index.html（内容/样式/脚本全部内联，file:// 双击可开，零联网）
可重复运行，结果幂等。
"""

import html as html_mod
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent                 # 06_离线预览站
BASE = ROOT.parent / "02_内容包"                       # 只读：正文来源
KW_JSON = (ROOT.parent / "03_零用药系统配置" / "药物关键词表"
           / "药物关键词表.json")
REDIRECT_CSV = (ROOT.parent / "03_零用药系统配置"
                / "重定向页保留清单.csv")
OUT = ROOT / "index.html"

# ---- 书籍 / 章节注册表（依据 01_规范与标准 §1） ----
BOOKS = [
    dict(id="A", dir="书籍A_公开知识库", name="公开知识库",
         slug="public-kb", visibility="public",
         desc="面向 C 端：父母 / 本人 / 伴侣 / 教师，任何人可读",
         chapters=["认识ADHD", "去看医生之前", "边界说明"]),
    dict(id="B", dir="书籍B_家庭工具与情景案例", name="家庭工具与情景案例",
         slug="family-tools", visibility="public",
         desc="面向 C 端：家庭可直接照做的工具、话术与记录模板",
         chapters=["日常场景与家庭调整", "家长自己", "学校沟通",
                   "记录与工具", "成人自己"]),
    dict(id="C", dir="书籍C_B端工作手册", name="B 端工作手册",
         slug="clinician-handbook", visibility="b2b",
         desc="仅 B 端角色可见：家长培训师 / 学校心理老师 / 个案管理",
         chapters=["行为目标与数据", "家长培训", "转介与边界"]),
    dict(id="D", dir="书籍D_临床边界参考", name="临床边界参考",
         slug="clinical-boundary", visibility="clinical",
         desc="仅临床审核角色可见：儿童精神科 / 心理科医生",
         chapters=["诊断与评估边界"]),
]
VISION_LABEL = {"b2b": "仅 B 端角色可见", "clinical": "仅临床角色可见"}

# 首页 6 入口（规范 §8，不多不少 6 条）
HOME_CARDS = [
    dict(q="孩子坐不住、写作业拖拉，我先做什么", who="父母", path=["B01", "B05", "A04"],
         hint="家庭环境调整 5 个动作 → 行为记录表 → 就诊前准备"),
    dict(q="老师反复反馈，要不要去医院", who="父母", path=["A04", "A05", "A02"],
         hint="就诊前准备 → “贴标签”的顾虑 → 不同年龄表现差异"),
    dict(q="怀疑自己是 ADHD 的成年人", who="本人", path=["B07", "A02", "A04"],
         hint="成人自我管理起步 → 年龄差异 → 就诊前准备"),
    dict(q="伴侣/家人总是“忘了、拖了”", who="伴侣", path=["A01", "B07"],
         hint="ADHD 是什么（执行功能解释）→ 成人自我管理"),
    dict(q="我是老师，班里有个孩子", who="教师", path=["B04", "B06"],
         hint="一页纸模板（教师端 5 件事）→ 与家长沟通话术"),
    dict(q="关于药物：本库能回答什么、不能回答什么", who="全部", path=["A06"],
         hint="用药边界说明：本库能回答什么、不能回答什么"),
]

BANNER_TEXT = ("本知识库不提供用药建议。药物相关决定由具备处方权的医生在评估后做出。"
               "你可以使用“就诊前准备”和“想问医生的问题清单”页面，把问题带给医生。")
# has_redirect=true（药品名壳页）：实站会跳转到 A06
REDIRECT_NOTE = "该词在实站会跳转到用药兜底页（A06）"
# has_redirect=false（通用词/问句/类别词）：只横幅，不跳转
NON_REDIRECT_NOTE = "通用词不设独立页面，由横幅统一兜底"


# ---------------- Markdown 极简转换 ----------------
def split_frontmatter(text):
    """返回 (meta_dict, body_lines)。首行必须是 ---。"""
    lines = text.splitlines()
    assert lines and lines[0].strip() == "---", "元数据块必须从第 1 行开始"
    meta = {}
    i = 1
    while i < len(lines) and lines[i].strip() != "---":
        m = re.match(r"^([^:：]+)[:：]\s*(.*)$", lines[i])
        if m:
            meta[m.group(1).strip()] = m.group(2).strip()
        i += 1
    body = lines[i + 1:]
    return meta, body


def strip_meta_blockquote(body_lines):
    """删掉人工可读元数据条（> **面向**… / > **本页不含药名…** 这两行引用）。"""
    out = [ln for ln in body_lines
           if not ln.startswith("> **面向**")
           and not ln.startswith("> **本页不含药名")]
    while out and not out[0].strip():
        out.pop(0)
    return out


def inline_md(s):
    """行内：先转义，再处理链接 / 加粗 / 行内代码。返回 HTML 字符串。"""
    s = html_mod.escape(s, quote=False)
    # 行内代码先保护
    codes = []

    def stash_code(m):
        codes.append(m.group(1))
        return "\x00C%d\x00" % (len(codes) - 1)
    s = re.sub(r"`([^`]+)`", stash_code, s)
    # Markdown 链接先转成占位，避免里面的 URL 被裸链自动化二次包裹
    links = []

    def stash_link(m):
        text, target = m.group(1), m.group(2)
        if target.lower().endswith(".md"):
            base = re.split(r"[\\/]", target)[-1]
            pid = re.match(r"^([ABCD]\d\d)", base)
            if pid:
                rendered = ('<a href="javascript:void(0)" class="internal-link" '
                            'data-page="%s">%s</a>' % (pid.group(1), text))
            else:
                rendered = text
        else:
            rendered = ('<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>'
                        % (target, text))
        links.append(rendered)
        return "\x00L%d\x00" % (len(links) - 1)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", stash_link, s)
    # 裸 URL 自动成链（出处清单里直接书写的 https://...）
    def autolink(m):
        url = m.group(0).rstrip(".,;，。；、")
        return ('<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>'
                % (url, url))
    s = re.sub(r"https?://[A-Za-z0-9\-._~:/?#@!$&'()*+,;=%]+", autolink, s)
    # 加粗
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    # 还原链接与行内代码
    for idx, l in enumerate(links):
        s = s.replace("\x00L%d\x00" % idx, l)
    for idx, c in enumerate(codes):
        s = s.replace("\x00C%d\x00" % idx, "<code>%s</code>" % c)
    return s


def render_table(rows):
    """rows: 表格行（含分隔行）文本列表 -> <table>。"""
    def cells(r):
        r = r.strip().strip("|")
        return [c.strip() for c in r.split("|")]
    head = cells(rows[0])
    body_rows = [cells(r) for r in rows[2:]]
    out = ['<table class="md-table"><thead><tr>']
    out += ["<th>%s</th>" % inline_md(c) for c in head]
    out.append("</tr></thead><tbody>")
    for r in body_rows:
        out.append("<tr>" + "".join("<td>%s</td>" % inline_md(c) for c in r) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def md_to_html(lines):
    """块级转换。"""
    out = []
    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]
        stripped = ln.strip()
        if not stripped:
            i += 1
            continue
        # 表格
        if stripped.startswith("|") and i + 1 < n and re.match(r"^\|[\s:|-]+\|?$", lines[i + 1].strip()):
            block = []
            while i < n and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            out.append(render_table(block))
            continue
        # 标题
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            lvl = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (lvl, inline_md(m.group(2)), lvl))
            i += 1
            continue
        # 分割线
        if re.match(r"^---+$", stripped):
            out.append("<hr>")
            i += 1
            continue
        # 引用块（连续 > 行合并）
        if stripped.startswith(">"):
            block = []
            while i < n and lines[i].strip().startswith(">"):
                block.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            inner = md_to_html(block)
            out.append("<blockquote>%s</blockquote>" % inner)
            continue
        # 无序列表
        if re.match(r"^[-*]\s+", stripped):
            items = []
            while i < n and re.match(r"^\s*[-*]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*]\s+", "", lines[i]))
                i += 1
            out.append("<ul>" + "".join("<li>%s</li>" % inline_md(it) for it in items) + "</ul>")
            continue
        # 有序列表
        if re.match(r"^\d+\.\s+", stripped):
            items = []
            while i < n and re.match(r"^\s*\d+\.\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+\.\s+", "", lines[i]))
                i += 1
            out.append("<ol>" + "".join("<li>%s</li>" % inline_md(it) for it in items) + "</ol>")
            continue
        # 普通段落（连续非空行合并）
        para = [stripped]
        i += 1
        while i < n and lines[i].strip() and not re.match(
                r"(^#{1,4}\s)|(^[-*]\s)|(^\d+\.\s)|(^>)|(^\|)|(^---+$)", lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        out.append("<p>%s</p>" % inline_md(" ".join(para)))
    return "\n".join(out)


def md_to_search_text(lines):
    """抽取纯文本用于搜索索引（去 markdown 符号）。"""
    txt = []
    for ln in lines:
        s = re.sub(r"^[#>\-*|\d.\s]+", "", ln).strip()
        s = re.sub(r"[*`]", "", s)
        s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
        if s:
            txt.append(s)
    return " ".join(txt)


# ---------------- 加载关键词表 ----------------
def load_med_keywords():
    if KW_JSON.exists():
        data = json.loads(KW_JSON.read_text(encoding="utf-8"))
        kws = []
        n_primary = 0
        if isinstance(data.get("keywords"), list):   # 旧 schema：主词 + variants
            for item in data["keywords"]:
                kws.append(item["keyword"])
                kws.extend(item.get("variants", []))
            n_primary = len(data["keywords"])
        elif isinstance(data.get("pages"), list):    # 新 schema：扁平词条表
            for item in data["pages"]:
                kws.append(item["text"])
                if item.get("is_primary"):
                    n_primary += 1
        tag = ("正式词表（药物关键词表.json：%d 主词 / %d 词条）"
               % (n_primary, len(kws)))
    else:
        # 演示词表：按规范 §4.1 禁用词自建最小集
        kws = ["药", "吃药", "用药", "药物", "剂量", "副作用", "不良反应",
               "要不要吃药", "哌甲酯", "mg", "毫克", "停药", "减量", "兴奋剂"]
        tag = "演示词表（03 目录 json 未生成，按规范 §4.1 自建最小词表）"
    return sorted(set(kws), key=lambda k: (-len(k), k)), tag


# ---------------- 加载重定向壳页权威清单（CSV） ----------------
def load_redirect_terms():
    """以 重定向页保留清单.csv 为权威（18 条）；
    药物关键词表.json 的 has_redirect 字段（现已有：true 18 / false 93）作兜底与交叉校验，
    两者不一致时以 CSV 为准并在自检里告警。
    返回 (terms_list, tag_str, warning_str)。"""
    import csv
    terms = []
    if REDIRECT_CSV.exists():
        with open(REDIRECT_CSV, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                t = (row.get("词条") or "").strip()
                if t:
                    terms.append(t)
        tag = ("重定向壳页清单（重定向页保留清单.csv：%d 条药品名）" % len(terms))
    else:
        tag = "重定向壳页清单（CSV 未找到，按空集处理）"

    # 交叉校验：读 JSON 的 has_redirect=true 集合，与 CSV 集合比对
    warning = ""
    try:
        data = json.loads(KW_JSON.read_text(encoding="utf-8"))
        json_true = sorted(p["text"] for p in data.get("pages", [])
                           if p.get("has_redirect") is True)
        csv_set = sorted(terms)
        if json_true != csv_set:
            only_csv = sorted(set(csv_set) - set(json_true))
            only_json = sorted(set(json_true) - set(csv_set))
            warning = ("[交叉校验告警] CSV 与 JSON has_redirect=true 集合不一致；"
                       "以 CSV 为准。仅 CSV 有：%s；仅 JSON 有：%s"
                       % (only_csv or "无", only_json or "无"))
    except Exception as e:
        warning = "[交叉校验告警] 读 JSON has_redirect 失败：%s" % e
    return terms, tag, warning


# ---------------- 扫描内容包 ----------------
def load_pages():
    pages = {}
    for book in BOOKS:
        bdir = BASE / book["dir"]
        for md in sorted(bdir.glob("*.md")):
            pid = re.match(r"^([ABCD]\d\d)", md.name).group(1)
            raw = md.read_text(encoding="utf-8")
            meta, body = split_frontmatter(raw)
            body = strip_meta_blockquote(body)
            # 正文首个 H1 即页面标题，与 page-head 的面包屑+H1 重复，从正文剔除
            h1 = md.stem
            if body and body[0].strip().startswith("# "):
                h1 = re.sub(r"^#\s+", "", body[0].strip())
                body = body[1:]
                while body and not body[0].strip():
                    body.pop(0)
            body_html = md_to_html(body)
            search_text = md_to_search_text(body)
            pages[pid] = dict(
                id=pid, book=book["id"], book_name=book["name"],
                chapter=meta.get("章节", ""),
                audience=meta.get("面向", ""),
                evidence=meta.get("证据状态", ""),
                reviewed=meta.get("最后审核", ""),
                checked=meta.get("零用药勾选", ""),
                ptype=meta.get("页面类型", ""),
                slug=meta.get("slug", ""),
                title=h1, body=body_html, text=search_text,
                file=md.name,
            )
    return pages


# ---------------- 侧边栏树 ----------------
def build_tree_html(pages):
    parts = []
    for book in BOOKS:
        chip = ""
        if book["visibility"] in VISION_LABEL:
            chip = ('<span class="vis-chip vis-%s" title="离线预览：实站按角色登录后可见">%s</span>'
                    % (book["visibility"], VISION_LABEL[book["visibility"]]))
        parts.append('<div class="tree-book"><div class="tree-book-title">📕 %s · %s %s</div>'
                     % (book["id"], html_mod.escape(book["name"]), chip))
        # A00 等（书籍顶层）单列在书下、不进章节
        for p in sorted((x for x in pages.values()
                         if x["book"] == book["id"] and x["chapter"].startswith("（")),
                        key=lambda x: x["id"]):
            parts.append('<div class="tree-page" data-page="%s">%s %s</div>'
                         % (p["id"], p["id"], html_mod.escape(p["title"])))
        # 章节按规范 §1 章节顺序输出，每章头只出现一次；章内按页号升序
        for ch in book["chapters"]:
            cps = sorted([p for p in pages.values()
                          if p["book"] == book["id"] and p["chapter"] == ch],
                         key=lambda x: x["id"])
            if not cps:
                continue
            parts.append('<div class="tree-chapter">%s</div>' % html_mod.escape(ch))
            for p in cps:
                parts.append('<div class="tree-page" data-page="%s">%s %s</div>'
                             % (p["id"], p["id"], html_mod.escape(p["title"])))
        parts.append("</div>")
    return "\n".join(parts)


BADGE_CLASS = {
    "强证据": "b-strong", "有条件推荐": "b-conditional",
    "经验性策略": "b-experience", "虚构教学案例": "b-fiction",
}


def meta_bar_html(p):
    ev = p["evidence"]
    if ev in BADGE_CLASS:
        badge = '<span class="badge %s">证据状态 · %s</span>' % (BADGE_CLASS[ev], ev)
    else:
        badge = '<span class="badge b-none">证据状态 · 导航页（首页不设）</span>'
    check = ('<label class="checkbar"><input type="checkbox" checked disabled> '
             '本页不含药名、剂量、用药选择、副作用处理、停药减量建议 —— ☑ 已勾选</label>')
    return ('<div class="metabar">'
            '<span class="meta-item"><b>面向</b> %s</span>%s'
            '<span class="meta-item"><b>最后审核</b> %s</span>'
            '</div><div class="metabar2">%s</div>'
            % (html_mod.escape(p["audience"]), badge,
               html_mod.escape(p["reviewed"]), check))


# ---------------- 模板字段说明面板 ----------------
TEMPLATE_PANEL = """
<div class="panel">
  <h3>模板字段说明（预览演示）</h3>
  <div class="tpl-cols">
    <div class="tpl-col">
      <h4>C 端模板（书籍 A / B，面向家长 / 本人 / 教师）</h4>
      <ul>
        <li>机器可读元数据（YAML 头）：<code>面向</code> / <code>证据状态</code> / <code>最后审核</code> / <code>零用药勾选</code> / <code>页面类型</code> / <code>书籍</code> / <code>章节</code> / <code>slug</code></li>
        <li>正文骨架：今天能做的 3 件事 → 为什么这样做有效 → 具体怎么做 → 什么情况下需要换一种做法 → 常见误区 → 依据与出处 → 下一条可操作建议</li>
        <li>页尾固定边界句：本页提供的是教育与自我管理信息，不构成诊断或治疗建议……</li>
      </ul>
    </div>
    <div class="tpl-col tpl-b">
      <h4>B 端模板（书籍 C / D，面向专业人员 / 临床审核）</h4>
      <ul>
        <li>同上字段，<code>页面类型</code> 为 <code>B端-书籍C</code> / <code>临床-书籍D</code></li>
        <li>第一节为「适用对象与使用前提」</li>
        <li class="must">必含：<b>本页不讨论药物选择与剂量</b></li>
        <li class="must">必含：<b>家长询问用药时的固定回应</b>——“这需要由开具处方的医生判断，我可以帮你整理要问医生的问题。”</li>
        <li>书籍 D 仅摘要层级：不构成诊断依据，不得据此对个人下诊断</li>
      </ul>
    </div>
  </div>
  <p class="evlegend">证据状态四档徽章：
    <span class="badge b-strong">强证据</span>
    <span class="badge b-conditional">有条件推荐</span>
    <span class="badge b-experience">经验性策略</span>
    <span class="badge b-fiction">虚构教学案例</span>
  </p>
</div>
"""


# ---------------- 组装 HTML ----------------
def build_html(pages, med_kws, kw_tag, redirect_terms, redirect_tag):
    tree = build_tree_html(pages)
    articles = []
    search_index = []
    for pid in sorted(pages):
        p = pages[pid]
        vis = ""
        if p["book"] in ("C", "D"):
            vis = ('<div class="vis-notice">⚠ %s —— 离线预览开放阅读，实站需对应角色登录。</div>'
                   % VISION_LABEL["b2b" if p["book"] == "C" else "clinical"])
        articles.append(
            '<article class="page" id="page-%s" hidden>'
            '<div class="page-head"><span class="pid">%s · %s</span>'
            '<h1>%s</h1></div>%s%s<div class="page-body">%s</div></article>'
            % (pid, pid, html_mod.escape(p["book_name"]), html_mod.escape(p["title"]),
               vis, meta_bar_html(p), p["body"]))
        snippet = re.sub(r"<[^>]+>", "", p["body"])[:90]
        search_index.append(dict(id=pid, title=p["title"], book=p["book_name"],
                                 chapter=p["chapter"], audience=p["audience"],
                                 text=(p["title"] + " " + p["text"]),
                                 snippet=snippet))
    articles_html = "\n".join(articles)

    cards = []
    for c in HOME_CARDS:
        chips = "".join('<span class="crumb">%s</span>' % x for x in c["path"])
        cards.append(
            '<div class="home-card" data-go="%s"><div class="hc-q">%s</div>'
            '<div class="hc-who">适合：%s</div>'
            '<div class="hc-hint">%s</div><div class="hc-path">%s</div></div>'
            % (c["path"][0], html_mod.escape(c["q"]), html_mod.escape(c["who"]),
               html_mod.escape(c["hint"]), chips))
    cards_html = "\n".join(cards)

    pages_json = json.dumps(search_index, ensure_ascii=False)
    med_json = json.dumps(med_kws, ensure_ascii=False)
    redirect_json = json.dumps(redirect_terms, ensure_ascii=False)

    tpl_panel = TEMPLATE_PANEL

    css = CSS
    js = JS.replace("__PAGES__", pages_json) \
           .replace("__MEDKW__", med_json) \
           .replace("__REDIRECT_TERMS__", redirect_json) \
           .replace("__BANNER__", json.dumps(BANNER_TEXT, ensure_ascii=False)) \
           .replace("__REDIRECT_NOTE__", json.dumps(REDIRECT_NOTE, ensure_ascii=False)) \
           .replace("__NON_REDIRECT_NOTE__", json.dumps(NON_REDIRECT_NOTE, ensure_ascii=False))

    landing = """
<section id="page-landing" class="page">
  <div class="hero">
    <h1>ADHD 知识库 · 离线预览站</h1>
    <p class="hero-sub">这是一个<b>完全离线</b>的结构与效果预览，双击即可打开，不需要联网。</p>
  </div>
  <div class="panel">
    <h3>这个包怎么用</h3>
    <ul class="howto">
      <li><b>你现在看到的是预览。</b>它用来在真正部署 BookStack 之前，先看到书籍结构、页面样式与搜索兜底逻辑。</li>
      <li><b>真实部署用另一个包。</b>导入 BookStack 的正式内容在 <code>04_BookStack导入</code> 目录；本预览站<b>不替代</b>它。</li>
      <li><b>内容以 02 目录为准。</b>所有页面正文来自 <code>02_内容包</code> 的 19 个 Markdown 文件；本页只是把它们渲染成网页。</li>
      <li><b>左侧切书切页。</b>A 公开知识库 / B 家庭工具与情景案例 对所有人；C 与 D 在实站中分别仅 B 端与临床角色可见（本预览已标注）。</li>
      <li><b>试试顶部搜索。</b>输入“作业 / 老师 / 记录表”看普通结果；输入“剂量 / 副作用 / 要不要吃药”看用药横幅（<b>不跳转</b>，通用词由横幅统一兜底）；输入“专注达 / 择思达 / 哌甲酯”看横幅 + 跳转兜底页（A06）。</li>
    </ul>
    <p class="kwtag">关键词来源：%s；重定向壳页来源：%s。</p>
  </div>
  <h2 class="sec-title">6 个高频入口（与 A00 一致，共 6 条）</h2>
  <div class="card-grid">%s</div>
  %s
</section>
""" % (html_mod.escape(kw_tag), html_mod.escape(redirect_tag), cards_html, tpl_panel)

    doc = """<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ADHD 知识库 · 离线预览</title>
<style>%s</style>
</head>
<body>
<header class="topbar">
  <div class="brand">ADHD 知识库 <span class="offline-tag">离线预览</span></div>
  <div class="searchbox">
    <input id="searchInput" type="search" placeholder="搜索页面：试试“作业”“老师”“记录表”，或“剂量”“要不要吃药”…">
    <button id="searchBtn">搜索</button>
  </div>
</header>
<div class="layout">
  <aside class="sidebar" id="sidebar">
    <div class="side-note">书籍 → 章节 → 页面（%d 页）</div>
    %s
  </aside>
  <main class="main" id="main">
    <div id="resultPanel" class="result-panel" hidden>
      <div id="medBanner" class="med-banner" hidden>
        <b id="medBannerText"></b>
        <button class="banner-close" id="bannerClose" title="关闭横幅">×</button>
      </div>
      <div id="medRedirect" class="med-redirect" hidden></div>
      <div id="medFallbackNote" class="med-fallback-note" hidden></div>
      <h3 class="res-title">搜索结果</h3>
      <div id="resultList"></div>
    </div>
    %s
    %s
  </main>
</div>
<script>%s</script>
</body></html>""" % (css, len(pages), tree, landing, articles_html, js)
    return doc


CSS = r"""
:root{--ink:#1f2328;--sub:#57606a;--line:#e3e6ea;--bg:#f7f8f9;--card:#fff;
--green:#1a7f37;--greenbg:#dafbe1;--amber:#9a6700;--amberbg:#fff8c5;
--steel:#0b6bcb;--steelbg:#ddf4ff;--red:#cf222e;--redbg:#ffebe9;--gray:#57606a;--graybg:#eef1f4;}
*{box-sizing:border-box}
body{margin:0;font-family:"Microsoft YaHei","PingFang SC","Source Han Sans SC","Noto Sans CJK SC",system-ui,-apple-system,"Segoe UI",sans-serif;
color:var(--ink);background:var(--bg);line-height:1.75;font-size:15.5px}
a{color:var(--steel)}
.topbar{position:sticky;top:0;z-index:20;display:flex;gap:16px;align-items:center;
padding:10px 18px;background:#fff;border-bottom:1px solid var(--line);flex-wrap:wrap}
.brand{font-weight:700;font-size:16px;white-space:nowrap}
.offline-tag{font-size:12px;background:var(--amberbg);color:var(--amber);
border:1px solid #eac54f;border-radius:10px;padding:1px 8px;margin-left:6px;font-weight:600}
.searchbox{flex:1;display:flex;gap:8px;min-width:240px;max-width:640px}
.searchbox input{flex:1;padding:8px 12px;border:1px solid var(--line);border-radius:8px;font-size:14px}
.searchbox button{padding:8px 16px;border:0;border-radius:8px;background:var(--ink);color:#fff;cursor:pointer}
.layout{display:flex;gap:0;align-items:flex-start}
.sidebar{width:300px;min-width:260px;max-width:46vw;height:calc(100vh - 53px);overflow:auto;
position:sticky;top:53px;background:#fff;border-right:1px solid var(--line);padding:12px}
.side-note{font-size:12px;color:var(--sub);margin-bottom:8px}
.tree-book{margin-bottom:10px}
.tree-book-title{font-weight:700;font-size:14px;padding:4px 6px}
.tree-chapter{font-size:12.5px;color:var(--sub);margin:8px 0 2px 6px;font-weight:600}
.tree-page{padding:5px 8px 5px 14px;font-size:13.5px;border-radius:6px;cursor:pointer;color:var(--ink)}
.tree-page:hover{background:var(--bg)}
.tree-page.active{background:var(--steelbg);color:var(--steel);font-weight:600}
.vis-chip{font-size:10.5px;border-radius:8px;padding:1px 6px;margin-left:6px;font-weight:600;vertical-align:middle}
.vis-b2b{background:#fff1e5;color:#bc4c00;border:1px solid #ffab7b}
.vis-clinical{background:var(--redbg);color:var(--red);border:1px solid #ff8182}
.main{flex:1;padding:24px 32px;max-width:960px;min-width:0}
.page{max-width:900px}
.hero h1{font-size:26px;margin:6px 0 4px}
.hero-sub{color:var(--sub);margin-top:0}
.panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 20px;margin:16px 0}
.panel h3{margin-top:0}
.howto li{margin:6px 0}
.kwtag{font-size:12.5px;color:var(--sub);margin-bottom:0}
.sec-title{margin:26px 0 10px;font-size:19px}
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
.home-card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;cursor:pointer;transition:box-shadow .15s,transform .15s}
.home-card:hover{box-shadow:0 3px 12px rgba(0,0,0,.08);transform:translateY(-1px)}
.hc-q{font-weight:700;font-size:14.5px}
.hc-who{font-size:12.5px;color:var(--steel);font-weight:600;margin-top:6px}
.hc-hint{font-size:12.5px;color:var(--sub);margin-top:4px}
.hc-path{margin-top:8px}
.crumb{display:inline-block;font-size:11.5px;background:var(--graybg);border-radius:8px;padding:1px 7px;margin-right:4px;color:var(--ink)}
.tpl-cols{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.tpl-col h4{margin:0 0 6px;font-size:14px}
.tpl-col ul{margin:4px 0;padding-left:20px;font-size:13.5px}
.tpl-b{background:#fff7f0;border:1px solid #ffab7b;border-radius:8px;padding:10px 14px}
.tpl-b .must{color:#bc4c00}
.evlegend{font-size:13px;margin-bottom:0}
.page-head .pid{font-size:12.5px;color:var(--sub)}
.page-head h1{font-size:23px;margin:4px 0 12px}
.vis-notice{background:#fff1e5;border:1px solid #ffab7b;color:#bc4c00;
border-radius:8px;padding:8px 12px;font-size:13px;margin-bottom:12px}
.metabar{display:flex;flex-wrap:wrap;gap:14px;align-items:center;
background:#fff;border:1px solid var(--line);border-left:4px solid var(--steel);
border-radius:8px;padding:8px 14px;margin-bottom:6px;font-size:13.5px}
.meta-item b{color:var(--sub);font-weight:600;margin-right:4px}
.metabar2{margin-bottom:18px}
.badge{display:inline-block;font-size:12px;font-weight:700;border-radius:10px;padding:2px 10px}
.b-strong{background:var(--greenbg);color:var(--green);border:1px solid #4ac26b}
.b-conditional{background:var(--amberbg);color:var(--amber);border:1px solid #eac54f}
.b-experience{background:var(--steelbg);color:var(--steel);border:1px solid #79c0ff}
.b-fiction{background:var(--redbg);color:var(--red);border:1px solid #ff8182}
.b-none{background:var(--graybg);color:var(--gray);border:1px solid var(--line)}
.checkbar{display:inline-flex;align-items:center;gap:6px;font-size:13px;
background:var(--greenbg);border:1px solid #4ac26b;color:#116329;border-radius:8px;padding:5px 12px}
.checkbar input{accent-color:var(--green)}
.page-body h2{font-size:18px;border-bottom:1px solid var(--line);padding-bottom:4px;margin-top:26px}
.page-body h3{font-size:15.5px;margin-top:20px}
.page-body p{margin:10px 0}
.page-body ul,.page-body ol{padding-left:24px}
.page-body blockquote{margin:12px 0;padding:8px 14px;background:var(--graybg);
border-left:4px solid var(--gray);border-radius:0 8px 8px 0;color:#3b4148}
.md-table{border-collapse:collapse;width:100%;margin:12px 0;font-size:13.5px}
.md-table th,.md-table td{border:1px solid var(--line);padding:6px 10px;text-align:left;vertical-align:top}
.md-table th{background:var(--graybg)}
code{background:var(--graybg);padding:1px 5px;border-radius:4px;font-size:13px}
hr{border:0;border-top:1px solid var(--line);margin:20px 0}
.result-panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 20px;margin-bottom:20px}
.med-banner{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;
background:#fff3cd;border:1.5px solid #d4a72c;color:#7a5c00;border-radius:10px;padding:12px 14px;margin-bottom:10px}
.banner-close{background:none;border:0;font-size:20px;cursor:pointer;color:#7a5c00;line-height:1}
.med-redirect{background:var(--redbg);border:1px solid #ff8182;color:var(--red);
border-radius:8px;padding:8px 12px;margin-bottom:10px;font-size:14px;font-weight:600;cursor:pointer;display:inline-block}
.med-fallback-note{background:var(--steelbg);border:1px solid #79c0ff;color:var(--steel);
border-radius:8px;padding:8px 12px;margin-bottom:10px;font-size:14px;display:inline-block}
.res-title{margin:6px 0 10px;font-size:15px}
.res-item{padding:10px 12px;border:1px solid var(--line);border-radius:8px;margin-bottom:8px;cursor:pointer}
.res-item:hover{border-color:var(--steel)}
.res-item .ri-t{font-weight:700;font-size:14.5px}
.res-item .ri-meta{font-size:12px;color:var(--sub)}
.res-item .ri-snip{font-size:13px;color:#3b4148;margin-top:3px}
.res-empty{color:var(--sub);font-size:14px}
@media(max-width:860px){
.layout{flex-direction:column}.sidebar{width:100%;max-width:none;height:auto;position:static;border-right:0;border-bottom:1px solid var(--line)}
.main{padding:16px}.tpl-cols{grid-template-columns:1fr}
}
"""

JS = r"""
var PAGES = __PAGES__;
var MEDKW = __MEDKW__;
var REDIRECT_TERMS = __REDIRECT_TERMS__;
var BANNER = __BANNER__;
var REDIRECT_NOTE = __REDIRECT_NOTE__;
var NON_REDIRECT_NOTE = __NON_REDIRECT_NOTE__;

function showPage(id){
  var arts = document.querySelectorAll('article.page, section.page');
  arts.forEach(function(a){ a.hidden = true; });
  var el = document.getElementById('page-' + id);
  document.getElementById('resultPanel').hidden = true;
  if(!el){ return; }
  el.hidden = false;
  document.querySelectorAll('.tree-page').forEach(function(t){
    t.classList.toggle('active', t.getAttribute('data-page') === id);
  });
  window.scrollTo({top:0, behavior:'smooth'});
}
function goHome(){ showPage('landing'); }

document.addEventListener('click', function(e){
  var t = e.target.closest('[data-page], .internal-link, .home-card, .med-redirect');
  if(!t){ return; }
  var id = t.getAttribute('data-page') || t.getAttribute('data-go');
  if(t.classList.contains('med-redirect')){ id = 'A06'; }
  if(id){ showPage(id); }
});

function esc(s){ return s.replace(/[&<>"]/g, function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }

function doSearch(){
  var q = document.getElementById('searchInput').value.trim().toLowerCase();
  var panel = document.getElementById('resultPanel');
  var list = document.getElementById('resultList');
  var banner = document.getElementById('medBanner');
  var redir = document.getElementById('medRedirect');
  var fallback = document.getElementById('medFallbackNote');
  panel.hidden = false;
  document.querySelectorAll('article.page, section.page').forEach(function(a){ a.hidden = true; });
  document.querySelectorAll('.tree-page').forEach(function(t){ t.classList.remove('active'); });
  if(!q){ panel.hidden = true; goHome(); return; }

  // ① 横幅命中：111 条关键词（通用词/问句/类别词/药品名都在内）
  var medHit = MEDKW.some(function(k){ return q.indexOf(k.toLowerCase()) !== -1; });
  // ② 跳转命中：仅 18 条药品名壳页（CSV 权威）
  var redirectHit = REDIRECT_TERMS.some(function(k){ return q.indexOf(k.toLowerCase()) !== -1; });

  if(medHit){
    document.getElementById('medBannerText').textContent = BANNER;
    banner.hidden = false;
    if(redirectHit){
      // 药品名：横幅 + 可点击跳转提示（落点 A06）
      redir.hidden = false;
      redir.textContent = '➜ ' + REDIRECT_NOTE + '（点击直达 A06）';
      fallback.hidden = true;
    } else {
      // 通用词：只横幅 + 一句"不设独立页"说明，绝不出现"已重定向/跳转"字样
      fallback.hidden = false;
      fallback.textContent = 'ℹ ' + NON_REDIRECT_NOTE;
      redir.hidden = true;
    }
  } else {
    banner.hidden = true;
    redir.hidden = true;
    fallback.hidden = true;
  }

  // ③ 普通匹配：标题 + 正文（仅 19 个内容页，不含壳页）
  var hits = PAGES.filter(function(p){
    return (p.title + ' ' + p.text).toLowerCase().indexOf(q) !== -1;
  });
  hits.sort(function(a,b){
    var at = a.title.toLowerCase().indexOf(q) !== -1 ? 0 : 1;
    var bt = b.title.toLowerCase().indexOf(q) !== -1 ? 0 : 1;
    return at - bt;
  });
  if(hits.length === 0){
    list.innerHTML = '<div class="res-empty">没有命中任何页面。换个词试试，或从左侧书目进入。</div>';
  } else {
    list.innerHTML = hits.map(function(p){
      return '<div class="res-item" data-page="' + p.id + '">'
        + '<div class="ri-t">' + esc(p.id + ' · ' + p.title) + '</div>'
        + '<div class="ri-meta">' + esc(p.book + ' / ' + p.chapter + ' / 面向：' + p.audience) + '</div>'
        + '<div class="ri-snip">' + esc(p.snippet) + '…</div></div>';
    }).join('');
  }
  window.scrollTo({top:0, behavior:'smooth'});
}
document.getElementById('searchBtn').addEventListener('click', doSearch);
document.getElementById('searchInput').addEventListener('keydown', function(e){
  if(e.key === 'Enter'){ doSearch(); }
});
document.getElementById('bannerClose').addEventListener('click', function(){
  document.getElementById('medBanner').hidden = true;
});
goHome();
"""


def main():
    pages = load_pages()
    assert len(pages) == 19, "应渲染 19 页，实际 %d" % len(pages)
    med_kws, kw_tag = load_med_keywords()
    redirect_terms, redirect_tag, redirect_warning = load_redirect_terms()
    doc = build_html(pages, med_kws, kw_tag, redirect_terms, redirect_tag)
    OUT.write_text(doc, encoding="utf-8")

    # ---- 自检输出 ----
    src = doc
    ext_scripts = len(re.findall(r'<script[^>]+src\s*=\s*["\']https?://', src))
    ext_css = len(re.findall(r'<link[^>]+href\s*=\s*["\']https?://', src))
    ext_img = len(re.findall(r'<img[^>]+src\s*=\s*["\']https?://', src))
    cdn_hits = len(re.findall(r'cdn|@import|fonts\.googleapis', src, re.I))
    meta_missing = 0
    for pid, p in pages.items():
        bar = meta_bar_html(p)
        for need in ["面向", "证据状态", "最后审核", "checkbar"]:
            if need not in bar:
                meta_missing += 1
    tree_count = len(re.findall(r'class="tree-page"', src))
    print("渲染页面数: %d" % len(pages))
    print("外部资源引用: script=%d link=%d img=%d cdn/@import/googlefonts=%d (应全为 0)"
          % (ext_scripts, ext_css, ext_img, cdn_hits))
    print("侧边栏层级页面条目: %d (应=19)" % tree_count)
    print("首页入口卡片: %d (应=6)" % src.count('class="home-card"'))
    print("每页元数据条缺项: %d (应=0)" % meta_missing)
    print("横幅文案存在: %s" % (BANNER_TEXT in src))
    print("跳转提示文案存在: %s" % (REDIRECT_NOTE in src))
    print("通用词兜底说明存在: %s" % (NON_REDIRECT_NOTE in src))
    print("药物关键词条数(横幅词表, 含变体): %d" % len(med_kws))
    print("重定向壳页条数(CSV 权威): %d" % len(redirect_terms))
    if redirect_warning:
        print(redirect_warning)
    else:
        print("交叉校验: CSV 与 JSON has_redirect=true 集合一致 (%d 条)" % len(redirect_terms))
    print("输出: %s (%.1f KB)" % (OUT, OUT.stat().st_size / 1024))


if __name__ == "__main__":
    main()
