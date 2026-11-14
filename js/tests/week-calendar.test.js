// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Jose Miguel Hernandez
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const { weeksOfMonth, parseArgs, formatReport, helpText, LABEL } = require('../week-calendar');
const {
  weekdayNames,
  monthNames,
  nameToOrdinal,
  addDays,
  formatDayLong,
  formatDate,
} = require('../utils/date');
const { describe, test } = require('node:test');
const assert = require('node:assert');

const SCRIPT = path.join(__dirname, '..', 'week-calendar.js');
const README = path.join(__dirname, '..', '..', 'README.md');

// Whole outputs, written out by hand from a calendar (not produced by the tool).
const HELP = lines([
  'Usage: node week-calendar.js <year> <month> --anchor <weekday> [--day <weekdays>] [--grid]',
  '',
  'Lists the weeks of one month. Week 1 is the first Sunday-to-Saturday week that contains',
  'the anchor weekday, week 2 is the week after it, and so on; a month has 4 or 5 numbered weeks.',
  '',
  'Arguments:',
  '  <year>      Whole year from 1583 to 9999 (Gregorian calendar)',
  '  <month>     Whole number from 1 (January) to 12 (December)',
  '',
  'Options:',
  '  --anchor    The weekday that week 1 must contain, for example Thursday or Thu (required)',
  '  --day       Also print the date of each of these weekdays in every week,',
  '              for example Monday or Mon,Sat',
  '  --grid      Also print the month as a grid, one row per week',
  '  -h, --help  Show this help',
  '',
  'Spaces around a value or a list item are ignored; a tab or line break is an error.',
  'Each flag is given once. Dates are calendar dates, the same in every time zone.',
]);
const E1 = lines([
  'Weeks of April 2031, numbered from the first week that contains a Thursday',
  'Each week runs Sunday to Saturday.',
  '',
  'Week 1: Sun Mar 30 2031 - Sat Apr 05 2031',
  '  Monday: Mon Mar 31 2031',
  '  Saturday: Sat Apr 05 2031',
  'Week 2: Sun Apr 06 2031 - Sat Apr 12 2031',
  '  Monday: Mon Apr 07 2031',
  '  Saturday: Sat Apr 12 2031',
  'Week 3: Sun Apr 13 2031 - Sat Apr 19 2031',
  '  Monday: Mon Apr 14 2031',
  '  Saturday: Sat Apr 19 2031',
  'Week 4: Sun Apr 20 2031 - Sat Apr 26 2031',
  '  Monday: Mon Apr 21 2031',
  '  Saturday: Sat Apr 26 2031',
  '',
  'April 2031 has 4 Thursdays, so it has 4 numbered weeks.',
  'Days of April 2031 before week 1: none.',
  'Days of April 2031 after week 4: Sun Apr 27 2031 - Wed Apr 30 2031.',
  '',
  'April 2031',
  '       Sun Mon Tue Wed Thu Fri Sat',
  'Week 1           1   2   3   4   5',
  'Week 2   6   7   8   9  10  11  12',
  'Week 3  13  14  15  16  17  18  19',
  'Week 4  20  21  22  23  24  25  26',
  '        27  28  29  30',
]);
const E2 = lines([
  'Weeks of April 2031, numbered from the first week that contains a Monday',
  'Each week runs Sunday to Saturday.',
  '',
  'Week 1: Sun Apr 06 2031 - Sat Apr 12 2031',
  'Week 2: Sun Apr 13 2031 - Sat Apr 19 2031',
  'Week 3: Sun Apr 20 2031 - Sat Apr 26 2031',
  'Week 4: Sun Apr 27 2031 - Sat May 03 2031',
  '',
  'April 2031 has 4 Mondays, so it has 4 numbered weeks.',
  'Days of April 2031 before week 1: Tue Apr 01 2031 - Sat Apr 05 2031.',
  'Days of April 2031 after week 4: none.',
]);
const E3 = lines([
  'Weeks of November 2031, numbered from the first week that contains a Tuesday',
  'Each week runs Sunday to Saturday.',
  '',
  'Week 1: Sun Nov 02 2031 - Sat Nov 08 2031',
  'Week 2: Sun Nov 09 2031 - Sat Nov 15 2031',
  'Week 3: Sun Nov 16 2031 - Sat Nov 22 2031',
  'Week 4: Sun Nov 23 2031 - Sat Nov 29 2031',
  '',
  'November 2031 has 4 Tuesdays, so it has 4 numbered weeks.',
  'Days of November 2031 before week 1: Sat Nov 01 2031.',
  'Days of November 2031 after week 4: Sun Nov 30 2031.',
  '',
  'November 2031',
  '       Sun Mon Tue Wed Thu Fri Sat',
  '                                 1',
  'Week 1   2   3   4   5   6   7   8',
  'Week 2   9  10  11  12  13  14  15',
  'Week 3  16  17  18  19  20  21  22',
  'Week 4  23  24  25  26  27  28  29',
  '        30',
]);
const E4 = lines([
  'Weeks of December 2011, numbered from the first week that contains a Friday',
  'Each week runs Sunday to Saturday.',
  '',
  'Week 1: Sun Nov 27 2011 - Sat Dec 03 2011',
  '  Friday: Fri Dec 02 2011',
  'Week 2: Sun Dec 04 2011 - Sat Dec 10 2011',
  '  Friday: Fri Dec 09 2011',
  'Week 3: Sun Dec 11 2011 - Sat Dec 17 2011',
  '  Friday: Fri Dec 16 2011',
  'Week 4: Sun Dec 18 2011 - Sat Dec 24 2011',
  '  Friday: Fri Dec 23 2011',
  'Week 5: Sun Dec 25 2011 - Sat Dec 31 2011',
  '  Friday: Fri Dec 30 2011',
  '',
  'December 2011 has 5 Fridays, so it has 5 numbered weeks.',
  'Days of December 2011 before week 1: none.',
  'Days of December 2011 after week 5: none.',
]);
const E5 = lines([
  'Weeks of December 9999, numbered from the first week that contains a Friday',
  'Each week runs Sunday to Saturday.',
  '',
  'Week 1: Sun Nov 28 9999 - Sat Dec 04 9999',
  '  Sunday: Sun Nov 28 9999',
  '  Saturday: Sat Dec 04 9999',
  'Week 2: Sun Dec 05 9999 - Sat Dec 11 9999',
  '  Sunday: Sun Dec 05 9999',
  '  Saturday: Sat Dec 11 9999',
  'Week 3: Sun Dec 12 9999 - Sat Dec 18 9999',
  '  Sunday: Sun Dec 12 9999',
  '  Saturday: Sat Dec 18 9999',
  'Week 4: Sun Dec 19 9999 - Sat Dec 25 9999',
  '  Sunday: Sun Dec 19 9999',
  '  Saturday: Sat Dec 25 9999',
  'Week 5: Sun Dec 26 9999 - Sat Jan 01 10000',
  '  Sunday: Sun Dec 26 9999',
  '  Saturday: Sat Jan 01 10000',
  '',
  'December 9999 has 5 Fridays, so it has 5 numbered weeks.',
  'Days of December 9999 before week 1: none.',
  'Days of December 9999 after week 5: none.',
  '',
  'December 9999',
  '       Sun Mon Tue Wed Thu Fri Sat',
  'Week 1               1   2   3   4',
  'Week 2   5   6   7   8   9  10  11',
  'Week 3  12  13  14  15  16  17  18',
  'Week 4  19  20  21  22  23  24  25',
  'Week 5  26  27  28  29  30  31',
]);
const E6 = lines([
  'Weeks of January 1583, numbered from the first week that contains a Saturday',
  'Each week runs Sunday to Saturday.',
  '',
  'Week 1: Sun Dec 26 1582 - Sat Jan 01 1583',
  '  Sunday: Sun Dec 26 1582',
  'Week 2: Sun Jan 02 1583 - Sat Jan 08 1583',
  '  Sunday: Sun Jan 02 1583',
  'Week 3: Sun Jan 09 1583 - Sat Jan 15 1583',
  '  Sunday: Sun Jan 09 1583',
  'Week 4: Sun Jan 16 1583 - Sat Jan 22 1583',
  '  Sunday: Sun Jan 16 1583',
  'Week 5: Sun Jan 23 1583 - Sat Jan 29 1583',
  '  Sunday: Sun Jan 23 1583',
  '',
  'January 1583 has 5 Saturdays, so it has 5 numbered weeks.',
  'Days of January 1583 before week 1: none.',
  'Days of January 1583 after week 5: Sun Jan 30 1583 - Mon Jan 31 1583.',
  '',
  'January 1583',
  '       Sun Mon Tue Wed Thu Fri Sat',
  'Week 1                           1',
  'Week 2   2   3   4   5   6   7   8',
  'Week 3   9  10  11  12  13  14  15',
  'Week 4  16  17  18  19  20  21  22',
  'Week 5  23  24  25  26  27  28  29',
  '        30  31',
]);
const E7 = lines([
  'Weeks of April 2031, numbered from the first week that contains a Thursday',
  'Each week runs Sunday to Saturday.',
  '',
  'Week 1: Sun Mar 30 2031 - Sat Apr 05 2031',
  'Week 2: Sun Apr 06 2031 - Sat Apr 12 2031',
  'Week 3: Sun Apr 13 2031 - Sat Apr 19 2031',
  'Week 4: Sun Apr 20 2031 - Sat Apr 26 2031',
  '',
  'April 2031 has 4 Thursdays, so it has 4 numbered weeks.',
  'Days of April 2031 before week 1: none.',
  'Days of April 2031 after week 4: Sun Apr 27 2031 - Wed Apr 30 2031.',
  '',
  'April 2031',
  '       Sun Mon Tue Wed Thu Fri Sat',
  'Week 1           1   2   3   4   5',
  'Week 2   6   7   8   9  10  11  12',
  'Week 3  13  14  15  16  17  18  19',
  'Week 4  20  21  22  23  24  25  26',
  '        27  28  29  30',
]);

