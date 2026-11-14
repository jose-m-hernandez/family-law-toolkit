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
  median,
} = require('../nth-week');
const { formatDate, weekdayNames, nameToOrdinal } = require('../utils/date');
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

  test('formatDate pads the year to four digits', () => {
    assert.strictEqual(formatDate(new Date(Date.UTC(999, 8, 9))), '0999-09-09');
  });

  test('a date that local time would skip (Samoa, 2011-12-30) is still listed', () => {
    const { datesByYear } = listFifthOccurrenceDates(2011, 2011, 5);
    assert.ok(datesByYear[2011].includes('2011-12-30'));
  });

  // These run the tool in a child process with TZ set there, so they pin the promise under
  // whatever zone the test run itself is in (CI runs in UTC).
  const runInZone = (tz, args) =>
    spawnSync(process.execPath, [path.join(__dirname, '..', 'nth-week.js'), ...args], {
      encoding: 'utf8',
      env: { ...process.env, TZ: tz },
    });

  test('Samoa: 2011-12-30 is printed by a run in Pacific/Apia', () => {
    const r = runInZone('Pacific/Apia', ['--weekday', '5', '--start', '2011', '--end', '2011']);
    assert.strictEqual(r.status, 0);
    assert.ok(r.stdout.includes('2011-12-30\n'), r.stdout);
  });

  test('east of UTC: a run in Asia/Kolkata prints 2031-04-29 and not the day before', () => {
    const r = runInZone('Asia/Kolkata', ['--weekday', '2', '--start', '2031', '--end', '2031']);
    assert.strictEqual(r.status, 0);
    assert.ok(r.stdout.includes('2031-04-29\n'), r.stdout);
    assert.ok(!r.stdout.includes('2031-04-28'), r.stdout);
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
    ['--weekday 7', ['--weekday', '7'], '"7"'],
    ['--weekday with a tab in it', ['--weekday', '2\t'], '--weekday takes'],
    ['--weekday with a newline between items', ['--weekday', '2,\n3'], '--weekday takes'],
    ['--anchor with a tab in it', ['--anchor', 'Tue\t'], '--anchor'],
    ['--start with a trailing newline', ['--anchor', 'Tue', '--start', '2031\n', '--end', '2031'], '--start must be a whole year'],
    ['--start with a tab in it', ['--anchor', 'Tue', '--start', '20\t31', '--end', '2031'], '--start must be a whole year'],
    ['--end with a leading newline', ['--anchor', 'Tue', '--start', '2031', '--end', '\n2031'], '--end must be a whole year'],
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

  test('spaces around a value or a list item are ignored', () => {
    const plain = run(['--weekday', '2,3', '--start', '2031', '--end', '2033']);
    const spaced = run(['--weekday', ' 2 , 3 ', '--start', ' 2031 ', '--end', ' 2033 ']);
    assert.strictEqual(spaced.status, 0);
    assert.strictEqual(spaced.stdout, plain.stdout);
    const named = run(['--anchor', ' Tue , Wed ', '--start', '2031', '--end', '2033']);
    assert.strictEqual(named.status, 0);
    assert.strictEqual(named.stdout, plain.stdout);
  });

  test('-h prints the help to stdout and exits 0', () => {
    const result = run(['-h']);
    assert.strictEqual(result.status, 0);
    assert.strictEqual(result.stderr.split('\n')[0], LABEL);
    assert.ok(result.stdout.includes('Usage: node nth-week.js'));
    assert.ok(result.stdout.includes('Spaces around a value'));
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
    // The run may straddle New Year's midnight: accept the year before or after the spawn.
    const before = new Date().getFullYear();
    const result = run(['--anchor', 'Tuesday']);
    const after = new Date().getFullYear();
    const m = /^Range: (\d{4})–(\d{4})$/m.exec(result.stdout);
    assert.ok(m, result.stdout);
    const [start, end] = [Number(m[1]), Number(m[2])];
    assert.strictEqual(end, start + 18);
    assert.ok(start >= before && start <= after, `${start} not in ${before}..${after}`);
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
    assert.ok(out.includes('proleptic Gregorian'));
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

describe('median', () => {
  test('odd length: the middle value, whatever the order', () => {
    assert.strictEqual(median([5, 4, 5]), 5);
    assert.strictEqual(median([4, 5, 5, 4, 5]), 5);
    assert.strictEqual(median([7]), 7);
  });

  test('even length: the mean of the two middle values', () => {
    assert.strictEqual(median([5, 4]), 4.5);
    assert.strictEqual(median([4, 5, 5, 4]), 4.5);
    assert.strictEqual(median([1, 2, 9, 10]), 5.5);
  });

  test('it does not reorder the list it is given', () => {
    const list = [3, 1, 2];
    median(list);
    assert.deepStrictEqual(list, [3, 1, 2]);
  });
});

describe('nth-week output', () => {
  const run = (args) =>
    spawnSync(process.execPath, [path.join(__dirname, '..', 'nth-week.js'), ...args], {
      encoding: 'utf8',
    });

  // Every accepted name and abbreviation, with the weekday number it must mean.
  const NAMES = {
    sunday: 0, sun: 0,
    monday: 1, mon: 1,
    tuesday: 2, tue: 2, tues: 2,
    wednesday: 3, wed: 3,
    thursday: 4, thu: 4, thurs: 4,
    friday: 5, fri: 5,
    saturday: 6, sat: 6,
  };
  const PRINTED = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  test('the weekday tables hold exactly the expected names', () => {
    assert.deepStrictEqual(weekdayNames, PRINTED);
    assert.deepStrictEqual(nameToOrdinal, NAMES);
  });

  for (const [name, num] of Object.entries(NAMES)) {
    test(`--anchor ${name} is weekday ${num}, printed as ${PRINTED[num]}`, () => {
      const result = run(['--anchor', name, '--start', '2031', '--end', '2031']);
      assert.strictEqual(result.status, 0);
      assert.ok(result.stdout.includes(`\n${PRINTED[num]} (${num}) → `), result.stdout);
      const upper = run(['--anchor', name.toUpperCase(), '--start', '2031', '--end', '2031']);
      assert.strictEqual(upper.stdout, result.stdout);
    });
  }

  for (let n = 0; n < 7; n++) {
    test(`--weekday ${n} is printed as ${PRINTED[n]}`, () => {
      const result = run(['--weekday', String(n), '--start', '2031', '--end', '2031']);
      assert.strictEqual(result.status, 0);
      assert.ok(result.stdout.includes(`\n${PRINTED[n]} (${n}) → `), result.stdout);
    });
  }

  test('an even-length range: per-year lines, Range line, total, average and median', () => {
    // Sundays: five months in 2028, four in 2029, so the median is 4.5.
    const result = run(['--anchor', 'Sunday', '--start', '2028', '--end', '2029']);
    assert.strictEqual(result.status, 0);
    assert.strictEqual(
      result.stdout,
      [
        '',
        '5th week counter (weeks numbered from the first week that contains the anchor weekday)',
        'Range: 2028–2029',
        'Definition: Week 1 is the first week that contains a Sunday. A month has a "5th week" if it contains 5 Sundays.',
        'Showing dates and per-year summary.',
        '2028-01-30',
        '2028-04-30',
        '2028-07-30',
        '2028-10-29',
        '2028-12-31',
        'Year 2028: 5 months',
        '2029-04-29',
        '2029-07-29',
        '2029-09-30',
        '2029-12-30',
        'Year 2029: 4 months',
        'Sunday (0) → Months with a 5th week (first week contains Sunday): 9 (between 2028 and 2029).',
        'Summary for Sunday: total months=9, years=2, avg/year=4.50, median/year=4.5, min/year=4, max/year=5',
        '',
      ].join('\n')
    );
  });

  test('an odd-length range: the middle year is the median', () => {
    // Saturdays: 5, 4, 4 months in 2028 to 2030.
    const result = run(['--anchor', 'Saturday', '--start', '2028', '--end', '2030']);
    assert.ok(result.stdout.includes('Year 2028: 5 months\n'));
    assert.ok(result.stdout.includes('Year 2029: 4 months\n'));
    assert.ok(result.stdout.includes('Year 2030: 4 months\n'));
    assert.ok(
      result.stdout.includes(
        'Summary for Saturday: total months=13, years=3, avg/year=4.33, median/year=4, min/year=4, max/year=5'
      )
    );
  });

  test('--end sets the last year; --start and --end can be the same year', () => {
    const result = run(['--anchor', 'Saturday', '--start', '2029', '--end', '2029']);
    assert.ok(result.stdout.includes('Range: 2029–2029\n'));
    assert.ok(result.stdout.includes('years=1,'));
    assert.ok(!result.stdout.includes('Year 2030'));
    const wider = run(['--anchor', 'Saturday', '--start', '2029', '--end', '2030']);
    assert.ok(wider.stdout.includes('Year 2030: 4 months\n'));
    assert.ok(wider.stdout.includes('years=2,'));
  });

  test('two weekdays: both blocks, in the order given, each counted separately', () => {
    const result = run(['--anchor', 'Wednesday,Tuesday', '--start', '2030', '--end', '2031']);
    assert.strictEqual(result.status, 0);
    const out = result.stdout;
    assert.ok(
      out.includes(
        'Definition: Week 1 is the first week that contains a Wednesday and Tuesday. A month has a "5th week" if it contains 5 of the same weekday; each weekday is counted separately.\n'
      )
    );
    const wed = out.indexOf('Wednesday (3) → ');
    const tue = out.indexOf('Tuesday (2) → ');
    assert.ok(wed > 0 && tue > wed, 'Wednesday block comes first, then Tuesday');
    // Wednesday dates come before the Wednesday total line; Tuesday's before its own.
    for (const d of ['2030-01-30', '2030-05-29', '2030-07-31', '2030-10-30', '2031-12-31']) {
      const at = out.indexOf(d);
      assert.ok(at > 0 && at < wed, d);
    }
    for (const d of ['2030-01-29', '2030-04-30', '2031-04-29', '2031-12-30']) {
      const at = out.lastIndexOf(d);
      assert.ok(at > wed && at < tue, d);
    }
    assert.ok(
      out.includes(
        'Summary for Wednesday: total months=9, years=2, avg/year=4.50, median/year=4.5, min/year=4, max/year=5\n'
      )
    );
    assert.ok(
      out.includes(
        'Summary for Tuesday: total months=9, years=2, avg/year=4.50, median/year=4.5, min/year=4, max/year=5\n'
      )
    );
    assert.strictEqual(out.split('Year 2030: ').length - 1, 2);
    assert.ok(out.includes('Wednesday (3) → Months with a 5th week (first week contains Wednesday): 9 (between 2030 and 2031).'));
    assert.ok(out.includes('Tuesday (2) → Months with a 5th week (first week contains Tuesday): 9 (between 2030 and 2031).'));
  });

  test('one weekday gets the singular definition, several get the separate-count wording', () => {
    const one = run(['--anchor', 'Tuesday', '--start', '2031', '--end', '2031']).stdout;
    assert.ok(one.includes('contains a Tuesday. A month has a "5th week" if it contains 5 Tuesdays.\n'));
    assert.ok(!one.includes('counted separately'));
    const many = run(['--weekday', '2,3', '--start', '2031', '--end', '2031']).stdout;
    assert.ok(many.includes('5 of the same weekday; each weekday is counted separately.'));
    assert.ok(!many.includes('same one of'));
    assert.ok(many.includes('contains a Tuesday and Wednesday.'));
  });
});
