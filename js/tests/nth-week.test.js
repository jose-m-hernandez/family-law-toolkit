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
const { formatDate } = require('../utils/date');
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
    assert.strictEqual(formatDate(d), '2031-04-29');
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

describe('dates do not depend on the time zone', () => {
  test('formatDate zero-pads month and day', () => {
    assert.strictEqual(formatDate(new Date(Date.UTC(2031, 0, 5))), '2031-01-05');
    assert.strictEqual(formatDate(new Date(Date.UTC(2031, 11, 30))), '2031-12-30');
  });

  test('a date that local time would skip (Samoa, 2011-12-30) is still listed', () => {
    const { datesByYear } = listFifthOccurrenceDates(2011, 2011, 5);
    assert.ok(datesByYear[2011].includes('2011-12-30'));
  });

  test('the tool prints the same output under two different TZ values', () => {
    const args = ['--anchor', 'Tuesday,Friday', '--start', '2031', '--end', '2033'];
    const outputs = ['Pacific/Kiritimati', 'America/Los_Angeles', 'Europe/London'].map(
      (tz) =>
        spawnSync(process.execPath, [path.join(__dirname, '..', 'nth-week.js'), ...args], {
          encoding: 'utf8',
          env: { ...process.env, TZ: tz },
        })
    );
    for (const r of outputs) assert.strictEqual(r.status, 0);
    assert.ok(outputs[0].stdout.includes('2031-04-29'));
    assert.strictEqual(outputs[1].stdout, outputs[0].stdout);
    assert.strictEqual(outputs[2].stdout, outputs[0].stdout);
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

  test('a run with no anchor weekday fails', () => {
    const result = run(['--start', '2031', '--end', '2031']);
    const lines = result.stderr.split('\n');
    assert.strictEqual(result.status, 1);
    assert.strictEqual(result.stdout, '');
    assert.strictEqual(lines[0], LABEL);
    assert.strictEqual(lines[1], MISSING);
    assert.ok(result.stderr.includes('Usage: node nth-week.js'));
  });

  // Each bad input: [description, args, text the message line must contain]
  const BAD = [
    ['--weekday 9', ['--weekday', '9'], '--weekday takes whole numbers 0'],
    ['--weekday -1', ['--weekday', '-1'], '"-1"'],
    ['--weekday 2.5', ['--weekday', '2.5'], '"2.5"'],
    ['--weekday empty', ['--weekday', ''], '--weekday takes'],
    ['--weekday 0x2', ['--weekday', '0x2'], '"0x2"'],
    ['--weekday 02', ['--weekday', '02'], '"02"'],
    ['--weekday list with a bad item', ['--weekday', '2,9,3'], '"9"'],
    ['--weekday trailing comma', ['--weekday', '2,'], '--weekday takes'],
    ['--weekday letters', ['--weekday', 'abc'], '"abc"'],
    ['unknown anchor name', ['--anchor', 'Funday'], '"Funday"'],
    ['unknown name in a list', ['--anchor', 'Tuesday,Funday,Wed'], '"Funday"'],
    ['prototype key constructor', ['--anchor', 'constructor'], '"constructor"'],
    ['prototype key toString', ['--anchor', 'toString'], '"toString"'],
    ['prototype key __proto__', ['--anchor', '__proto__'], '"__proto__"'],
    ['anchor and weekday together', ['--anchor', 'Tuesday', '--weekday', '3'], 'not both; use one'],
    ['start not a number', ['--anchor', 'Tue', '--start', 'abc'], '--start must be a whole year from 1583 to 9999 (Gregorian calendar); got "abc"'],
    ['start fractional', ['--anchor', 'Tue', '--start', '2031.5'], '"2031.5"'],
    ['start 0x7e0', ['--anchor', 'Tue', '--start', '0x7e0'], '"0x7e0"'],
    ['start 1582', ['--anchor', 'Tue', '--start', '1582', '--end', '1590'], '"1582"'],
    ['start 99', ['--anchor', 'Tue', '--start', '99', '--end', '2000'], '"99"'],
    ['start negative', ['--anchor', 'Tue', '--start', '-5'], '"-5"'],
    ['end 10000', ['--anchor', 'Tue', '--start', '2031', '--end', '10000'], '--end must be a whole year from 1583 to 9999'],
    ['end 200000', ['--anchor', 'Tue', '--start', '2031', '--end', '200000'], '"200000"'],
    ['end Infinity', ['--anchor', 'Tue', '--end', 'Infinity'], '"Infinity"'],
    ['reversed range', ['--anchor', 'Tue', '--start', '2040', '--end', '2031'], '--start 2040 is after --end 2031'],
    ['range over 1000 years', ['--anchor', 'Tue', '--start', '1583', '--end', '2583'], 'is 1001 years; at most 1000 years'],
    ['default end past 9999', ['--anchor', 'Tue', '--start', '9990'], 'default end year (start + 18) is 10008'],
    ['--weekday with no value at the end', ['--weekday'], '--weekday needs a value'],
    ['--anchor with no value at the end', ['--anchor'], '--anchor needs a value'],
    ['--start with no value at the end', ['--anchor', 'Tue', '--start'], '--start needs a value'],
    ['--end with no value at the end', ['--anchor', 'Tue', '--end'], '--end needs a value'],
    ['--weekday followed by a flag', ['--weekday', '--start', '2031'], '--weekday needs a value'],
    ['--start followed by a flag', ['--anchor', 'Tue', '--start', '--end', '2031'], '--start needs a value'],
    ['unknown flag', ['--anchor', 'Tue', '--bogus', '1'], '"--bogus"'],
    ['stray word', ['--anchor', 'Tue', 'Tuesday'], '"Tuesday"'],
    ['a flag given twice', ['--anchor', 'Tue', '--start', '2031', '--start', '2032'], '--start is given more than once'],
  ];
  for (const [name, args, text] of BAD) {
    test(`bad input fails with a message: ${name}`, () => {
      const result = run(args);
      const lines = result.stderr.split('\n');
      assert.strictEqual(result.status, 1);
      assert.strictEqual(result.stdout, '');
      assert.strictEqual(lines[0], LABEL);
      assert.ok(lines[1].startsWith('nth-week: '), lines[1]);
      assert.ok(lines[1].includes(text), lines[1]);
      assert.ok(result.stderr.includes('Usage: node nth-week.js'));
      assert.ok(!result.stderr.includes('    at '), 'no stack trace');
    });
  }

  test('the years 1583 and 9999 and a 1000-year range are accepted', () => {
    assert.strictEqual(run(['--anchor', 'Tue', '--start', '1583', '--end', '1583']).status, 0);
    assert.strictEqual(run(['--anchor', 'Tue', '--start', '9999', '--end', '9999']).status, 0);
    assert.strictEqual(run(['--anchor', 'Tue', '--start', '1583', '--end', '2582']).status, 0);
    assert.strictEqual(run(['--anchor', 'Tue', '--start', '9981']).status, 0);
  });

  test('--start alone ends 18 years later', () => {
    const result = run(['--anchor', 'Tuesday', '--start', '2031']);
    assert.strictEqual(result.status, 0);
    assert.ok(result.stdout.includes('Range: 2031–2049\n'));
    assert.ok(result.stdout.includes('years=19,'));
    assert.ok(result.stdout.includes('Year 2049: '));
    assert.ok(!result.stdout.includes('Year 2050: '));
  });

  test('with no years given the range is this year and 18 years after it', () => {
    const year = new Date().getFullYear();
    const result = run(['--anchor', 'Tuesday']);
    assert.ok(result.stdout.includes(`Range: ${year}–${year + 18}\n`));
  });

  test('a repeated weekday is counted once', () => {
    const once = run(['--anchor', 'Tuesday', '--start', '2031', '--end', '2031']);
    const twice = run(['--anchor', 'Tue,tuesday,TUES', '--start', '2031', '--end', '2031']);
    assert.strictEqual(twice.stdout, once.stdout);
    const nums = run(['--weekday', '2,2', '--start', '2031', '--end', '2031']);
    assert.strictEqual(nums.stdout, once.stdout);
  });

  test('--list and --per-year are accepted and change nothing', () => {
    const base = run(['--anchor', 'Tuesday', '--start', '2031', '--end', '2031']);
    const flagged = run(['--anchor', 'Tuesday', '--list', '--per-year', '--start', '2031', '--end', '2031']);
    assert.strictEqual(flagged.status, 0);
    assert.strictEqual(flagged.stdout, base.stdout);
  });

  test('--help lists every flag the program accepts', () => {
    const out = run(['--help']).stdout;
    for (const flag of ['--anchor', '--weekday', '--start', '--end', '--list', '--per-year', '--help', '-h']) {
      assert.ok(out.includes(flag), flag);
    }
    assert.ok(out.includes('start + 18'));
    assert.ok(out.includes('1583 to 9999'));
  });

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