function lines(list) {
  return list.join('\n') + '\n';
}

const E1_ARGS = ['2031', '4', '--anchor', 'Thursday', '--day', 'Monday,Saturday', '--grid'];
const E2_ARGS = ['2031', '4', '--anchor', 'Monday'];
const E3_ARGS = ['2031', '11', '--anchor', 'Tuesday', '--grid'];
const E4_ARGS = ['2011', '12', '--anchor', 'Friday', '--day', 'Friday'];
const E5_ARGS = ['9999', '12', '--anchor', 'Friday', '--day', 'Sunday,Saturday', '--grid'];
const E6_ARGS = ['1583', '1', '--anchor', 'Saturday', '--day', 'Sunday', '--grid'];
const E7_ARGS = ['2031', '4', '--anchor', 'Thursday', '--grid'];

const CASES = [
  ['E1', E1_ARGS, E1],
  ['E2', E2_ARGS, E2],
  ['E3', E3_ARGS, E3],
  ['E4', E4_ARGS, E4],
  ['E5', E5_ARGS, E5],
  ['E6', E6_ARGS, E6],
  ['E7', E7_ARGS, E7],
];

function runTool(args, extraEnv) {
  return spawnSync(process.execPath, [SCRIPT].concat(args), {
    encoding: 'utf8',
    env: Object.assign({}, process.env, extraEnv || {}),
  });
}

