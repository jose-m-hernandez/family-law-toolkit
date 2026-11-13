// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Jose Miguel Hernandez
const path = require('path');
const { spawnSync } = require('child_process');
const {
  daysInMonth,
  getFifthOccurrenceDate,
  computeMonthsWithFifth,
  listFifthOccurrenceDates,
  tallyFifthWeeks,
} = require('../nth-week');
const { describe, test } = require('node:test');
const assert = require('node:assert');

describe('nth-week helpers', () => {
  test('daysInMonth handles leap years', () => {
    assert.strictEqual(daysInMonth(2032, 1), 29); // Feb 2032
    assert.strictEqual(daysInMonth(2031, 1), 28); // Feb 2031
  });

  test('getFifthOccurrenceDate finds 5th Tuesday in April 2031', () => {
    // April 2031 has Tuesdays on 1,8,15,22,29 → 5th on 29th
    const d = getFifthOccurrenceDate(2031, 3, 2);
    assert.notStrictEqual(d, null);
    assert.strictEqual(d.toISOString().substring(0, 10), '2031-04-29');
  });

  test('getFifthOccurrenceDate returns null when there is no 5th occurrence', () => {
    // May 2031 Tuesdays: 6,13,20,27 → only 4
    const d = getFifthOccurrenceDate(2031, 4, 2);
    assert.strictEqual(d, null);
  });

  test('computeMonthsWithFifth aggregates distinct months and per-year counts', () => {
    const { total, perYear } = computeMonthsWithFifth(2031, 2031, 2);
    // In 2031, Tuesdays have 4 months with a 5th occurrence (Apr, Jul, Sep, Dec)
    assert.strictEqual(total, 4);
    assert.strictEqual(perYear[2031], 4);
  });

  test('listFifthOccurrenceDates returns ISO dates by year', () => {
    const { datesByYear, total } = listFifthOccurrenceDates(2031, 2031, 2);
    assert.strictEqual(total, 4);
    assert.deepStrictEqual(datesByYear[2031], [
      '2031-04-29',
      '2031-07-29',
      '2031-09-30',
      '2031-12-30',
    ]);
  });

  test('tallyFifthWeeks sums across range', () => {
    const total = tallyFifthWeeks(2031, 2033, 2, { verboseDates: false, perYear: false });
    assert.strictEqual(total, 12); // 4 per year for Tuesdays in 2031-2033
  });
});

describe('nth-week CLI', () => {
  const LABEL = 'Educational; not legal advice; not certified for court filing; consult counsel.';
  const HEADING =
    '5th week counter (weeks numbered from the first week that contains the anchor weekday)';
  const MISSING =
    'nth-week: the anchor weekday is required; give --anchor <name> (for example, --anchor Tuesday) or --weekday <0-6>.';

  const run = (args) =>
    spawnSync(process.execPath, [path.join(__dirname, '..', 'nth-week.js'), ...args], {
      encoding: 'utf8',
    });

  for (const [name, args] of [
    ['a normal run', ['--anchor', 'Tuesday', '--start', '2031', '--end', '2031']],
    ['--help', ['--help']],
  ]) {
    test(`the label is the first stderr line: ${name}`, () => {
      const result = run(args);
      assert.strictEqual(result.status, 0);
      assert.strictEqual(result.stderr.split('\n')[0], LABEL);
    });
  }

  test('stdout does not contain the label', () => {
    const result = run(['--anchor', 'Tuesday', '--start', '2031', '--end', '2031']);
    assert.ok(!result.stdout.includes(LABEL));
    assert.ok(result.stdout.includes('2031-04-29'));
    assert.strictEqual(result.stderr, LABEL + '\n');
  });

  for (const [name, args] of [
    ['no anchor at all', ['--start', '2031', '--end', '2031']],
    ['an unknown anchor name', ['--anchor', 'Funday', '--start', '2031', '--end', '2031']],
  ]) {
    test(`a run with no anchor weekday fails: ${name}`, () => {
      const result = run(args);
      const lines = result.stderr.split('\n');
      assert.strictEqual(result.status, 1);
      assert.strictEqual(result.stdout, '');
      assert.strictEqual(lines[0], LABEL);
      assert.strictEqual(lines[1], MISSING);
      assert.ok(result.stderr.includes('Usage: node nth-week.js'));
    });
  }

  test('the heading names what the counter does', () => {
    const result = run(['--anchor', 'Tuesday', '--start', '2031', '--end', '2031']);
    assert.strictEqual(result.stdout.split('\n')[1], HEADING);
    assert.ok(!result.stdout.toLowerCase().includes('court-style'));
    assert.ok(!result.stdout.toLowerCase().includes('common family court definitions'));
  });

  test('--weekday also satisfies the anchor', () => {
    const byName = run(['--anchor', 'Tuesday', '--start', '2031', '--end', '2031']);
    const byOrdinal = run(['--weekday', '2', '--start', '2031', '--end', '2031']);
    assert.strictEqual(byOrdinal.status, 0);
    assert.strictEqual(byOrdinal.stdout, byName.stdout);
  });
});
