/* 批次 4 · 前端真接线验收（node 零依赖，注入 mock fetch）
 * 覆盖方案 §4d 四条路径：
 *   ① 服务在 → degraded:false / blocked:false，line + steps + disclaimer 透传；
 *   ② 服务不在 / 连接失败 → degraded:true，line/steps 置空不渲染；
 *   ③ mock 返回 blocked:true → blocked 透传、不暴露被拦文本与内部错误；
 *   ④ 超时（30ms 模拟 3s 硬超时路径）→ degraded、AbortController 触发。
 * 另覆盖：health 非 200、服务端 degraded 透传、probeHealth 导出、绝对 BASE、
 *         degraded 与 blocked 字段不混用、静态契约。
 */
'use strict';
const path = require('path');
const fs = require('fs');
require(path.join(__dirname, 'src', 'core.js'));
const K = globalThis.PCCore;
const API = require(path.join(__dirname, 'src', 'api.js'));

let pass = 0, fail = 0;
const lines = [];
function ok(name, cond, detail) {
  if (cond) { pass++; lines.push(`✓ ${name}${detail ? ' — ' + detail : ''}`); }
  else { fail++; lines.push(`✗ ${name}${detail ? ' — ' + detail : ''}`); }
}
function resp(body, status) {
  return Promise.resolve({ ok: (status || 200) >= 200 && (status || 200) < 300,
                           status: status || 200,
                           json: () => Promise.resolve(body) });
}

