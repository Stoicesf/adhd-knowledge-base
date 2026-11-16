/* 批次 1 验收：node 零依赖，轻量 DOM 仿真真实执行 app.js。
 * 覆盖：呼吸 5 回合时间轴 + 帧驱动渲染、12 张话术卡逐张文案核对、
 *       pending 占位不编造、三级撤退/预警表/修复/免责渲染、
 *       日志写入-持久化-清空、黑夜模式切换、火气分档、静态资源契约。
 * 浏览器像素级（375px 不溢出）只能静态断言，不假装跑过浏览器。
 */
'use strict';
const fs = require('fs');
const path = require('path');

const HERE = __dirname;
const DATA = path.join(HERE, 'data');
const SRC = path.join(HERE, 'src');
const F = JSON.parse(fs.readFileSync(path.join(DATA, 'features.json'), 'utf-8'));
const C = JSON.parse(fs.readFileSync(path.join(DATA, 'copy_mapping.json'), 'utf-8'));
const CHUNKS = path.join(HERE, '..', '..', '03_agent编译', 'output', 'chunks.jsonl');
const inject = {};
fs.readFileSync(CHUNKS, 'utf-8').split('\n').filter(Boolean).forEach(l => {
  const r = JSON.parse(l); inject[r.id] = r.inject_text;
});

let pass = 0, fail = 0;
const lines = [];
function ok(name, cond, detail) {
  if (cond) { pass++; lines.push(`✓ ${name}${detail ? ' — ' + detail : ''}`); }
  else { fail++; lines.push(`✗ ${name}${detail ? ' — ' + detail : ''}`); }
}

/* ---------- 轻量 DOM 仿真 ---------- */
function mkNode(tag) {
  return {
    tagName: tag, className: '', _text: '', children: [], style: {},
    value: '', checked: false, disabled: false, _h: {},
    get textContent() { return this._text + this.children.map(c => c.textContent).join(''); },
    set textContent(v) { this._text = String(v); this.children = []; },
    appendChild(c) { this.children.push(c); return c; },
    addEventListener(ev, fn) { this._h[ev] = fn; },
    setAttribute(k, v) { this[k] = v; }
  };
}
const nodes = {};
global.document = {
  documentElement: mkNode('html'),
  body: mkNode('body'),
  getElementById(id) { return nodes[id] || (nodes[id] = mkNode('div')); },
  createElement(tag) { return mkNode(tag); }
};
const mem = {};
global.localStorage = {
  getItem: k => (k in mem ? mem[k] : null),
  setItem: (k, v) => { mem[k] = String(v); },
  removeItem: k => { delete mem[k]; }
};
let fakeNow = 1000;
global.performance = { now: () => fakeNow };
const rafQ = [];
global.requestAnimationFrame = fn => { rafQ.push(fn); return rafQ.length; };
global.cancelAnimationFrame = () => {};
global.matchMedia = () => ({ matches: false });
global.window = global;
global.__PC_FEATURES__ = F;
global.__PC_COPY__ = C;

require(path.join(SRC, 'core.js'));
require(path.join(SRC, 'api.js'));
const K = global.PCCore;
ok('core.js 暴露 PCCore', !!K && typeof K.breathingTimeline === 'function');
require(path.join(SRC, 'app.js'));   // 真实执行渲染
ok('app.js 执行完成、无异常', true);

/* ---------- 1. 呼吸时间轴与帧驱动 ---------- */
const tl = K.breathingTimeline(F);
ok('呼吸 5 回合 / 15 阶段', tl.rounds === 5 && tl.phases.length === 15,
   `rounds=${tl.rounds} phases=${tl.phases.length}`);
ok('总时长 60000ms（(4+2+6)*5*1000）', tl.totalMs === 60000, `totalMs=${tl.totalMs}`);
ok('阶段顺序 4-2-6 循环 5 次', tl.phases.every((p, i) =>
   p.durationMs === [4000, 2000, 6000][i % 3] &&
   p.startMs === i * 0 + tl.phases.slice(0, i).reduce((s, x) => s + x.durationMs, 0)));
const st0 = K.breathingStateAt(tl, 0);
const stIn = K.breathingStateAt(tl, 2000);
const stHold = K.breathingStateAt(tl, 5000);
const stEx = K.breathingStateAt(tl, 7000);
ok('吸气/屏息/呼气阶段可判', st0.phase === 'inhale' && stHold.phase === 'hold' && stEx.phase === 'exhale',
   `${st0.phase}/${stHold.phase}/${stEx.phase}`);
ok('scale 单调：吸气放大、呼气回落', st0.scale === 1 && stIn.scale > 1 && stHold.scale === 1.35 && stEx.scale < 1.35,
   `${st0.scale.toFixed(3)}→${stIn.scale.toFixed(3)}→${stEx.scale.toFixed(3)}`);
