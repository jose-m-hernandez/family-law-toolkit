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

// Generic month/day helpers
function daysInMonth(year, monthIndex) {
  return new Date(year, monthIndex + 1, 0).getDate();
}

function getNthOccurrenceDate(year, monthIndex, weekdayOrdinal, n) {
  if (n <= 0) return null;
  const firstDay = new Date(year, monthIndex, 1).getDay();
  const firstOccurDate = 1 + ((weekdayOrdinal - firstDay + 7) % 7);
  const targetDate = firstOccurDate + (n - 1) * 7;
  return targetDate <= daysInMonth(year, monthIndex)
    ? new Date(year, monthIndex, targetDate)
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
  getNthOccurrenceDate,
  getFifthOccurrenceDate,
};
