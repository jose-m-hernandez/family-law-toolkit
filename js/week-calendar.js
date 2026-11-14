// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Jose Miguel Hernandez
/**
 * Week Calendar (the weeks of one month, numbered from the first week that contains the anchor weekday)
 *
 * Purpose
 * - List the numbered weeks of one month, with each week's dates, so that "the second week" or
 *   "weeks 1 and 3" can be read off as dates once the anchor weekday is chosen.
 *
 * Definition
 * - Every week runs Sunday to Saturday.
 * - Week 1 is the week that contains the month's first anchor weekday (for example, the first
 *   Thursday); week N is the week that contains the month's N-th anchor weekday.
 * - A month has as many numbered weeks as it has of the anchor weekday: 4 or 5. This matches the
 *   "fifth week" of js/nth-week.js.
 * - Week 1 can start in the month before, and the last week can end in the month after. Days of
 *   the month before week 1 or after the last week belong to no numbered week; they are listed.
 *
 * Input rules (a run that breaks one prints a message and the usage to stderr, prints nothing to
 * stdout, and exits 1)
 * - The year is a whole number from 1583 to 9999 and the month a whole number from 1 (January)
 *   to 12 (December). All dates use today's Gregorian calendar rules, also for years before a
 *   country adopted it (the proleptic Gregorian calendar).
 * - --anchor is required and takes one weekday name, full or short, in any case.
 * - --day takes weekday names, comma-separated; a weekday given twice is printed once, and the
 *   weekdays print Sunday first whatever order they were given in.
 * - Spaces around a value or a list item are ignored; a tab or line break is an error.
 * - Every flag is given once; --anchor and --day need a value. An unknown flag or a stray word is
 *   an error.
 * - Dates are calendar dates, printed the same in every time zone.
 *
 * CLI
 * - <year> <month>        The month to list, in that order (flags may come before or after them)
 * - --anchor <weekday>    The weekday that week 1 must contain. Required. Example: --anchor Thursday
 * - --day <weekdays>      Also print the date of each of these weekdays in every week
 * - --grid                Also print the month as a grid, one row per week
 * - -h, --help            Show usage help
 *
 * Usage Examples
 *   node js/week-calendar.js 2031 4 --anchor Thursday
 *   node js/week-calendar.js 2031 4 --anchor Thursday --day Monday,Saturday
 *   node js/week-calendar.js 2031 4 --anchor Thursday --grid
 */

const {
  weekdayNames,
  monthNames,
  nameToOrdinal,
  daysInMonth,
  getNthOccurrenceDate,
  addDays,
  formatDayLong,
} = require('./utils/date');

const LABEL = 'Educational; not legal advice; not certified for court filing; consult counsel.';

const MIN_YEAR = 1583;
const MAX_YEAR = 9999;

const NAME = 'week-calendar';
const MISSING_YEAR_MONTH = `${NAME}: the year and the month are required, in that order; for example, 2031 4 for April 2031.`;
const MISSING_ANCHOR = `${NAME}: the anchor weekday is required; give --anchor <name> (for example, --anchor Thursday).`;

/**
 * CLI usage help text. Ends in one line break.
 * @returns {string}
 */
function helpText() {
  return `Usage: node week-calendar.js <year> <month> --anchor <weekday> [--day <weekdays>] [--grid]

Lists the weeks of one month. Week 1 is the first Sunday-to-Saturday week that contains
the anchor weekday, week 2 is the week after it, and so on; a month has 4 or 5 numbered weeks.

Arguments:
  <year>      Whole year from ${MIN_YEAR} to ${MAX_YEAR} (Gregorian calendar)
  <month>     Whole number from 1 (January) to 12 (December)

Options:
  --anchor    The weekday that week 1 must contain, for example Thursday or Thu (required)
  --day       Also print the date of each of these weekdays in every week,
              for example Monday or Mon,Sat
  --grid      Also print the month as a grid, one row per week
  -h, --help  Show this help

Spaces around a value or a list item are ignored; a tab or line break is an error.
Each flag is given once. Dates are calendar dates, the same in every time zone.
`;
}

/**
 * Remove plain spaces from both ends. Tabs and line breaks are kept, so they fail the checks.
 * @param {string} text
 * @returns {string}
 */
function trimSpaces(text) {
  return text.replace(/^ +| +$/g, '');
}

/**
 * Look a weekday name up in nameToOrdinal (own keys only).
 * @param {string} item
 * @returns {number | undefined} The ordinal 0 (Sunday) to 6, or undefined when not a name.
 */