async function main() {
  /* ① 服务在：先探测 health 再 POST，正常分支 */
  let calls = [], postBody = null;
  const live = API.create({ fetchImpl: (url, init) => {
    calls.push({ url, method: init.method });
    if (url.indexOf('/api/health') >= 0) { return resp({ status: 'ok', version: '0.1' }); }
    postBody = JSON.parse(init.body);
    return resp({ line: '先停一下。', steps: ['合上本子', '等呼吸平', '今晚到这里'],
                  disclaimer: '本工具不替代专业诊断。', degraded: false, blocked: false,
                  level: 'mid', hint: '' });
  }});
  const r1 = await live.request({ anger_level: 3, situation: '孩子又摔笔了' });
  ok('① 先探测 health 再 POST', calls.length === 2 &&
     calls[0].url.endsWith('/api/health') && calls[1].url.endsWith('/api/calm_script') &&
     calls[0].method === 'GET' && calls[1].method === 'POST',
     calls.map(c => c.method + ' ' + c.url.split('/').pop()).join(' → '));
  ok('① degraded:false / blocked:false', r1.degraded === false && r1.blocked === false &&
     r1.stub === false);
  ok('① line + 三步 + disclaimer 透传（disclaimer 不在前端硬编码第二份）',
     r1.line === '先停一下。' && r1.steps.length === 3 &&
     r1.disclaimer === '本工具不替代专业诊断。');
  ok('① POST body 为 JSON 且带 anger_level/situation',
     postBody && postBody.anger_level === 3 && postBody.situation === '孩子又摔笔了',
     JSON.stringify(postBody));

  /* ② 服务不在：降级，不白屏、不带台词内容 */
  const down = API.create({ fetchImpl: () => Promise.reject(new Error('ECONNREFUSED')) });
  const r2 = await down.request({ anger_level: 5 });
  ok('② 服务不在 → degraded:true', r2.degraded === true && r2.reason === 'service_unavailable_or_timeout');
  ok('② degraded 时 line/steps 置空（UI 只显示降级提示）',
     r2.line === null && r2.steps.length === 0, `line=${JSON.stringify(r2.line)}`);
  ok('② degraded:true 且 blocked:false（两字段不混用）',
     r2.degraded === true && r2.blocked === false);

  /* ②' health 非 200 也降级 */
  const badHealth = API.create({ fetchImpl: (url) =>
    url.indexOf('health') >= 0 ? resp({}, 503) : resp({ line: 'x' }) });
  const r3 = await badHealth.request({ anger_level: 1 });
  ok("②' health 非 200 也降级", r3.degraded === true && r3.blocked === false && r3.line === null);

  /* ④ 超时（30ms 模拟 3s 硬超时路径） */
  let aborted = false;
  const slow = API.create({ timeoutMs: 30, fetchImpl: (url, init) => new Promise((_, rej) => {
    if (init.signal) { init.signal.addEventListener('abort', () => { aborted = true; rej(new Error('aborted')); }); }
    setTimeout(() => rej(new Error('too late')), 500);
  }) });
  const r4 = await slow.request({ anger_level: 2 });
  ok('④ 超时返回 degraded、不悬挂', r4.degraded === true && r4.line === null &&
     r4.reason === 'service_unavailable_or_timeout');
  ok('④ 超时触发 AbortController.abort', aborted === true);

  /* ③ mock 返回 blocked:true：透传 flag、不暴露被拦文本/内部错误 */
  const blocked = API.create({ fetchImpl: (url) => url.indexOf('health') >= 0
    ? resp({ status: 'ok' })
    : resp({ line: '你就是ADHD', steps: ['吃药', '加量', '停药'],
             disclaimer: 'D', degraded: false, blocked: true, hint: '内部错误' }) });
  const r5 = await blocked.request({ anger_level: 4 });
  const dump = JSON.stringify(r5);
  ok('③ blocked:true 原样透传且 degraded:false', r5.blocked === true && r5.degraded === false);
  ok('③ 不暴露被拦文本 / 内部错误',
     dump.indexOf('你就是ADHD') === -1 && dump.indexOf('吃药') === -1 &&
     dump.indexOf('加量') === -1 && dump.indexOf('内部错误') === -1, dump.slice(0, 120));
  ok('③ blocked 时 line/steps 置空（UI 分支只显示统一提示）',
     r5.line === null && r5.steps.length === 0 && r5.disclaimer === '');
  ok('③ blocked 统一提示「请先看撤退方案」', r5.hint === '请先看撤退方案');

  /* 服务端 degraded 透传（预期态：条目被移除等，不是失败） */
  const serverDegraded = API.create({ fetchImpl: (url) => url.indexOf('health') >= 0
    ? resp({ status: 'ok' })
    : resp({ line: '占位', steps: ['占位', '占位', '占位'],
             disclaimer: 'D', degraded: true, blocked: false, level: 'high',
             hint: K.DEGRADED_HINT }) });
  const r6 = await serverDegraded.request({ anger_level: 5 });
  ok('服务端 degraded 透传（预期态，不是失败）',
     r6.degraded === true && r6.blocked === false && r6.hint === K.DEGRADED_HINT &&
     r6.line === null && r6.steps.length === 0);

  /* probeHealth 导出 + 契约 */
  ok('probeHealth 可独立调用（服务在 → true）',
     await API.create({ fetchImpl: (url) => resp({ status: 'ok' }) }).probeHealth() === true);
  let probeDown = false;
  try { await API.create({ fetchImpl: () => Promise.reject(new Error('x')) }).probeHealth(); }
  catch (e) { probeDown = true; }
  ok('probeHealth 服务不在 → reject（不吞错）', probeDown === true);

  /* 静态契约 */
  const src = fs.readFileSync(path.join(__dirname, 'src', 'api.js'), 'utf-8');
  ok('API_BASE 为绝对地址 http://127.0.0.1:8765（file:// 直开页面真接线的唯一选项）',
     src.indexOf("http://127.0.0.1:8765") >= 0);
  ok('默认超时 3000ms（硬超时，非 fetch 无限等待）', src.indexOf('3000') >= 0);
  ok('api.js 不再标记桩（stub: false）', src.indexOf('stub: false') >= 0);
  ok('api.js 不硬编码业务文案', src.indexOf('inject_text') === -1 &&
     dump.indexOf('先停一下') === -1);

  lines.push('');
  lines.push(`汇总：通过 ${pass} / 失败 ${fail}`);
  const out = '# 阶段 B 批次 4 · 前端真接线验收结果\n\n' +
    '执行方式：node（零依赖）注入 mock `fetch`，覆盖方案 §4d 四条路径：\n' +
    '服务在（degraded:false/blocked:false）→ 真实 line/steps/disclaimer、服务不在 → degraded:true、\n' +
    'mock blocked:true → 统一提示且不暴露被拦文本、超时（30ms 模拟 3s 硬超时）→ degraded + abort；\n' +
    '另覆盖 health 非 200、服务端 degraded 透传、probeHealth 导出、绝对 BASE 与静态契约。\n\n' +
    '## 逐项\n\n' + lines.map(l => '- ' + l).join('\n') + '\n';
  fs.writeFileSync(path.join(__dirname, 'data', '批次4_前端接线验收.md'), out, 'utf-8');
  console.log(`[batch4-api] pass=${pass} fail=${fail}`);
  process.exit(fail ? 1 : 0);
}
main().catch(e => { console.error(e); process.exit(1); });