function ymd(d) {
  return formatDate(d);
}

describe('week-calendar tables', () => {
  test('weekdayNames and monthNames are exact', () => {
    assert.deepStrictEqual(weekdayNames, [
      'Sunday',
      'Monday',
      'Tuesday',
      'Wednesday',
      'Thursday',
      'Friday',
      'Saturday',
    ]);
    assert.deepStrictEqual(monthNames, [
      'January',
      'February',
      'March',
      'April',
      'May',
      'June',
      'July',
      'August',
      'September',
      'October',
      'November',
      'December',
    ]);
  });

  const NAMES = {
    sunday: 0,
    sun: 0,
    monday: 1,
    mon: 1,
    tuesday: 2,
    tue: 2,
    tues: 2,
    wednesday: 3,
    wed: 3,
    thursday: 4,
    thu: 4,
    thurs: 4,
    friday: 5,
    fri: 5,
    saturday: 6,
    sat: 6,
  };

  test('nameToOrdinal has exactly the 16 names', () => {
    assert.deepStrictEqual(nameToOrdinal, NAMES);
    assert.strictEqual(Object.keys(nameToOrdinal).length, 16);
  });

  for (const [name, ordinal] of Object.entries(NAMES)) {
    test(`--anchor ${name} is ${ordinal}, in any case and with spaces around it`, () => {
      for (const form of [name, name.toUpperCase(), `  ${name} `, name[0].toUpperCase() + name.slice(1)]) {
        const p = parseArgs(['2031', '4', '--anchor', form]);
        assert.strictEqual(p.error, undefined, form);
        assert.strictEqual(p.anchor, ordinal, form);
      }
    });

    test(`--day ${name} is ${ordinal}, in any case and with spaces around it`, () => {
      for (const form of [name, name.toUpperCase(), `  ${name} `]) {
        const p = parseArgs(['2031', '4', '--anchor', 'Thu', '--day', form]);
        assert.strictEqual(p.error, undefined, form);
        assert.deepStrictEqual(p.days, [ordinal], form);
      }
    });
  }
});

