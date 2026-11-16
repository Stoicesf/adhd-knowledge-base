/* parent-cool 复刻 · 批次 1 核心逻辑（纯函数，浏览器 / node 共用）
 * 纪律：不编造文案。pending 槽位一律返回固定占位串；
 *       mapped 槽位逐字返回 copy_mapping.json 的 text（= inject_text）。
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) { module.exports = api; }
  root.PCCore = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  /* 批次 4 · 占位文案中性化：pending 槽位对用户可见的文本不再带批次号。
   * status 仍是 pending_batch3（挂账语义不变），只改显示文本；
   * 分组→中性文本的映射是唯一出口，app.js 不再各自写占位串。 */
  var PENDING_TEXT = '该条内容正在整理中';
  var PENDING_BY_GROUP = {
    script_cards: '该条话术正在整理中',
    retreat_tiers: '该档指引正在整理中',
    repair_card: '修复话术正在整理中',
    warning_signs: '该项信号对照正在整理中',
    disclaimer: '免责声明原文待补'
  };
  var PENDING_BY_SLOT = {
    disclaimer: '免责声明原文待补'
  };
  function pendingText(group, slot) {
    if (slot && PENDING_BY_SLOT[slot]) { return PENDING_BY_SLOT[slot]; }
    return (group && PENDING_BY_GROUP[group]) || PENDING_TEXT;
  }
  var STUB_LINE = 'AI 台词待接线（批次 1 桩，未接模型）';
  var STUB_STEPS = ['…', '…', '…'];
  var DEGRADED_HINT = 'AI 台词暂不可用，可先看下方撤退方案';
  var LOG_KEY = 'parent_cool_emotion_log_v1';
  var THEME_KEY = 'parent_cool_theme_v1';

  /* ---- 呼吸：4-2-6 × 5 回合，时间轴用绝对毫秒，避免累计漂移 ---- */
  function breathingTimeline(features) {
    var b = features.breathing;
    var phases = [
      { key: 'inhale', label: '吸气', seconds: b.inhale, from: 1.0, to: 1.35 },
      { key: 'hold', label: '屏息', seconds: b.hold, from: 1.35, to: 1.35 },
      { key: 'exhale', label: '呼气', seconds: b.exhale, from: 1.35, to: 1.0 }
    ];
    var out = [], t = 0;
    for (var r = 1; r <= b.rounds; r++) {
      for (var i = 0; i < phases.length; i++) {
        var p = phases[i];
        var ms = p.seconds * 1000;
        out.push({
          round: r, phase: p.key, label: p.label,
          startMs: t, endMs: t + ms, durationMs: ms,
          scaleFrom: p.from, scaleTo: p.to
        });
        t += ms;
      }
    }
    return { phases: out, totalMs: t, rounds: b.rounds };
  }

  function breathingStateAt(timeline, elapsedMs) {
    var t = Math.max(0, elapsedMs);
    if (t >= timeline.totalMs) {
      return { done: true, round: timeline.rounds, phase: 'done', label: '完成',
               progress: 1, scale: 1.0, remainingMs: 0 };
    }
    var cur = null;
    for (var i = 0; i < timeline.phases.length; i++) {
      var p = timeline.phases[i];
      if (t >= p.startMs && t < p.endMs) { cur = p; break; }
    }
    if (!cur) { cur = timeline.phases[0]; }
    var prog = (t - cur.startMs) / cur.durationMs;
    if (prog < 0) { prog = 0; }
    if (prog > 1) { prog = 1; }
    return {
      done: false, round: cur.round, phase: cur.phase, label: cur.label,
      progress: prog,
      scale: cur.scaleFrom + (cur.scaleTo - cur.scaleFrom) * prog,
      remainingMs: timeline.totalMs - t
    };
  }

  /* ---- 槽位解析：这是「不编造」的唯一入口 ---- */
  function resolveSlot(record) {
    if (!record) { return { slot: null, text: PENDING_TEXT, pending: true }; }
    if (record.status === 'mapped') {
      if (typeof record.text !== 'string' || !record.text.length) {
        throw new Error('mapped 槽位缺 text：' + record.slot);
      }
      return { slot: record.slot, text: record.text, pending: false,
               source: record.source_entry_id };
    }
    if (record.status === 'pending_batch3') {
      if (record.text !== null || record.source_entry_id !== null) {
        throw new Error('pending 槽位不得携带文案：' + record.slot);
      }
      return { slot: record.slot, text: pendingText(record.group, record.slot),
               pending: true, source: null };
    }
    if (record.status === 'filled_constant') {
      // 批次 5：常量填充槽位（免责）。不是知识库条目，不得携带 source_entry_id；
      // text 由生成器从 server.py 机械提取，非手抄。
      if (typeof record.text !== 'string' || !record.text.length) {
        throw new Error('filled_constant 槽位缺 text：' + record.slot);
      }
      if (record.source_entry_id !== null) {
        throw new Error('filled_constant 槽位不得携带知识库来源：' + record.slot);
      }
      return { slot: record.slot, text: record.text, pending: false, source: null };
    }
    throw new Error('未知 status：' + record.status);
  }

  function groupSlots(copyDoc, group) {
    return (copyDoc.records || []).filter(function (r) { return r.group === group; });
  }

  function findSlot(copyDoc, slot) {
    var rs = (copyDoc.records || []).filter(function (r) { return r.slot === slot; });
    return rs.length ? rs[0] : null;
  }

  /* ---- 火气分档（与批次 2 server.py 同源，测试里双向核对） ---- */
  function angerTier(level) {
    var n = Number(level);
    if (!Number.isInteger(n) || n < 1 || n > 5) {
      throw new Error('anger_level 必须是 1-5 整数：' + level);
    }
    if (n <= 2) { return 'low'; }
    if (n <= 4) { return 'mid'; }
    return 'high';
  }

  /* ---- 日志：storage 可注入，node 下用内存 mock 验收 ---- */
  function loadLogs(storage) {
    try {
      var raw = storage.getItem(LOG_KEY);
      var arr = raw ? JSON.parse(raw) : [];
      return Array.isArray(arr) ? arr : [];
    } catch (e) { return []; }
  }
  function saveLogs(storage, logs) {
    storage.setItem(LOG_KEY, JSON.stringify(logs));
    return logs;
  }
  function appendLog(storage, entry, logs) {
    var cur = logs || loadLogs(storage);
    cur.push(entry);
    return saveLogs(storage, cur);
  }
  function clearLogs(storage) {
    storage.removeItem(LOG_KEY);
    return [];
  }
  function makeLogEntry(form, isoString) {
    var lv = Number(form.anger_level_1_5);
    if (!Number.isInteger(lv) || lv < 1 || lv > 5) {
      throw new Error('火气值须为 1-5 整数');
    }
    var fields = ['timestamp', 'anger_level_1_5', 'trigger', 'did_lose_temper', 'note'];
    var e = {
      timestamp: isoString || new Date().toISOString(),
      anger_level_1_5: lv,
      trigger: String(form.trigger || ''),
      did_lose_temper: Boolean(form.did_lose_temper),
      note: String(form.note || '')
    };
    if (Object.keys(e).length !== fields.length) { throw new Error('日志字段集不符'); }
    return e;
  }

  /* ---- 主题 ---- */
  function resolveTheme(stored, prefersDark) {
    if (stored === 'dark' || stored === 'light') { return stored; }
    return prefersDark ? 'dark' : 'light';
  }
  function toggleTheme(current) { return current === 'dark' ? 'light' : 'dark'; }

  /* ---- AI 区桩（批次 1 遗留，仅作内部兜底；批次 4 起 UI 对 degraded 不渲染 line/steps） ---- */
  function stubResult() {
    return {
      line: STUB_LINE,
      steps: STUB_STEPS.slice(),
      disclaimer: PENDING_BY_GROUP.disclaimer,
      degraded: true,
      blocked: false,
      stub: true,
      hint: DEGRADED_HINT
    };
  }

  return {
    PENDING_TEXT: PENDING_TEXT, PENDING_BY_GROUP: PENDING_BY_GROUP,
    pendingText: pendingText,
    STUB_LINE: STUB_LINE, DEGRADED_HINT: DEGRADED_HINT,
    LOG_KEY: LOG_KEY, THEME_KEY: THEME_KEY,
    breathingTimeline: breathingTimeline, breathingStateAt: breathingStateAt,
    resolveSlot: resolveSlot, groupSlots: groupSlots, findSlot: findSlot,
    angerTier: angerTier,
    loadLogs: loadLogs, saveLogs: saveLogs, appendLog: appendLog,
    clearLogs: clearLogs, makeLogEntry: makeLogEntry,
    resolveTheme: resolveTheme, toggleTheme: toggleTheme,
    stubResult: stubResult
  };
});