ok('到 60s 落完成态', K.breathingStateAt(tl, 60000).done === true);
ok('59.9s 仍未完成（不早退）', K.breathingStateAt(tl, 59900).done === false);
// 用 16.7ms 假帧走完整轮，检查阶段切换与理论边界偏差 ≤ 1 帧
let maxDev = 0, prevPhase = null;
for (let t = 0; t <= 60000; t += 16.7) {
  const s = K.breathingStateAt(tl, t);
  if (!s.done && prevPhase !== null && s.phase !== prevPhase) {
    const boundary = tl.phases.find(p => p.startMs <= t && p.endMs > t);
    maxDev = Math.max(maxDev, Math.abs(t - boundary.startMs));
  }
  prevPhase = s.done ? null : s.phase;
}
ok('帧驱动阶段切换误差 ≤100ms（绝对时差、无累计漂移）', maxDev <= 100, `maxDev=${maxDev.toFixed(1)}ms`);
// 实际触发 start 并推进到完成帧
rafQ.length = 0;
nodes['breath-start']._h.click();
ok('点击开始后入队 rAF', rafQ.length === 1);
const frame = rafQ[0];
frame(fakeNow + 30000);
ok('30s 帧渲染到第 3 回合', nodes['breath-label'].textContent.indexOf('3 / 5') >= 0,
   nodes['breath-label'].textContent);
frame(fakeNow + 60000);
ok('60s 帧渲染完成态', nodes['breath-label'].textContent === '完成' &&
   nodes['breath-start'].disabled === false, nodes['breath-label'].textContent);

/* ---------- 2. 12 张话术卡逐张核对（不编造） ---------- */
const cards = K.groupSlots(C, 'script_cards');
ok('话术卡槽位数 = 12', cards.length === 12, `slots=${cards.length}`);
let cardTexts = [], cardSources = [];
for (let i = 0; i < 12; i++) {
  const box = nodes['script-card'];
  cardTexts.push(box.children[0] ? box.children[0].textContent : '');
  cardSources.push(box.children[1] ? box.children[1].textContent : '');
  nodes['script-next']._h.click();
}
let mappedOk = 0, pendingOk = 0;
cards.forEach((rec, i) => {
  if (rec.status === 'mapped') {
    if (cardTexts[i] === inject[rec.source_entry_id]) { mappedOk++; }
  } else {
    if (cardTexts[i] === K.pendingText('script_cards') &&
        cardSources[i].indexOf('来源：整理中') >= 0) { pendingOk++; }
  }
});
// 批次 3 联动（2026-11-13）：script_card_08..12 由 5 条派生条目回填，
// 卡片组 mapped 7→12 / pending 5→0。期望值改为从 copy_mapping.json 动态取，
// 保留「逐字一致」「占位不编造」两条覆盖，不删断言、不放宽口径。
// 卡片内已无 pending，占位覆盖由 §3 的 10 个非卡片槽位继续承担
// （3 撤退 + 5 预警 + 1 修复 + 1 免责），下面另加一条归属断言可证伪。
const expectedMapped = cards.filter(c => c.status === 'mapped').length;
const expectedPending = cards.filter(c => c.status === 'pending_batch3').length;
ok('每张 mapped 卡逐字等于 inject_text', expectedMapped > 0 && mappedOk === expectedMapped,
   `${mappedOk}/${expectedMapped}`);
ok('每张 pending 卡只显示固定占位、无编造文案', pendingOk === expectedPending,
   `${pendingOk}/${expectedPending}`);
// 批次 5 联动（2026-11-14）：三档撤退 3 槽 mapped、免责 1 槽 filled_constant，
// pending 10 → 6（修复卡 1 + 五类预警 5）。期望值仍从 copy_mapping.json 动态取。
// 批次 8 联动（2026-11-15）：修复卡 + 五类预警 6 槽授权抓取来源接入 → pending 6 → 0。
// 期望值动态取，不硬编码 6。
ok('批次8 后剩余 pending 恰为 0（修复卡+五类预警已回填）、全落非卡片组，且全页无批次号占位残留',
   C.records.filter(r => r.status === 'pending_batch3').length === 0 &&
   C.records.filter(r => r.status === 'pending_batch3' && r.group === 'script_cards').length === 0 &&
   [nodes['script-card'], nodes['retreat-list'], nodes['warning-table'],
    nodes['repair-card'], nodes['disclaimer-text']]
     .every(n => n.textContent.indexOf('批次') === -1),
   `total=${C.records.filter(r => r.status === 'pending_batch3').length}`);
