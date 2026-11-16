// 最小 DOM stub：在 node 中真实执行内嵌脚本，验证搜索分级逻辑
// 验证方式：eval(js) 后真实触发 searchBtn.click，读取 DOM 元素状态与 innerHTML
const fs = require('fs');
const html = fs.readFileSync('F:/ADHD文献/06_离线预览站/index.html', 'utf8');
const js = html.match(/<script>([\s\S]*)<\/script>/)[1];

function makeEl(id) {
  return {
    id, hidden: false, textContent: '', innerHTML: '', value: '',
    listeners: {},
    addEventListener(ev, fn) { this.listeners[ev] = fn; },
    setAttribute() {}, getAttribute() { return null; },
    classList: { toggle() {}, remove() {}, add() {} },
    closest() { return null; },
  };
}
const els = {};
['searchInput','searchBtn','resultPanel','medBanner','medBannerText','bannerClose',
 'medRedirect','medFallbackNote','resultList','sidebar','main'].forEach(id => els[id] = makeEl(id));
const treePages = ['A00','A01','B01','C01','A06'].map(id => { const e = makeEl('tree-'+id); e.getAttribute = () => id; return e; });
const articles = ['landing','A00','A01','A02','A03','A04','A05','A06',
                   'B01','B02','B03','B04','B05','B06','B07',
                   'C01','C02','C03','D01','D02'].map(id => makeEl('page-'+id));

global.document = {
  getElementById: id => els[id] || makeEl(id),
  querySelectorAll: sel => {
    if (sel === 'article.page, section.page') return articles;
    if (sel === '.tree-page') return treePages;
    return [];
  },
  addEventListener() {},
};
global.window = { scrollTo() {} };

eval(js);

function run(q) {
  els.searchInput.value = q;
  els.searchBtn.listeners['click']();
  // 从 innerHTML 提取结果条目标题（ri-t 里的 "A06 · 标题"）
  const html = els.resultList.innerHTML;
  const titles = [];
  const re = /<div class="ri-t">([^<]+)<\/div>/g;
  let m;
  while ((m = re.exec(html)) !== null) titles.push(m[1]);
  return {
    q,
    bannerShown: !els.medBanner.hidden,
    redirectShown: !els.medRedirect.hidden,
    redirectText: els.medRedirect.textContent || '',
    fallbackShown: !els.medFallbackNote.hidden,
    fallbackText: els.medFallbackNote.textContent || '',
    resultsCount: titles.length,
    titles: titles,
  };
}

const cases = ['药物','剂量','副作用','要不要吃药','专注达','择思达','作业','老师'];
const out = cases.map(run);
console.log(JSON.stringify(out, null, 2));

// 横幅关闭
els.bannerClose.listeners['click']();
console.log('after close: bannerHidden =', els.medBanner.hidden);
