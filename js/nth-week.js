// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Jose Miguel Hernandez
/**
 * Fifth-Week Counter (weeks numbered from the first week that contains the anchor weekday)
 *
 * Purpose
 * - Quantify how often a month has a "5th week", with weeks numbered from the first week that
 *   contains the anchor weekday.
 *
 * Definition
 * - Week 1 is the first calendar week that contains the specified anchor weekday(s)
 *   (for example, Tuesday and/or Wednesday).
 * - A month is said to have a "5th week" when that month contains 5 occurrences of the anchor weekday.
 *   (Example: a month with 5 Tuesdays qualifies as having a 5th week when Tuesday is the anchor.)
 *
 * Defaults
 * - Start year: current year
 * - End year: start year + 18 (so with --start 2031 alone, 2031 to 2049)
 * - Anchor weekday: none; --anchor or --weekday is required, not both
 * - Output includes: all 5th-occurrence dates, per-year counts, and a summary
 *
 * Input rules (a run that breaks one prints a message and the usage to stderr, prints nothing to
 * stdout, and exits 1)
 * - Years are whole numbers from 1583 to 9999, start <= end, and at most 1000 years in the range.
 *   All dates use today's Gregorian calendar rules, also for years before a country adopted it
 *   (the proleptic Gregorian calendar).
 * - --weekday takes whole numbers 0 to 6, comma-separated; --anchor takes weekday names.
 *   Spaces around a value or a list item are ignored; a tab or line break is an error.
 * - Every flag that takes a value needs one, and takes it once; an unknown flag or a stray word
 *   that is not a flag is an error.
 * - A weekday given twice is counted once. Each weekday in a list is counted separately.
 * - Dates are calendar dates, printed the same in every time zone.
 *
 * CLI
 * - --start <year>         Start year (inclusive). Default: current year
 * - --end <year>           End year (inclusive). Default: start + 18
 * - --weekday <0-6|csv>   Anchor weekday ordinal(s). 0=Sun ... 6=Sat. Example: --weekday 2,3
 * - --anchor <names>      Anchor weekday name(s). Example: --anchor Tuesday or --anchor Tuesday,Wednesday
 * - --list                Accepted; dates are always printed
 * - --per-year            Accepted; per-year counts are always printed
 * - -h, --help            Show usage help
 *
 * Usage Examples
 *   node nth-week.js --anchor Tuesday
 *   node nth-week.js --start 2024 --end 2030 --anchor Tuesday
 *   node nth-week.js --weekday 3 --start 2024 --end 2026
 */
// Pure computation helpers

const {
  daysInMonth,
  formatDate,
  getFifthOccurrenceDate,
  weekdayNames,
  nameToOrdinal,
} = require('./utils/date');

/**
 * List ISO dates for each 5th occurrence in the range.
 * @param {number} startYear
 * @param {number} endYear
 * @param {number} weekdayOrdinal
 * @returns {{ datesByYear: Record<number,string[]>, total: number }}
 */
function listFifthOccurrenceDates(startYear, endYear, weekdayOrdinal) {
  const datesByYear = {};
  let total = 0;
  for (let y = startYear; y <= endYear; y++) {
    const arr = [];
    for (let m = 0; m < 12; m++) {
      const d = getFifthOccurrenceDate(y, m, weekdayOrdinal);
      if (d) {
        arr.push(formatDate(d));
        total++;
      }
    }
    datesByYear[y] = arr;
  }
  return { datesByYear, total };
}

/**
 * Compute the set of months (and yearly counts) that have a 5th occurrence.
 * @param {number} startYear
 * @param {number} endYear
 * @param {number} weekdayOrdinal
 * @returns {{ monthsSet: Set<string>, perYear: Record<number,number>, total: number }}
 */
function computeMonthsWithFifth(startYear, endYear, weekdayOrdinal) {
  const monthsSet = new Set(); // keys like YYYY-MM
  const perYear = {};
  for (let y = startYear; y <= endYear; y++) {
    let c = 0;
    for (let m = 0; m < 12; m++) {
      const fifth = getFifthOccurrenceDate(y, m, weekdayOrdinal);
      if (fifth) {
        monthsSet.add(`${y}-${String(m + 1).padStart(2, '0')}`);
        c++;
      }
    }
    perYear[y] = c;
  }
  return { monthsSet, perYear, total: Array.from(monthsSet).length };
}

/**
 * Compute and optionally print the 5th occurrence dates for a given year and anchor weekday.
 * Uses getFifthOccurrenceDate for accuracy and performance.
 *
 * @param {number} year - Four-digit year (e.g., 2025).
 * @param {number} startDayOrdinal - Anchor weekday ordinal (0=Sun ... 6=Sat).
 * @param {{ verboseDates?: boolean, perYear?: boolean }} [options]
 * @returns {number} The number of months in the given year that contain a 5th occurrence.
 */
