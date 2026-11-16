/* 批次 4 · DOM 绑定与渲染。
 * 静态内容文案只来自 window.__PC_COPY__（由 data/copy_mapping.json 机械包装）；
 * pending 槽位占位统一由 PCCore.resolveSlot 按分组返回中性文本，本文件不写占位常量；
 * AI 区走 api.js 真 fetch，degraded / blocked / 正常三分支分开渲染。
 */
(function () {
  'use strict';
  var F = window.__PC_FEATURES__, C = window.__PC_COPY__, K = window.PCCore;
  var $ = function (id) { return document.getElementById(id); };
  var el = function (tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) { n.className = cls; }
    if (text !== undefined && text !== null) { n.textContent = text; }
    return n;
  };

  if (!F || !C || !K) {
    document.body.appendChild(el('p', null, '数据文件未加载：请在完整目录中打开本页。'));
    return;
  }

  /* ---- 主题：自动 + 手动覆盖 ---- */
  var prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  var storedTheme = null;
  try { storedTheme = localStorage.getItem(K.THEME_KEY); } catch (e) { storedTheme = null; }
  var theme = K.resolveTheme(storedTheme, prefersDark);
  function applyTheme() {
    document.documentElement.setAttribute('data-theme', theme);
    $('theme-toggle').textContent = theme === 'dark' ? '切换为浅色' : '切换为深色';
  }
  applyTheme();
  $('theme-toggle').addEventListener('click', function () {
    theme = K.toggleTheme(theme);
    try { localStorage.setItem(K.THEME_KEY, theme); } catch (e) { /* 隐私模式下忽略 */ }
    applyTheme();
  });

  /* ---- 呼吸：rAF 用 performance.now() 绝对时差，不累加帧间隔，避免漂移 ---- */
  var timeline = K.breathingTimeline(F);
  $('breathing-spec').textContent = '吸气 ' + F.breathing.inhale + ' 秒 · 屏息 ' +
    F.breathing.hold + ' 秒 · 呼气 ' + F.breathing.exhale + ' 秒，共 ' + F.breathing.rounds + ' 回合';
  var rafId = null, startAt = 0;
  function frame(now) {
    var st = K.breathingStateAt(timeline, now - startAt);
    $('breath-circle').style.transform = 'scale(' + st.scale.toFixed(4) + ')';
    $('breath-label').textContent = st.done ? '完成' :
      (st.label + ' · 第 ' + st.round + ' / ' + timeline.rounds + ' 回合');
    $('breath-progress').textContent = st.done ? (timeline.rounds + ' / ' + timeline.rounds + ' 回合 · 已完成') :
      ((st.round - 1) + ' / ' + timeline.rounds + ' 回合');
    if (st.done) {
      $('breath-start').disabled = false;
      $('breath-start').textContent = '再来一次';
      rafId = null;
      return;
    }
    rafId = requestAnimationFrame(frame);
  }
  $('breath-start').addEventListener('click', function () {
    if (rafId !== null) { cancelAnimationFrame(rafId); rafId = null; }
    $('breath-start').disabled = true;
    startAt = performance.now();
    rafId = requestAnimationFrame(frame);
  });

  /* ---- 话术卡轮播 ---- */
  var cards = K.groupSlots(C, 'script_cards').map(K.resolveSlot);
  var cardIdx = 0;
  function renderCard() {
    var box = $('script-card');
    box.textContent = '';
    var cur = cards[cardIdx];
    box.className = cur.pending ? 'script-card pending' : 'script-card';
    box.appendChild(el('div', null, cur.text));
    box.appendChild(el('span', 'script-source',
      cur.pending ? '来源：整理中' : ('来源：' + cur.source)));
    $('script-counter').textContent = '第 ' + (cardIdx + 1) + ' / ' + cards.length + ' 张';
  }
  if (!cards.length) { $('script-card').textContent = K.PENDING_TEXT; }
  else { renderCard(); }
  $('script-prev').addEventListener('click', function () {
    if (!cards.length) { return; }
    cardIdx = (cardIdx - 1 + cards.length) % cards.length; renderCard();
  });
  $('script-next').addEventListener('click', function () {
    if (!cards.length) { return; }
    cardIdx = (cardIdx + 1) % cards.length; renderCard();
  });

  /* ---- 三级撤退 ---- */
  var retreatBox = $('retreat-list');
  F.retreat_tiers.forEach(function (tier) {
    var rec = K.resolveSlot(K.findSlot(C, tier.slot));
    var d = el('details', 'retreat-item');
    d.appendChild(el('summary', null, '火气 ' + tier.level + ' 分'));
    var body = el('div', 'retreat-body');
    body.appendChild(rec.pending ? el('div', 'pending-slot', rec.text)
                                : el('div', 'script-card', rec.text));
    if (!rec.pending) { body.appendChild(el('span', 'script-source', '来源：' + rec.source)); }
    d.appendChild(body);
    retreatBox.appendChild(d);
  });

  /* ---- 五类预警表（两列全部由 copy_mapping 决定，pending 显示占位） ---- */
  var table = $('warning-table');
  var thead = el('thead'), htr = el('tr');
  htr.appendChild(el('th', null, '部位'));
  F.warning_signs.columns.forEach(function (c) { htr.appendChild(el('th', null, c)); });
  thead.appendChild(htr); table.appendChild(thead);
  var tbody = el('tbody');
  F.warning_signs.categories.forEach(function (cat) {
    var rec = K.resolveSlot(K.findSlot(C, 'warning_signs_' + cat));
    var tr = el('tr');
    tr.appendChild(el('td', null, cat));
    F.warning_signs.columns.forEach(function () {
      var td = el('td');
      td.appendChild(rec.pending ? el('span', 'pending-slot', rec.text)
                                : el('span', null, rec.text));
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);

  /* ---- 修复话术 ---- */
  var repair = K.resolveSlot(K.findSlot(C, 'repair_card_01'));
  var repairBox = $('repair-card');
  repairBox.className = repair.pending ? 'script-card pending' : 'script-card';
  repairBox.textContent = repair.text;
  if (!repair.pending) {
    repairBox.appendChild(el('span', 'script-source', '来源：' + repair.source));
  }

  /* ---- 免责声明（pending 时显示中性占位：免责声明原文待补） ---- */
  var disc = K.resolveSlot(K.findSlot(C, 'disclaimer'));
  $('disclaimer-text').textContent = disc.text;

  /* ---- 火气值下拉（两处共用同一档位表） ---- */
  ['ai-anger', 'log-anger'].forEach(function (id) {
    var sel = $(id);
    F.ai_line.anger_level.forEach(function (n) {
      var o = el('option', null, String(n)); o.value = String(n); sel.appendChild(o);
    });
  });

  /* ---- 日志 ---- */
  function renderLogs() {
    var logs = K.loadLogs(localStorage);
    var list = $('log-list'); list.textContent = '';
    logs.slice().reverse().forEach(function (e) {
      var li = el('li');
      li.textContent = e.timestamp + ' · 火气 ' + e.anger_level_1_5 +
        ' · ' + (e.trigger || '（未填场景）') +
        (e.did_lose_temper ? ' · 发火了' : ' · 没发火') +
        (e.note ? ' · ' + e.note : '');
      list.appendChild(li);
    });
    $('log-count').textContent = '共 ' + logs.length + ' 条记录（保存在本机浏览器）';
  }
  $('log-form').addEventListener('submit', function (ev) {
    ev.preventDefault();
    try {
      var entry = K.makeLogEntry({
        anger_level_1_5: $('log-anger').value,
        trigger: $('log-trigger').value,
        did_lose_temper: $('log-lost').checked,
        note: $('log-note').value
      });
      K.appendLog(localStorage, entry);
      $('log-trigger').value = ''; $('log-note').value = ''; $('log-lost').checked = false;
      renderLogs();
    } catch (e) { $('log-count').textContent = e.message; }
  });
  $('log-clear').addEventListener('click', function () {
    K.clearLogs(localStorage); renderLogs();
  });
  renderLogs();

  /* ---- AI 区：批次 4 真接线。degraded / blocked / 正常三分支分开渲染，不共用提示条。 ---- */
  var AI_DEGRADED_TEXT = 'AI 台词暂不可用（服务未启动），可先看下方撤退方案';
  var AI_BLOCKED_TEXT = '当前台词未通过安全检查，请先看下方撤退方案';
  var AI_RETRY_MS = 3000;

  function setRetreatHighlight(on) {
    // mkNode 仿真与真实 DOM 都走 className，避免依赖 classList
    $('sec-retreat').className = on ? 'card retreat-highlight' : 'card';
  }
  function renderResult(res) {
    var out = $('ai-output'); out.textContent = '';
    setRetreatHighlight(false);
    if (res.blocked) {
      // blocked：line/steps 不渲染，只出统一提示并高亮撤退方案区
      out.appendChild(el('div', 'ai-note blocked-note', AI_BLOCKED_TEXT));
      setRetreatHighlight(true);
      return;
    }
    if (res.degraded) {
      // degraded：AI 区只显示降级提示，line/steps 不渲染（服务端占位串不上界面）
      out.textContent = '';
      return;
    }
    if (res.line) { out.appendChild(el('div', 'ai-line', res.line)); }
    if (res.steps && res.steps.length) {
      var ol = el('ol', 'ai-steps');
      res.steps.forEach(function (s) { ol.appendChild(el('li', null, s)); });
      out.appendChild(ol);
    }
    if (res.disclaimer) {
      // disclaimer 只来自服务端返回字段，前端不硬编码第二份
      out.appendChild(el('div', 'ai-disclaimer', res.disclaimer));
    }
  }
  var aiBtn = $('ai-submit');
  function aiReset(label) {
    aiBtn.disabled = false;
    aiBtn.textContent = label;
  }
  aiBtn.addEventListener('click', function () {
    aiBtn.disabled = true;
    aiBtn.textContent = '生成中…';            // loading 态直到 fetch resolve/reject
    $('ai-status').textContent = '';
    window.PCApi.request({
      anger_level: Number($('ai-anger').value),
      situation: $('ai-situation').value
    }).then(function (res) {
      renderResult(res);
      if (res.degraded) {
        // 降级：按钮置灰 3 秒后恢复可重试
        $('ai-status').textContent = AI_DEGRADED_TEXT;
        setTimeout(function () { aiReset('再试一次'); }, AI_RETRY_MS);
      } else if (res.blocked) {
        $('ai-status').textContent = '';
        aiReset('给我一句话');
      } else {
        $('ai-status').textContent = res.stub ? '当前为静态演示，未接本地服务' : '';
        aiReset('给我一句话');
      }
    }).catch(function () {
      $('ai-status').textContent = AI_DEGRADED_TEXT;
      renderResult(K.stubResult());
      setTimeout(function () { aiReset('再试一次'); }, AI_RETRY_MS);
    });
  });
})();