function weekdayOrdinal(item) {
  const key = trimSpaces(item).toLowerCase();
  return Object.hasOwn(nameToOrdinal, key) ? nameToOrdinal[key] : undefined;
}

/**
 * The numbered weeks of a month.
 * @param {number} year
 * @param {number} monthIndex 0 (January) to 11 (December)
 * @param {number} anchorOrdinal 0 (Sunday) to 6 (Saturday)
 * @returns {{ week: number, start: Date, end: Date }[]} 4 or 5 weeks; Dates at UTC midnight,
 *   start a Sunday and end the Saturday six days later.
 */
function weeksOfMonth(year, monthIndex, anchorOrdinal) {
  const weeks = [];
  for (let n = 1; ; n++) {
    const anchorDate = getNthOccurrenceDate(year, monthIndex, anchorOrdinal, n);
    if (anchorDate === null) break;
    const start = addDays(anchorDate, -anchorDate.getUTCDay());
    weeks.push({ week: n, start, end: addDays(start, 6) });
  }
  return weeks;
}

/**
 * Parse the command-line arguments. Returns an error message, or the settings to run with.
 * @param {string[]} args Arguments after the script path.
 * @returns {{ error: string } | { year: number, month: number, anchor: number, days: number[], grid: boolean }}
 */
function parseArgs(args) {
  const given = {};
  let grid = false;
  const words = [];
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === '--grid') {
      if (grid) return { error: `${NAME}: --grid is given more than once.` };
      grid = true;
    } else if (a === '--anchor' || a === '--day') {
      if (Object.hasOwn(given, a)) return { error: `${NAME}: ${a} is given more than once.` };
      const v = args[i + 1];
      if (v === undefined || v.startsWith('--')) return { error: `${NAME}: ${a} needs a value.` };
      given[a] = v;
      i++;
    } else if (a.startsWith('-') || words.length === 2) {
      return { error: `${NAME}: unknown argument ${JSON.stringify(a)}.` };
    } else {
      words.push(a);
    }
  }
  if (words.length < 2) return { error: MISSING_YEAR_MONTH };

  const yearText = trimSpaces(words[0]);
  const year = /^[0-9]{4}$/.test(yearText) ? Number(yearText) : NaN;
  if (!(year >= MIN_YEAR && year <= MAX_YEAR)) {
    return {
      error: `${NAME}: the year must be a whole year from ${MIN_YEAR} to ${MAX_YEAR} (Gregorian calendar); got ${JSON.stringify(words[0])}.`,
    };
  }
  const monthText = trimSpaces(words[1]);
  const month = /^[0-9]{1,2}$/.test(monthText) ? Number(monthText) : NaN;
  if (!(month >= 1 && month <= 12)) {
    return {
      error: `${NAME}: the month must be a whole number from 1 (January) to 12 (December); got ${JSON.stringify(words[1])}.`,
    };
  }

  if (!Object.hasOwn(given, '--anchor')) return { error: MISSING_ANCHOR };
  const anchor = weekdayOrdinal(given['--anchor']);
  if (anchor === undefined) {
    return {
      error: `${NAME}: --anchor takes one weekday name, like Thursday or Thu; got ${JSON.stringify(given['--anchor'])}.`,
    };
  }

  const days = [];
  if (Object.hasOwn(given, '--day')) {
    const bad = [];
    for (const item of given['--day'].split(',')) {
      const ordinal = weekdayOrdinal(item);
      if (ordinal === undefined) bad.push(item);
      else if (!days.includes(ordinal)) days.push(ordinal);
    }
    if (bad.length > 0) {
      return {
        error: `${NAME}: unknown weekday name ${bad.map((b) => JSON.stringify(b)).join(', ')} in --day ${JSON.stringify(given['--day'])}; use names like Monday or Mon.`,
      };
    }
    days.sort((a, b) => a - b);
  }

  return { year, month, anchor, days, grid };
}

/**
 * Describe a run of days: `none`, one date, or `first - last`.
 * @param {Date | null} first
 * @param {Date | null} last
 * @returns {string}
 */
function formatSpan(first, last) {
  if (first === null) return 'none';
  if (first.getTime() === last.getTime()) return formatDayLong(first);
  return `${formatDayLong(first)} - ${formatDayLong(last)}`;
}