function findFifthWeeks(year, startDayOrdinal, options = { verboseDates: false, perYear: false }) {
  let count = 0;
  for (let month = 0; month < 12; month++) {
    const d = getFifthOccurrenceDate(year, month, startDayOrdinal);
    if (d) {
      if (options.verboseDates) console.log(formatDate(d));
      count++;
    }
  }
  if (options.perYear) console.log(`Year ${year}: ${count} months`);
  return count;
}

/**
 * Tally months with a 5th occurrence across a year range.
 *
 * @param {number} startYear - Inclusive start year.
 * @param {number} endYear - Inclusive end year.
 * @param {number} startDayOrdinal - Anchor weekday ordinal (0=Sun ... 6=Sat).
 * @param {{ verboseDates?: boolean, perYear?: boolean }} [options]
 * @returns {number} Total count of months in the range that have a 5th occurrence.
 */
function tallyFifthWeeks(
  startYear,
  endYear,
  startDayOrdinal,
  options = { verboseDates: false, perYear: false }
) {
  let total = 0;
  for (let y = startYear; y <= endYear; y++) {
    total += findFifthWeeks(y, startDayOrdinal, options);
  }
  return total;
}

/**
 * CLI usage help text.
 * @returns {string}
 */
function helpText() {
  return `
Usage: node nth-week.js (--anchor <names> | --weekday <0-6|csv>) [--start <year>] [--end <year>] [--list] [--per-year]

Options:
  --anchor    Anchor weekday name(s), for example Tuesday or Tuesday,Wed (this or --weekday is required, not both)
  --weekday   Weekday number 0=Sun ... 6=Sat, or a comma-separated list (this or --anchor is required, not both)
  --start     Start year (default: current year)
  --end       End year, inclusive (default: start + 18)
  --list      Accepted; each 5th-occurrence date is always printed
  --per-year  Accepted; the count for each year is always printed
  -h, --help  Show this help

Years are whole numbers from 1583 to 9999, start no later than end, at most 1000 years.
All dates use today's Gregorian calendar rules, also for years before a country adopted it (proleptic Gregorian).
Spaces around a value or a list item are ignored.
Each weekday in a list is counted separately. Dates are calendar dates, the same in every time zone.
`;
}

/**
 * Print CLI usage help to stdout.
 */
function printHelp() {
  console.log(helpText());
}

const LABEL = 'Educational; not legal advice; not certified for court filing; consult counsel.';
const MISSING =
  'nth-week: the anchor weekday is required; give --anchor <name> (for example, --anchor Tuesday) or --weekday <0-6>.';

const MIN_YEAR = 1583;
const MAX_YEAR = 9999;
const MAX_SPAN = 1000;
const DEFAULT_SPAN = 18;
const FLAGS_WITH_VALUE = ['--start', '--end', '--weekday', '--anchor'];
const FLAGS_ALWAYS_ON = ['--list', '--per-year'];

/**
 * Remove plain spaces from both ends. Tabs and line breaks are kept, so they fail the checks.
 * @param {string} text
 * @returns {string}
 */
function trimSpaces(text) {
  return text.replace(/^ +| +$/g, '');
}

/**
 * Read a year given on the command line: four digits, in the Gregorian range.
 * @param {string} flag
 * @param {string} text
 * @returns {{ value?: number, error?: string }}
 */
function parseYear(flag, text) {
  const t = trimSpaces(text);
  const value = /^[0-9]{4}$/.test(t) ? Number(t) : NaN;
  if (!(value >= MIN_YEAR && value <= MAX_YEAR)) {
    return {
      error: `nth-week: ${flag} must be a whole year from ${MIN_YEAR} to ${MAX_YEAR} (Gregorian calendar); got ${JSON.stringify(text)}.`,
    };
  }
  return { value };
}

/**
 * Parse the command-line arguments. Returns an error message, or the settings to run with.
 * @param {string[]} args Arguments after the script path.
 * @param {number} currentYear
 * @returns {{ error: string } | { start: number, end: number, weekdays: number[] }}
 */