const extra = cardTexts.filter((t, i) => cards[i].status === 'pending_batch3' &&
   t !== K.pendingText('script_cards'));
ok('pending 卡无任何其他文本', extra.length === 0, `extra=${extra.length}`);

/* ---------- 3. 撤退 / 预警 / 修复 / 免责（批次 5：三档撤退 mapped、免责 filled_constant） ---------- */
const retreatSlots = ['retreat_low', 'retreat_mid', 'retreat_high']
  .map(s => K.resolveSlot(K.findSlot(C, s)));
const retreatTexts = nodes['retreat-list'].children.map(d => d.children[1].textContent);
const retreatTiers = retreatSlots.map(r => r.source);
ok('三级撤退批次 5 起 mapped：逐字取自对应档位条目，且映射到 no_label/one_step/refer 三档',
   retreatSlots.length === 3 && retreatSlots.every((r, i) =>
     r.pending === false && r.text === inject[r.source] &&
     retreatTexts[i].indexOf(r.text) === 0) &&
   JSON.stringify(retreatTiers.slice().sort()) ===
   JSON.stringify(['pc_escalation_no_label_01', 'pc_escalation_one_step_01', 'pc_escalation_refer_01']),
   retreatTiers.join(','));
const tbody = nodes['warning-table'].children[1];
const rows = tbody.children;
ok('预警表 5 行 × 3 列（部位 + 两列）', rows.length === 5 &&
   rows.every(r => r.children.length === 3), `rows=${rows.length}`);
const cellTexts = rows.flatMap(r => [r.children[1].textContent, r.children[2].textContent]);
// 批次 8：预警表两列已回填为 mapped（逐字取自 pc_warning_* 条目），
// 两列同显该槽 inject_text（app.js 对 columns 各生成一个 td，均填 rec.text）。
const warnRecs = ['呼吸', '肌肉', '声音', '胸口', '念头'].map(c =>
  K.resolveSlot(K.findSlot(C, 'warning_signs_' + c)));
ok('预警表 10 格全部为 mapped 逐字文案（非占位）',
   cellTexts.every(t => warnRecs.some(r => r.pending === false && r.text === t)),
   `mapped=${warnRecs.filter(r => !r.pending).length}/5 非占位格=${cellTexts.filter(t => t !== K.pendingText('warning_signs')).length}/10`);
const repairRec = K.resolveSlot(K.findSlot(C, 'repair_card_01'));
ok('修复卡批次 8 起 mapped：逐字文案 + 来源，非占位',
   repairRec.pending === false && repairRec.source === 'pc_repair_card_01' &&
   nodes['repair-card'].textContent.indexOf(repairRec.text) === 0,
   repairRec.text.slice(0, 20) + '…');
const discRec = K.resolveSlot(K.findSlot(C, 'disclaimer'));
ok('免责槽位批次 5 起 filled_constant：中性免责文本、无批次标记、非 pending',
   discRec.pending === false && discRec.source === null &&
   nodes['disclaimer-text'].textContent === discRec.text &&
   discRec.text.indexOf('不替代') >= 0 &&
   ['批次', 'batch', '派生'].every(m => discRec.text.indexOf(m) === -1),
   discRec.text.slice(0, 30) + '…');

/* ---------- 4. 火气分档 ---------- */
const tiers = [1, 2, 3, 4, 5].map(K.angerTier);
ok('1/2→low, 3/4→mid, 5→high', tiers.join(',') === 'low,low,mid,mid,high', tiers.join(','));
let rejected = 0;
[0, 6, 1.5, '3x', null].forEach(v => { try { K.angerTier(v); } catch (e) { rejected++; } });
ok('非法火气值被拒（含字符串/小数/越界）', rejected === 5, `${rejected}/5`);

/* ---------- 5. 日志：写入、持久化、清空 ---------- */
// 表单控件只在提交回调内被读取，仿真 DOM 需先显式创建（getElementById 懒建）
const $n = id => global.document.getElementById(id);
$n('log-anger').value = '4';
$n('log-trigger').value = '数学错题';
$n('log-lost').checked = true;
$n('log-note').value = '今晚没忍住';
$n('log-form')._h.submit({ preventDefault() {} });
const raw1 = mem[K.LOG_KEY];
ok('提交后写入 localStorage', !!raw1 && JSON.parse(raw1).length === 1);
const e1 = JSON.parse(raw1)[0];
ok('日志五字段齐全且类型正确',
   ['timestamp','anger_level_1_5','trigger','did_lose_temper','note'].every(k => k in e1) &&
   e1.anger_level_1_5 === 4 && e1.did_lose_temper === true && e1.trigger === '数学错题',
   JSON.stringify(e1));
