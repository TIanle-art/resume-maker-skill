#!/usr/bin/env node
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import vm from 'node:vm';
import { webcrypto } from 'node:crypto';
import { fileURLToPath } from 'node:url';

const skillRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const html = fs.readFileSync(path.join(skillRoot, 'assets', 'application-tracker.html'), 'utf8');
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(scriptMatch, 'tracker must contain one inline script');
const initialization = '      populateStatuses(); populateApplicationTypes(); render();';
assert.ok(scriptMatch[1].includes(initialization), 'test instrumentation point must exist');
const alerts = [];
const context = vm.createContext({
  window: { crypto: webcrypto },
  document: { querySelector: () => ({}) },
  localStorage: {
    getItem: () => null,
    setItem: () => { throw new Error('storage unavailable'); }
  },
  alert: (message) => alerts.push(message),
  confirm: () => true,
  console
});
const instrumented = scriptMatch[1]
  .replace(initialization, `
      globalThis.__trackerTest = {
        recordRowHtml, csvCell, parseMarkdown, buildMarkdown,
        mergeRecords, normalizeRecord, parseBackupValue, persist
      };
      if (false) {
`)
  .replace(/\n    \}\)\(\);\s*$/, '\n      }\n    })();');
vm.runInContext(instrumented, context, { filename: 'application-tracker.inline.js' });
const api = context.__trackerTest;

const sample = `# 投递记录

## 总表

| 公司 | 岗位 | 方向 | 类型 | 城市 | 渠道 | 投递日期 | 简历版本 | 状态 | 下一步与日期 | 薪资信息 | 备注 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 示例\\|科技 | 后端开发 | 软件开发 | 社招 | 郑州 | 内推 | 2026-11-14 09:30 | 定制简历.docx | HR面 | 11 月 20 日二面 | 20k | 第一轮<br>已完成 |

## 各公司备注

### 示例科技
- 已完成一面，保留这段原始备注。

## 更新记录

- 2026-11-14：创建。
`;

test('Markdown 全字段导入并归一状态别名', () => {
  const result = api.parseMarkdown(sample);
  assert.equal(result.records.length, 1);
  assert.equal(result.issues.length, 0);
  const record = result.records[0];
  assert.equal(record.company, '示例|科技');
  assert.equal(record.position, '后端开发');
  assert.equal(record.direction, '软件开发');
  assert.equal(record.type, '社招');
  assert.equal(record.city, '郑州');
  assert.equal(record.channel, '内推');
  assert.equal(record.date, '2026-11-14');
  assert.equal(record.time, '09:30');
  assert.equal(record.resumeVersion, '定制简历.docx');
  assert.equal(record.status, 'HR 面');
  assert.equal(record.next, '11 月 20 日二面');
  assert.equal(record.salary, '20k');
  assert.equal(record.note, '第一轮\n已完成');
});

test('Markdown 导出仅替换总表并可无损往返', () => {
  const first = api.parseMarkdown(sample).records;
  const exported = api.buildMarkdown(first, sample);
  assert.ok(exported.includes('- 已完成一面，保留这段原始备注。'));
  assert.ok(exported.includes('- 2026-11-14：创建。'));
  assert.ok(exported.includes('示例\\|科技'));
  assert.ok(exported.includes('| HR 面 |'));
  assert.ok(exported.includes('| 2026-11-14 09:30 |'));
  const second = api.parseMarkdown(exported);
  assert.equal(second.issues.length, 0);
  assert.equal(second.records.length, 1);
  assert.equal(second.records[0].company, first[0].company);
  assert.equal(second.records[0].note, first[0].note);
  assert.equal(second.records[0].status, first[0].status);
});

test('旧版 11 列 Markdown 与空日期可导入', () => {
  const legacy = `# 投递记录
## 总表
| 公司 | 岗位 | 方向 | 类型 | 城市 | 渠道 | 投递日期 | 简历版本 | 状态 | 下一步与日期 | 薪资信息 |
|---|---|---|---|---|---|---|---|---|---|---|
| 示例公司 | 实习岗 | 软件 | 实习 |  | 官网 |  |  | 待投递 |  |  |
## 各公司备注
## 更新记录
`;
  const result = api.parseMarkdown(legacy);
  assert.equal(result.records.length, 1);
  assert.equal(result.records[0].date, '');
  assert.equal(result.records[0].note, '');
  assert.equal(result.records[0].type, '实习');
});

test('非法状态被逐行报告，不进入有效记录', () => {
  const invalid = sample.replace('| HR面 |', '| 未知阶段 |');
  const result = api.parseMarkdown(invalid);
  assert.equal(result.records.length, 0);
  assert.equal(result.issues.length, 1);
  assert.match(result.issues[0], /进度状态不受支持/);
});

test('记录 ID 与文本进入 HTML 前完整转义', () => {
  const row = api.recordRowHtml(api.normalizeRecord({
    id: 'x" data-injected="yes',
    company: '<img src=x>',
    status: '已投递'
  }));
  assert.ok(!row.includes('data-injected="yes'));
  assert.ok(row.includes('&quot;'));
  assert.ok(row.includes('&lt;img src=x&gt;'));
  assert.ok(!row.includes('<img src=x>'));
});

test('CSV 对公式前缀加安全标记且保留常规文本', () => {
  assert.equal(api.csvCell('=1+1'), '"\'=1+1"');
  assert.equal(api.csvCell('  @SUM(A1)'), '"\'  @SUM(A1)"');
  assert.equal(api.csvCell('2026-11-14'), '"2026-11-14"');
  assert.equal(api.csvCell('说"你好"'), '"说""你好"""');
});

test('合并键区分同公司同岗位的不同城市', () => {
  const a = api.normalizeRecord({ id: 'a', company: '示例公司', position: '后端', city: '郑州', status: '已投递' });
  const b = api.normalizeRecord({ id: 'b', company: '示例公司', position: '后端', city: '北京', status: '已投递' });
  const result = api.mergeRecords([], [a, b]);
  assert.equal(result.added, 2);
  assert.equal(result.records.length, 2);
});

test('新版对象备份和旧版数组备份均兼容', () => {
  const legacy = api.parseBackupValue([{ company: '旧版公司' }]);
  assert.equal(legacy.items.length, 1);
  assert.equal(legacy.markdown, null);
  const current = api.parseBackupValue({ format: 'resume-maker-application-tracker', version: 2, records: [{ company: '新版公司' }], markdown: sample });
  assert.equal(current.items.length, 1);
  assert.equal(current.markdown, sample);
});

test('浏览器存储失败返回 false 并提示，不提交新状态', () => {
  assert.equal(api.persist([], null), false);
  assert.equal(alerts.length, 1);
  assert.match(alerts[0], /现有记录未改变/);
});