describe('weeksOfMonth', () => {
  const starts = (anchor, year = 2031, monthIndex = 3) =>
    weeksOfMonth(year, monthIndex, anchor).map((w) => ymd(w.start));

  // April 2031: the 1st is a Tuesday and the month has 30 days.
  const APRIL_2031 = {
    0: ['2031-04-06', '2031-04-13', '2031-04-20', '2031-04-27'], // Sundays 6, 13, 20, 27
    1: ['2031-04-06', '2031-04-13', '2031-04-20', '2031-04-27'], // Mondays 7, 14, 21, 28
    2: ['2031-03-30', '2031-04-06', '2031-04-13', '2031-04-20', '2031-04-27'], // Tuesdays 1 to 29
    3: ['2031-03-30', '2031-04-06', '2031-04-13', '2031-04-20', '2031-04-27'], // Wednesdays 2 to 30
    4: ['2031-03-30', '2031-04-06', '2031-04-13', '2031-04-20'], // Thursdays 3, 10, 17, 24
    5: ['2031-03-30', '2031-04-06', '2031-04-13', '2031-04-20'], // Fridays 4, 11, 18, 25
    6: ['2031-03-30', '2031-04-06', '2031-04-13', '2031-04-20'], // Saturdays 5, 12, 19, 26
  };

  for (const [anchor, expected] of Object.entries(APRIL_2031)) {
    test(`April 2031 counted from ${weekdayNames[anchor]}`, () => {
      assert.deepStrictEqual(starts(Number(anchor)), expected);
    });
  }

  test('each entry has a week number, a Sunday start and the Saturday six days later, at UTC midnight', () => {
    for (let anchor = 0; anchor < 7; anchor++) {
      const weeks = weeksOfMonth(2031, 3, anchor);
      weeks.forEach((w, i) => {
        assert.strictEqual(w.week, i + 1);
        assert.strictEqual(w.start.getUTCDay(), 0);
        assert.strictEqual(w.start.getTime() % 86400000, 0);
        assert.strictEqual(w.end.getTime(), addDays(w.start, 6).getTime());
        assert.strictEqual(w.end.getUTCDay(), 6);
      });
    }
  });

  test('4 versus 5 weeks: February 2031 has four Saturdays, February 2032 has five Sundays', () => {
    // 1 February 2031 is a Saturday: 1, 8, 15, 22.
    assert.strictEqual(weeksOfMonth(2031, 1, 6).length, 4);
    // 1 February 2032 is a Sunday, and 2032 is a leap year: 1, 8, 15, 22, 29.
    assert.strictEqual(weeksOfMonth(2032, 1, 0).length, 5);
    // The 29th is the one that makes the fifth week; February 2031 has no 29th.
    assert.strictEqual(weeksOfMonth(2031, 1, 0).length, 4);
    assert.strictEqual(ymd(weeksOfMonth(2032, 1, 0)[4].start), '2032-02-29');
  });

  test('the week that holds the first anchor of the next month is not numbered in this one', () => {
    // September 2031, Thursday anchor: Thursdays 4, 11, 18, 25, so four weeks; the week of
    // 28 September to 4 October holds October's first Thursday and is not week 5 of September.
    const weeks = weeksOfMonth(2031, 8, 4);
    assert.strictEqual(weeks.length, 4);
    assert.strictEqual(ymd(weeks[3].start), '2031-09-21');
    // October 2031: its week 1 is that week.
    assert.strictEqual(ymd(weeksOfMonth(2031, 9, 4)[0].start), '2031-09-28');
  });

  test('no month has fewer than 4 or more than 5 weeks', () => {
    for (let m = 0; m < 12; m++) {
      for (let a = 0; a < 7; a++) {
        const n = weeksOfMonth(2031, m, a).length;
        assert.ok(n === 4 || n === 5, `${m} ${a} ${n}`);
      }
    }
  });
});