/**
 * The month as a grid: one row per Sunday-to-Saturday row, from the row that holds the 1st to the
 * row that holds the last day. A row that starts a numbered week is labelled with it.
 * @param {number} year
 * @param {number} monthIndex
 * @param {{ week: number, start: Date, end: Date }[]} weeks
 * @returns {string[]} Lines, without trailing spaces.
 */
function gridLines(year, monthIndex, weeks) {
  const lines = [`${monthNames[monthIndex]} ${year}`];
  lines.push(
    '      ' +
      weekdayNames.map((n) => ` ${n.slice(0, 3)}`).join('')
  );
  const firstDay = new Date(Date.UTC(year, monthIndex, 1));
  const total = daysInMonth(year, monthIndex);
  let rowStart = addDays(firstDay, -firstDay.getUTCDay());
  for (;;) {
    const match = weeks.find((w) => w.start.getTime() === rowStart.getTime());
    let line = match ? `Week ${match.week}` : '      ';
    for (let i = 0; i < 7; i++) {
      const cell = addDays(rowStart, i);
      const inMonth = cell.getUTCMonth() === monthIndex && cell.getUTCFullYear() === year;
      line += inMonth ? String(cell.getUTCDate()).padStart(4, ' ') : '    ';
    }
    lines.push(line.replace(/ +$/, ''));
    if (addDays(rowStart, 6).getTime() >= Date.UTC(year, monthIndex, total)) break;
    rowStart = addDays(rowStart, 7);
  }
  return lines;
}

/**
 * The whole text a good run writes to stdout.
 * @param {{ year: number, month: number, anchor: number, days: number[], grid: boolean }} settings
 * @returns {string}
 */
function formatReport(settings) {
  const { year, month, anchor, days, grid } = settings;
  const monthIndex = month - 1;
  const monthLabel = `${monthNames[monthIndex]} ${year}`;
  const anchorName = weekdayNames[anchor];
  const weeks = weeksOfMonth(year, monthIndex, anchor);

  const lines = [
    `Weeks of ${monthLabel}, numbered from the first week that contains a ${anchorName}`,
    'Each week runs Sunday to Saturday.',
    '',
  ];
  for (const w of weeks) {
    lines.push(`Week ${w.week}: ${formatDayLong(w.start)} - ${formatDayLong(w.end)}`);
    for (const d of days) {
      lines.push(`  ${weekdayNames[d]}: ${formatDayLong(addDays(w.start, d))}`);
    }
  }
  lines.push('');
  lines.push(
    `${monthLabel} has ${weeks.length} ${anchorName}s, so it has ${weeks.length} numbered weeks.`
  );

  const firstOfMonth = new Date(Date.UTC(year, monthIndex, 1));
  const lastOfMonth = new Date(Date.UTC(year, monthIndex, daysInMonth(year, monthIndex)));
  const firstWeek = weeks[0];
  const lastWeek = weeks[weeks.length - 1];
  const hasBefore = firstWeek.start.getTime() > firstOfMonth.getTime();
  const hasAfter = lastWeek.end.getTime() < lastOfMonth.getTime();
  lines.push(
    `Days of ${monthLabel} before week 1: ${formatSpan(
      hasBefore ? firstOfMonth : null,
      hasBefore ? addDays(firstWeek.start, -1) : null
    )}.`
  );
  lines.push(
    `Days of ${monthLabel} after week ${lastWeek.week}: ${formatSpan(
      hasAfter ? addDays(lastWeek.end, 1) : null,
      hasAfter ? lastOfMonth : null
    )}.`
  );

  if (grid) {
    lines.push('');
    for (const g of gridLines(year, monthIndex, weeks)) lines.push(g);
  }
  return lines.join('\n') + '\n';
}

/**
 * Run the calendar as a program. Writes the label as the first line of stderr on every run.
 */
function runCli() {
  process.stderr.write(LABEL + '\n');

  const args = process.argv.slice(2);
  if (args.includes('-h') || args.includes('--help')) {
    process.stdout.write(helpText());
    process.exitCode = 0;
    return;
  }

  const parsed = parseArgs(args);
  if ('error' in parsed) {
    // A refused run keeps stdout empty: the message and the usage go to stderr
    process.stderr.write(parsed.error + '\n' + helpText());
    process.exitCode = 1;
    return;
  }
  process.stdout.write(formatReport(parsed));
}

if (require.main === module) {
  runCli();
}

module.exports = {
  weeksOfMonth,
  parseArgs,
  formatReport,
  helpText,
  LABEL,
};
