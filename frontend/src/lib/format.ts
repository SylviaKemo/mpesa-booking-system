/**
 * Formats a KES amount as "Ksh 3,000".
 *
 * Deliberately does not use `toLocaleString`: the services menu renders on the
 * server and hydrates on the client, and locale data can differ between the two,
 * which produces a hydration mismatch. Manual grouping is identical everywhere.
 */
export function money(amount: number): string {
  const grouped = Math.round(amount)
    .toString()
    .replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return `Ksh ${grouped}`;
}

const DOW = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

export const WEEKDAY_INITIALS = DOW.map((d) => d.slice(0, 2));

/** "Mon 15 Sep" — from a `Date.toDateString()` key. */
export function prettyDate(key: string): string {
  const d = new Date(key);
  return `${DOW[d.getDay()]} ${d.getDate()} ${MONTHS[d.getMonth()]}`;
}

/** "Sep 2026" — the calendar's month heading. */
export function monthLabel(date: Date): string {
  return `${MONTHS[date.getMonth()]} ${date.getFullYear()}`;
}