describe('date helpers', () => {
  test('addDays moves by calendar days in UTC, forwards and backwards', () => {
    assert.strictEqual(ymd(addDays(new Date(Date.UTC(2031, 2, 30)), 4)), '2031-04-03');
    assert.strictEqual(ymd(addDays(new Date(Date.UTC(2031, 0, 1)), -1)), '2030-12-31');
    assert.strictEqual(ymd(addDays(new Date(Date.UTC(2032, 1, 28)), 1)), '2032-02-29');
  });

  test('formatDayLong prints Www Mmm DD YYYY', () => {
    assert.strictEqual(formatDayLong(new Date(Date.UTC(2031, 3, 3))), 'Thu Apr 03 2031');
    assert.strictEqual(formatDayLong(new Date(Date.UTC(2031, 10, 30))), 'Sun Nov 30 2031');
    assert.strictEqual(formatDayLong(new Date(Date.UTC(9999, 11, 32))), 'Sat Jan 01 10000');
    assert.strictEqual(formatDayLong(new Date(Date.UTC(1583, 0, 1))), 'Sat Jan 01 1583');
  });
});

describe('formatReport and a spawned run', () => {
  for (const [name, args, expected] of CASES) {
    test(`${name}: formatReport gives the whole text`, () => {
      const p = parseArgs(args);
      assert.strictEqual(p.error, undefined);
      assert.strictEqual(formatReport(p), expected);
    });

    test(`${name}: a run prints it, the label goes to stderr, status 0`, () => {
      const r = runTool(args);
      assert.strictEqual(r.status, 0);
      assert.strictEqual(r.stdout, expected);
      assert.strictEqual(r.stderr, LABEL + '\n');
    });
  }

  test('LABEL is the label text', () => {
    assert.strictEqual(
      LABEL,
      'Educational; not legal advice; not certified for court filing; consult counsel.'
    );
  });

  test('no line ends in a space', () => {
    for (const [, , expected] of CASES) {
      for (const line of expected.split('\n')) assert.ok(!/ $/.test(line), JSON.stringify(line));
    }
  });
});