function parseArgs(args, currentYear) {
  const given = {};
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (FLAGS_ALWAYS_ON.includes(a)) continue;
    if (!FLAGS_WITH_VALUE.includes(a)) {
      return { error: `nth-week: unknown argument ${JSON.stringify(a)}.` };
    }
    if (Object.hasOwn(given, a)) return { error: `nth-week: ${a} is given more than once.` };
    const v = args[i + 1];
    if (v === undefined || v.startsWith('--')) {
      return { error: `nth-week: ${a} needs a value.` };
    }
    given[a] = v;
    i++;
  }

  if (Object.hasOwn(given, '--anchor') && Object.hasOwn(given, '--weekday')) {
    return { error: 'nth-week: give --anchor or --weekday, not both; use one.' };
  }

  let start = currentYear;
  if (Object.hasOwn(given, '--start')) {
    const r = parseYear('--start', given['--start']);
    if (r.error) return r;
    start = r.value;
  }
  let end = start + DEFAULT_SPAN;
  if (Object.hasOwn(given, '--end')) {
    const r = parseYear('--end', given['--end']);
    if (r.error) return r;
    end = r.value;
  } else if (end > MAX_YEAR) {
    return {
      error: `nth-week: the default end year (start + ${DEFAULT_SPAN}) is ${end}, past ${MAX_YEAR}; give --end.`,
    };
  }
  if (start > end) {
    return { error: `nth-week: --start ${start} is after --end ${end}.` };
  }
  if (end - start + 1 > MAX_SPAN) {
    return {
      error: `nth-week: the range ${start} to ${end} is ${end - start + 1} years; at most ${MAX_SPAN} years.`,
    };
  }

  let weekdays = [];
  if (Object.hasOwn(given, '--weekday')) {
    const bad = [];
    for (const item of given['--weekday'].split(',')) {
      const t = trimSpaces(item);
      if (/^[0-6]$/.test(t)) weekdays.push(Number(t));
      else bad.push(item);
    }
    if (bad.length > 0) {
      return {
        error: `nth-week: --weekday takes whole numbers 0 (Sunday) to 6 (Saturday), comma-separated; got ${bad.map((b) => JSON.stringify(b)).join(', ')} in ${JSON.stringify(given['--weekday'])}.`,
      };
    }
  } else if (Object.hasOwn(given, '--anchor')) {
    const bad = [];
    for (const item of given['--anchor'].split(',')) {
      const key = trimSpaces(item).toLowerCase();
      if (Object.hasOwn(nameToOrdinal, key)) weekdays.push(nameToOrdinal[key]);
      else bad.push(item);
    }
    if (bad.length > 0) {
      return {
        error: `nth-week: unknown weekday name ${bad.map((b) => JSON.stringify(b)).join(', ')} in --anchor ${JSON.stringify(given['--anchor'])}; use names like Tuesday or Tue.`,
      };
    }
  }
  weekdays = weekdays.filter((wd, i) => weekdays.indexOf(wd) === i);
  if (weekdays.length === 0) return { error: MISSING };

  return { start, end, weekdays };
}

/**
 * Median of a list of numbers (the mean of the two middle ones when the length is even).
 * @param {number[]} values
 * @returns {number}
 */
function median(values) {
  const arr = [...values].sort((a, b) => a - b);
  const mid = Math.floor(arr.length / 2);
  return arr.length % 2 ? arr[mid] : (arr[mid - 1] + arr[mid]) / 2;
}

/**
 * Run the counter as a program. Writes the label as the first line of stderr on every run.
 */
function runCli() {
  console.error(LABEL);

  /**
   * Raw CLI arguments (excluding `node` and script path).
   * @type {string[]}
   */
  const args = process.argv.slice(2);
  if (args.includes('-h') || args.includes('--help')) {
    printHelp();
    process.exit(0);
  }

  const parsed = parseArgs(args, new Date().getFullYear());
  if ('error' in parsed) {
    console.error(parsed.error);
    // A refused run keeps stdout empty: the usage goes to stderr
    console.error(helpText());
    process.exit(1);
  }
  const { start, end, weekdays } = parsed;
  const verboseDates = true;
  const perYear = true;

  console.log(
    `\n5th week counter (weeks numbered from the first week that contains the anchor weekday)`
  );
  console.log(`Range: ${start}–${end}`);
  const humanList = weekdays.map((wd) => weekdayNames[wd]).join(' and ');
  const rule =
    weekdays.length > 1
      ? `A month has a "5th week" if it contains 5 of the same weekday; each weekday is counted separately.`
      : `A month has a "5th week" if it contains 5 ${humanList}s.`;
  console.log(`Definition: Week 1 is the first week that contains a ${humanList}. ${rule}`);
  console.log('Showing dates and per-year summary.');

  weekdays.forEach((wd) => {
    const name = weekdayNames[wd];
    // Print dates and per-year via legacy path for continuity
    const total = tallyFifthWeeks(start, end, wd, { verboseDates, perYear });
    // Compute analytics and print summary
    const { total: distinctMonths, perYear: perYearCounts } = computeMonthsWithFifth(
      start,
      end,
      wd
    );
    const yearSpan = end - start + 1;
    const avgPerYear = distinctMonths / yearSpan;
    const medianPerYear = median(Object.values(perYearCounts));
    let minPerYear = Infinity;
    let maxPerYear = -Infinity;
    for (const c of Object.values(perYearCounts)) {
      if (c < minPerYear) minPerYear = c;
      if (c > maxPerYear) maxPerYear = c;
    }

    console.log(
      `${name} (${wd}) → Months with a 5th week (first week contains ${name}): ${total} (between ${start} and ${end}).`
    );
    console.log(
      `Summary for ${name}: total months=${distinctMonths}, years=${yearSpan}, avg/year=${avgPerYear.toFixed(2)}, median/year=${medianPerYear}, min/year=${minPerYear}, max/year=${maxPerYear}`
    );
  });
}

if (require.main === module) {
  runCli();
}

module.exports = {
  daysInMonth,
  formatDate,
  getFifthOccurrenceDate,
  computeMonthsWithFifth,
  listFifthOccurrenceDates,
  tallyFifthWeeks,
  parseArgs,
  median,
};
