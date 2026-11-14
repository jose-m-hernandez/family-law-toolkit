// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Jose Miguel Hernandez
// Shared date/time utilities for the command-line tools

// Weekday names and lookup map
const weekdayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const nameToOrdinal = {
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

// Generic month/day helpers.
// Every date is built and read in UTC (Date.UTC and the getUTC* methods), so a calendar date is
// the same in every time zone. Dates built in local time can skip a day (for example 2011-12-30
// in Samoa) or print a day early east of UTC. Valid for years 100 and later.
function daysInMonth(year, monthIndex) {
  return new Date(Date.UTC(year, monthIndex + 1, 0)).getUTCDate();
}

/**
 * Print a Date made by these helpers as YYYY-MM-DD, from its calendar fields.
 * @param {Date} d
 * @returns {string}
 */
function formatDate(d) {
  const y = String(d.getUTCFullYear()).padStart(4, '0');
  const m = String(d.getUTCMonth() + 1).padStart(2, '0');
  const day = String(d.getUTCDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function getNthOccurrenceDate(year, monthIndex, weekdayOrdinal, n) {
  if (n <= 0) return null;
  const firstDay = new Date(Date.UTC(year, monthIndex, 1)).getUTCDay();
  const firstOccurDate = 1 + ((weekdayOrdinal - firstDay + 7) % 7);
  const targetDate = firstOccurDate + (n - 1) * 7;
  return targetDate <= daysInMonth(year, monthIndex)
    ? new Date(Date.UTC(year, monthIndex, targetDate))
    : null;
}

function getFifthOccurrenceDate(year, monthIndex, weekdayOrdinal) {
  return getNthOccurrenceDate(year, monthIndex, weekdayOrdinal, 5);
}

module.exports = {
  // constants
  weekdayNames,
  nameToOrdinal,
  // month/day helpers
  daysInMonth,
  formatDate,
  getNthOccurrenceDate,
  getFifthOccurrenceDate,
};