describe('flags', () => {
  const base = ['2031', '4', '--anchor', 'Thursday'];

  test('--day off: no weekday lines; on: one line per weekday in every week', () => {
    const off = formatReport(parseArgs(base));
    assert.ok(!/^ {2}/m.test(off));
    const on = formatReport(parseArgs(base.concat(['--day', 'Monday'])));
    assert.strictEqual(on.split('\n').filter((l) => l.startsWith('  Monday: ')).length, 4);
    assert.ok(on.includes('  Monday: Mon Mar 31 2031\n'));
  });

  test('--grid off: no grid; on: the grid follows the last line', () => {
    const off = formatReport(parseArgs(base));
    assert.ok(!off.includes('       Sun Mon Tue Wed Thu Fri Sat'));
    const on = formatReport(parseArgs(base.concat(['--grid'])));
    assert.ok(on.startsWith(off + '\nApril 2031\n       Sun Mon Tue Wed Thu Fri Sat\n'));
  });

  test('--anchor changes week 1', () => {
    assert.ok(formatReport(parseArgs(['2031', '4', '--anchor', 'Monday'])).includes('Week 1: Sun Apr 06 2031'));
    assert.ok(formatReport(parseArgs(base)).includes('Week 1: Sun Mar 30 2031'));
  });

  test('flags before the year and month give the same output as after them', () => {
    const after = runTool(E1_ARGS);
    const before = runTool(['--grid', '--day', 'Monday,Saturday', '--anchor', 'Thursday', '2031', '4']);
    const between = runTool(['2031', '--anchor', 'Thursday', '4', '--grid', '--day', 'Monday,Saturday']);
    assert.strictEqual(before.status, 0);
    assert.strictEqual(before.stdout, after.stdout);
    assert.strictEqual(between.stdout, after.stdout);
  });

  test('--day Saturday,Monday prints Monday first', () => {
    const p = parseArgs(base.concat(['--day', 'Saturday,Monday']));
    assert.deepStrictEqual(p.days, [1, 6]);
    assert.strictEqual(formatReport(p), formatReport(parseArgs(base.concat(['--day', 'Monday,Saturday']))));
    assert.ok(formatReport(p).includes('Week 2: Sun Apr 06 2031 - Sat Apr 12 2031\n  Monday: Mon Apr 07 2031\n  Saturday:'));
  });

  test('--day Sun,Mon,Tue,Wed,Thu,Fri,Sat given backwards prints Sunday first', () => {
    const p = parseArgs(base.concat(['--day', 'sat,fri,thu,wed,tue,mon,sun']));
    assert.deepStrictEqual(p.days, [0, 1, 2, 3, 4, 5, 6]);
  });

  test('--day Mon,monday prints Monday once', () => {
    const p = parseArgs(base.concat(['--day', 'Mon,monday']));
    assert.deepStrictEqual(p.days, [1]);
    const text = formatReport(p);
    assert.strictEqual(text.split('\n').filter((l) => l.startsWith('  Monday: ')).length, 4);
  });

  test('parseArgs returns the settings', () => {
    assert.deepStrictEqual(parseArgs(E1_ARGS), {
      year: 2031,
      month: 4,
      anchor: 4,
      days: [1, 6],
      grid: true,
    });
    assert.deepStrictEqual(parseArgs(base), {
      year: 2031,
      month: 4,
      anchor: 4,
      days: [],
      grid: false,
    });
  });

  test('spaces around the year, the month and the values are ignored; 04 is April', () => {
    const p = parseArgs([' 2031 ', ' 04', '--anchor', ' thu ', '--day', ' mon , sat ']);
    assert.deepStrictEqual(p, { year: 2031, month: 4, anchor: 4, days: [1, 6], grid: false });
  });

  test('a week 1 that starts on the 1st leaves no days before it', () => {
    // 1 June 2031 is a Sunday; Thursdays are 5, 12, 19, 26.
    const text = formatReport(parseArgs(['2031', '6', '--anchor', 'Thursday']));
    assert.ok(text.includes('Week 1: Sun Jun 01 2031 - Sat Jun 07 2031\n'));
    assert.ok(text.includes('Days of June 2031 before week 1: none.\n'));
    assert.ok(text.endsWith('Days of June 2031 after week 4: Sun Jun 29 2031 - Mon Jun 30 2031.\n'));
  });

  test('a month that ends on a Saturday ends its grid on that row', () => {
    // 31 December 2011 is a Saturday; 1 December 2011 is a Thursday.
    const grid = [
      'December 2011',
      '       Sun Mon Tue Wed Thu Fri Sat',
      'Week 1' + ' '.repeat(16) + '   1   2   3',
      'Week 2   4   5   6   7   8   9  10',
      'Week 3  11  12  13  14  15  16  17',
      'Week 4  18  19  20  21  22  23  24',
      'Week 5  25  26  27  28  29  30  31',
    ].join('\n');
    const text = formatReport(parseArgs(['2011', '12', '--anchor', 'Friday', '--grid']));
    assert.ok(text.endsWith('\n\n' + grid + '\n'), text);
  });

  test('a month with a single day in a span prints one date', () => {
    // E3: one day before week 1 and one after week 4
    assert.ok(E3.includes('before week 1: Sat Nov 01 2031.\n'));
    assert.ok(E3.includes('after week 4: Sun Nov 30 2031.\n'));
  });
});

describe('--help', () => {
  test('helpText is the help text', () => {
    assert.strictEqual(helpText(), HELP);
    assert.ok(HELP.endsWith('\n') && !HELP.endsWith('\n\n'));
  });

  for (const args of [
    ['--help'],
    ['-h'],
    ['--bogus', '--help'],
    ['2031', '--anchor', '-h'],
    ['2031', '4', '--anchor', 'Thu', '--anchor', 'Fri', '-h'],
    ['1582', '13', '--help'],
  ]) {
    test(`${args.join(' ')} prints the help, label on stderr, status 0`, () => {
      const r = runTool(args);
      assert.strictEqual(r.status, 0);
      assert.strictEqual(r.stdout, HELP);
      assert.strictEqual(r.stderr, LABEL + '\n');
    });
  }
});

