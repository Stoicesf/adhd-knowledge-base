/* 批次 4 · 前端真接线（在批次 2 桥接骨架上收紧，零前端依赖）
 *
 * 调用契约不变：window.PCApi.request(payload) -> Promise<result>，app.js 无需为桩/真服务分叉。
 * 批次 4 变化：
 *   - API_BASE 默认改为绝对地址 http://127.0.0.1:8765（页面从 file:// 直接打开时
 *     相对路径必然落空，绝对 BASE 才是真接线的唯一可选项）；
 *   - 顶层导出 probeHealth()：启动探测入口；
 *   - 3s 硬超时（AbortController + setTimeout，不是 fetch 默认无限等待）；
 *   - degraded（服务不在/超时）与 blocked（guardrail 拦截）仍是两个独立字段，不混用；
 *   - blocked 时 UI 层负责提示文案，本层只保证不把被拦文本/内部错误带回界面。
 * create({fetchImpl, timeoutMs, base}) 可注入 fetch/base，用于 node 验收（test_api.js）。
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) { module.exports = api; }
  root.PCApi = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  var DEFAULT_BASE = 'http://127.0.0.1:8765';
  var DEFAULT_TIMEOUT_MS = 3000;

  function core() {
    var K = (typeof globalThis !== 'undefined') ? globalThis.PCCore : null;
    if (!K) { throw new Error('PCCore 未加载'); }
    return K;
  }

  function create(opts) {
    opts = opts || {};
    var injected = opts.fetchImpl;
    var timeoutMs = opts.timeoutMs || DEFAULT_TIMEOUT_MS;
    var base = String(opts.base !== undefined ? opts.base : DEFAULT_BASE).replace(/\/$/, '');

    function fetcher() {
      if (injected) { return injected; }
      if (typeof fetch === 'function') { return fetch.bind(globalThis); }
      return null;
    }

    function timedFetch(url, init) {
      var f = fetcher();
      if (!f) { return Promise.reject(new Error('no fetch')); }
      var ctl = typeof AbortController !== 'undefined' ? new AbortController() : null;
      var timer = null;
      var timeout = new Promise(function (_, reject) {
        timer = setTimeout(function () {
          if (ctl) { ctl.abort(); }
          reject(new Error('timeout'));
        }, timeoutMs);
      });
      var req = f(url, ctl ? Object.assign({}, init, { signal: ctl.signal }) : init);
      return Promise.race([req, timeout]).then(function (res) {
        if (timer) { clearTimeout(timer); }
        return res;
      }, function (e) {
        if (timer) { clearTimeout(timer); }
        throw e;
      });
    }

    function probeHealth() {
      return timedFetch(base + '/api/health', { method: 'GET', cache: 'no-store' })
        .then(function (res) {
          if (!res || !res.ok) { throw new Error('health not ok'); }
          return true;
        });
    }

    function degraded(reason) {
      var r = core().stubResult();
      // 降级结果的 line/steps 置空：UI 对 degraded 只显示提示，不渲染台词内容
      r.line = null;
      r.steps = [];
      r.degraded = true;
      r.blocked = false;
      r.reason = reason || 'service_unavailable';
      return r;
    }

    function request(payload) {
      var p = Object.assign({ anger_level: 3, situation: '' }, payload || {});
      return probeHealth().then(function () {
        return timedFetch(base + '/api/calm_script', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(p),
          cache: 'no-store'
        });
      }).then(function (res) {
        if (!res || !res.ok) { throw new Error('bad response'); }
        return res.json();
      }).then(function (data) {
        var out = {
          line: typeof data.line === 'string' ? data.line : null,
          steps: Array.isArray(data.steps) ? data.steps : [],
          disclaimer: typeof data.disclaimer === 'string' ? data.disclaimer : '',
          degraded: Boolean(data.degraded),
          blocked: Boolean(data.blocked),
          level: data.level || null,
          hint: data.blocked ? '请先看撤退方案' : (data.hint || ''),
          stub: false,
          reason: data.blocked ? 'guardrail_blocked' : ''
        };
        if (out.blocked) {
          // 服务端本就不返回被拦文本；再兜一层：blocked 时不携带任何台词内容，
          // line/steps 置空，由 UI 层统一提示并高亮撤退方案区。
          out.line = null;
          out.steps = [];
          out.disclaimer = '';
          out.hint = '请先看撤退方案';
        }
        if (out.degraded) {
          out.line = null;
          out.steps = [];
          out.hint = core().DEGRADED_HINT;
        }
        return out;
      }).catch(function () {
        return degraded('service_unavailable_or_timeout');
      });
    }

    return { probe: probeHealth, probeHealth: probeHealth, request: request,
             stub: false, timeoutMs: timeoutMs, base: base };
  }

  return {
    create: create,
    request: function (p) { return create().request(p); },
    probeHealth: function () { return create().probeHealth(); },
    stub: false
  };
});