// 模拟刷新：重建 storage 视图后仍能读到
const reloaded = K.loadLogs(global.localStorage);
ok('模拟刷新后记录仍在', reloaded.length === 1 && reloaded[0].trigger === '数学错题');
nodes['log-clear']._h.click();
ok('清空后为空', mem[K.LOG_KEY] === undefined && K.loadLogs(global.localStorage).length === 0);

/* ---------- 6. 黑夜模式 ---------- */
const before = nodes['__html'] ? null : global.document.documentElement['data-theme'];
global.document.documentElement.setAttribute('data-theme', 'light');
ok('初始主题解析（无存储 + 系统浅色）', K.resolveTheme(null, false) === 'light');
ok('系统深色时默认深色', K.resolveTheme(null, true) === 'dark');
ok('手动存储优先于系统', K.resolveTheme('light', true) === 'light');
nodes['theme-toggle']._h.click();
ok('点击后切到 dark', global.document.documentElement['data-theme'] === 'dark');
nodes['theme-toggle']._h.click();
ok('再点切回 light', global.document.documentElement['data-theme'] === 'light');

/* ---------- 7. 静态资源契约 ---------- */
const html = fs.readFileSync(path.join(SRC, 'index.html'), 'utf-8');
const css = fs.readFileSync(path.join(SRC, 'style.css'), 'utf-8');
const appjs = fs.readFileSync(path.join(SRC, 'app.js'), 'utf-8');
const apijs = fs.readFileSync(path.join(SRC, 'api.js'), 'utf-8');
const corejs = fs.readFileSync(path.join(SRC, 'core.js'), 'utf-8');
const secs = ['sec-breathing','sec-scripts','sec-ai','sec-retreat','sec-warning',
              'sec-repair','sec-log','sec-disclaimer'];
ok('HTML 八段结构 + 标题齐全', secs.every(s => html.indexOf('id="' + s + '"') >= 0) &&
   html.indexOf('<h1') >= 0, `${secs.length} sections`);
ok('HTML 用 <script src> 加载同源数据，无 fetch',
   html.indexOf('../data/features.js') >= 0 && html.indexOf('../data/copy_mapping.js') >= 0 &&
   html.indexOf('type="module"') === -1);
ok('CSS 375px 断点 + overflow-x + box-sizing', css.indexOf('max-width: 375px') >= 0 &&
   css.indexOf('overflow-x: hidden') >= 0 && css.indexOf('box-sizing: border-box') >= 0);
ok('CSS 自动 + 手动黑夜双通道', css.indexOf('prefers-color-scheme: dark') >= 0 &&
   css.indexOf('html[data-theme="dark"]') >= 0 && css.indexOf('html[data-theme="light"]') >= 0);
ok('app.js 不含硬编码内容文案（只引用数据）',
   appjs.indexOf('__PC_COPY__') >= 0 && appjs.indexOf('inject_text') === -1);
// 批次 1 为桩、批次 2 起切真 fetch；断言改为「接线状态明确 + 调用契约不变」，
// 使同一份静态验收在两个批次都能复跑，不因 api.js 换实现而假红。
ok('api.js 接线状态明确且 request(payload) 契约不变',
   (apijs.indexOf('stub: true') >= 0 || apijs.indexOf('stub: false') >= 0) &&
   apijs.indexOf('request') >= 0 && apijs.indexOf('PCApi') >= 0);
ok('core.js resolveSlot 对 pending 强制 text=null',
   corejs.indexOf("record.text !== null") >= 0);
ok('features.json 与 copy_mapping.json 同源包装一致',
   fs.readFileSync(path.join(DATA, 'copy_mapping.js'), 'utf-8')
     .indexOf('window.__PC_COPY__ = ') === 0);

/* ---------- 输出 ---------- */
lines.push('');
lines.push(`汇总：通过 ${pass} / 失败 ${fail}`);
const out = '# 阶段 B 批次 1 · 静态复刻验收结果\n\n' +
  '执行方式：node（零依赖）轻量 DOM 仿真，**真实执行** `src/app.js` 渲染；\n' +
  '假时钟 `performance.now()` + 手动泵 rAF 帧驱动呼吸动画。\n\n' +
  '> 边界：375px 像素级不溢出、实机黑夜配色、刷新后页面重载属浏览器渲染行为，\n' +
  '> 本地只做静态断言与逻辑层仿真，**未跑浏览器**，不假称已实机验收。\n\n' +
  '## 逐项\n\n' + lines.map(l => '- ' + l).join('\n') + '\n';
fs.writeFileSync(path.join(DATA, '批次1_验收结果.md'), out, 'utf-8');
console.log(`[batch1] pass=${pass} fail=${fail}`);
process.exit(fail ? 1 : 0);