describe('bad input', () => {
  const NAME = 'week-calendar: ';
  const YM = NAME + 'the year and the month are required, in that order; for example, 2031 4 for April 2031.';
  const AN = NAME + 'the anchor weekday is required; give --anchor <name> (for example, --anchor Thursday).';
  const year = (raw) =>
    NAME + `the year must be a whole year from 1583 to 9999 (Gregorian calendar); got ${raw}.`;
  const month = (raw) =>
    NAME + `the month must be a whole number from 1 (January) to 12 (December); got ${raw}.`;
  const anchor = (raw) => NAME + `--anchor takes one weekday name, like Thursday or Thu; got ${raw}.`;
  const unknown = (raw) => NAME + `unknown argument ${raw}.`;

  const TABLE = [
    [[], YM],
    [['2031'], YM],
    [['2031', '4'], AN],
    [['2031', '4', '--anchor'], NAME + '--anchor needs a value.'],
    [['2031', '4', '--anchor', '--grid'], NAME + '--anchor needs a value.'],
    [['2031', '4', '--anchor', 'Thu', '--anchor', 'Fri'], NAME + '--anchor is given more than once.'],
    [['2031', '4', '--anchor', 'Thu', '--grid', '--grid'], NAME + '--grid is given more than once.'],
    [
      ['2031', '4', '--anchor', 'Thu', '--day', 'Mon', '--day', 'Sat'],
      NAME + '--day is given more than once.',
    ],
    [['2031', '4', '--anchor', 'Thu', '--day'], NAME + '--day needs a value.'],
    [['2031', '4', '--anchor', 'Thu', '--list'], unknown('"--list"')],
    [['2031', '4', '--anchor', 'Thu', '-g'], unknown('"-g"')],
    [['2031', '4', '5', '--anchor', 'Thu'], unknown('"5"')],
    [['2031', '4', '--anchor', 'Thu', 'extra'], unknown('"extra"')],
    [['--bogus', '1582', '13'], unknown('"--bogus"')],
    [['1582', '4', '--anchor', 'Thu'], year('"1582"')],
    [['10000', '1', '--anchor', 'Thu'], year('"10000"')],
    [['2031.0', '4', '--anchor', 'Thu'], year('"2031.0"')],
    [['-2031', '4', '--anchor', 'Thu'], unknown('"-2031"')],
    [['abcd', '4', '--anchor', 'Thu'], year('"abcd"')],
    [['1582', '13', '--anchor', 'Thu'], year('"1582"')],
    [['2031', '0', '--anchor', 'Thu'], month('"0"')],
    [['2031', '13', '--anchor', 'Thu'], month('"13"')],
    [['2031', '4.5', '--anchor', 'Thu'], month('"4.5"')],
    [['2031', '\t4', '--anchor', 'Thu'], month('"\\t4"')],
    [['2031', '', '--anchor', 'Thu'], month('""')],
    [['02031', '4', '--anchor', 'Thu'], year('"02031"')],
    [['12345', '4', '--anchor', 'Thu'], year('"12345"')],
    [['2031', '004', '--anchor', 'Thu'], month('"004"')],
    [['2031', '+4', '--anchor', 'Thu'], month('"+4"')],
    [['2031', '4', '--anchor', 'Funday'], anchor('"Funday"')],
    [['2031', '4', '--anchor', 'Thu,Fri'], anchor('"Thu,Fri"')],
    [['2031', '4', '--anchor', '4'], anchor('"4"')],
    [['2031', '4', '--anchor', 'constructor'], anchor('"constructor"')],
    [['2031', '4', '--anchor', '__proto__'], anchor('"__proto__"')],
    [['2031', '4', '--anchor', 'toString'], anchor('"toString"')],
    [['2031', '4', '--anchor', 'hasOwnProperty'], anchor('"hasOwnProperty"')],
    [['2031', '4', '--anchor', '\tThu'], anchor('"\\tThu"')],
    [['2031', '4', '--anchor', ''], anchor('""')],
    [
      ['2031', '4', '--anchor', 'Thu', '--day', 'Mon,Funday,toString'],
      NAME +
        'unknown weekday name "Funday", "toString" in --day "Mon,Funday,toString"; use names like Monday or Mon.',
    ],
    [
      ['2031', '4', '--anchor', 'Thu', '--day', ''],
      NAME + 'unknown weekday name "" in --day ""; use names like Monday or Mon.',
    ],
    [
      ['2031', '4', '--anchor', 'Thu', '--day', 'constructor,__proto__'],
      NAME +
        'unknown weekday name "constructor", "__proto__" in --day "constructor,__proto__"; use names like Monday or Mon.',
    ],
    // order of checks: the first error met, left to right, then year, month, anchor, day
    [['2031', '13', '--anchor', 'Funday', '--day', 'x'], month('"13"')],
    [['2031', '4', '--anchor', 'Funday', '--day', 'x'], anchor('"Funday"')],
    [['--anchor', 'Thu', '--grid', '--grid', '1582', '13'], NAME + '--grid is given more than once.'],
    [['2031', '4', '--day', 'x'], AN],
    [['2031', '4', '--anchor', 'Thu', '--anchor'], NAME + '--anchor is given more than once.'],
    [['2031', '4', '--anchor', 'Thu', '--day', 'Mon', '--bogus'], unknown('"--bogus"')],
    [['2031', '4', '--anchor', 'Thu', '--day', ' Mon ,  \tSat'], NAME + 'unknown weekday name "  \\tSat" in --day " Mon ,  \\tSat"; use names like Monday or Mon.'],
  ];

  TABLE.forEach(([args, message]) => {
    test(`args "${args.join(' ')}"`, () => {
      assert.ok(!message.includes('\n'));
      const r = runTool(args);
      assert.strictEqual(r.status, 1);
      assert.strictEqual(r.stdout, '');
      assert.strictEqual(r.stderr, LABEL + '\n' + message + '\n' + HELP);
      assert.ok(!r.stderr.includes('    at '), 'no stack trace');
      assert.deepStrictEqual(parseArgs(args), { error: message });
    });
  });

  test('a refused run from a directory other than the root works the same', () => {
    const r = spawnSync(process.execPath, [SCRIPT], { encoding: 'utf8', cwd: path.sep });
    assert.strictEqual(r.status, 1);
    assert.strictEqual(r.stdout, '');
  });
});

