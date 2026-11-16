# -*- coding: utf-8 -*-
import re
from collections import Counter
s = open(r'F:\ADHD文献\06_离线预览站\index.html', encoding='utf-8').read()

# ---- 完整侧栏树：顺序扫描 sidebar 内元素 ----
side = re.search(r'<aside class="sidebar".*?>(.*?)</aside>', s, re.S).group(1)
tokens = re.findall(
    r'<div class="tree-book-title">(.*?)</div>'
    r'|<div class="tree-chapter">(.*?)</div>'
    r'|<div class="tree-page" data-page="([A-D]\d\d)">([^<]*)</div>', side)
tree_lines = []
chap_seen = []
for book_t, ch_t, pid, label in tokens:
    if book_t:
        title = re.sub(r'<[^>]+>', '', book_t).strip()
        tree_lines.append('\n[' + title + ']')
    elif ch_t:
        tree_lines.append('  ▸ ' + ch_t)
        chap_seen.append(ch_t)
    else:
        tree_lines.append('      - ' + pid + ' ' + re.sub(r'&quot;', '"', label).strip())
print('\n'.join(tree_lines))

dup = {k: v for k, v in Counter(chap_seen).items() if v > 1}
print('\n章节头总数:', len(chap_seen), ' 重复出现的章节头:', dup if dup else '无 (0)')

# ---- 每页 h1 数 ----
dups = []
for seg in re.findall(r'(<article class="page" id="page-[A-D]\d\d".*?)(?=<article|</main>)', s, re.S):
    pid = re.search(r'id="page-([A-D]\d\d)"', seg).group(1)
    n = len(re.findall(r'<h1[ >]', seg))
    body = re.sub(r'<div class="page-head">.*?</div>', '', seg, flags=re.S)
    title = re.search(r'<h1>(.*?)</h1>', seg).group(1)
    nt = re.sub(r'[\s　：:，。、·\-—“”"\'()（）]+', '', title)
    body_norm = re.sub(r'[\s　：:，。、·\-—“”"\'()（）]+', '', body)
    if n != 1 or nt in body_norm:
        dups.append((pid, 'h1=%d' % n))
print('每页 h1 数=1 且正文无重复标题的页数: %d/19；异常: %s' % (19 - len(dups), dups if dups else '无'))

# ---- 外部资源 ----
print('外部资源: script=%d link=%d img=%d cdn=@import=%d' % (
    len(re.findall(r'<script[^>]+src=["\']?https?://', s, re.I)),
    len(re.findall(r'<link[^>]+href=["\']?https?://', s, re.I)),
    len(re.findall(r'<img[^>]+src=["\']?https?://', s, re.I)),
    len(re.findall(r'cdn|@import|fonts\.googleapis', s, re.I))))
print('首页卡片:', len(re.findall(r'class="home-card"', s)),
      ' 侧栏页面条目:', len(re.findall(r'class="tree-page"', s)))