describe('dates do not depend on the time zone', () => {
  for (const tz of ['Asia/Kolkata', 'Pacific/Apia', 'America/Los_Angeles']) {
    test(`E1 and E4 are byte-equal in ${tz}`, () => {
      const r1 = runTool(E1_ARGS, { TZ: tz });
      assert.strictEqual(r1.status, 0);
      assert.strictEqual(r1.stdout, E1);
      const r4 = runTool(E4_ARGS, { TZ: tz });
      assert.strictEqual(r4.status, 0);
      assert.strictEqual(r4.stdout, E4);
    });
  }

  test('Samoa: the date local time would skip (2011-12-30) is printed in Pacific/Apia', () => {
    const r = runTool(E4_ARGS, { TZ: 'Pacific/Apia' });
    assert.ok(r.stdout.includes('  Friday: Fri Dec 30 2011'), r.stdout);
  });

  test('E5 and E6 (the year bounds) are byte-equal in Pacific/Apia', () => {
    assert.strictEqual(runTool(E5_ARGS, { TZ: 'Pacific/Apia' }).stdout, E5);
    assert.strictEqual(runTool(E6_ARGS, { TZ: 'Pacific/Apia' }).stdout, E6);
  });
});

describe('README', () => {
  const readme = fs.readFileSync(README, 'utf8');
  const start = readme.indexOf('## Numbering the weeks of a month');
  const end = readme.indexOf('\n## ', start + 1);
  const section = readme.slice(start, end);

  test('the section sits between "Counting fifth weeks" and "Licence"', () => {
    const a = readme.indexOf('## Counting fifth weeks');
    const c = readme.indexOf('## Licence');
    assert.ok(a >= 0 && a < start && start < c);
    assert.strictEqual(readme.split('## Numbering the weeks of a month').length, 2);
  });

  test('it contains the E7 command once and the whole E7 output indented four spaces', () => {
    const command = '    node js/week-calendar.js 2031 4 --anchor Thursday --grid';
    assert.strictEqual(section.split(command + '\n').length, 2);
    const indented = E7.split('\n')
      .slice(0, -1)
      .map((l) => (l === '' ? '' : '    ' + l))
      .join('\n');
    assert.ok(section.includes(indented + '\n'), 'the E7 output, indented four spaces');
  });

  test('every flag in the help text appears in the section', () => {
    for (const flag of ['--anchor', '--day', '--grid', '--help']) {
      assert.ok(HELP.includes(flag), flag);
      assert.ok(section.includes(flag), flag);
    }
    assert.ok(section.includes('1583') && section.includes('9999'));
    assert.ok(section.includes('js/week-calendar.js'));
    assert.ok(section.includes(LABEL));
  });
});
