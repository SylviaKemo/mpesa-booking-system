export type CalendarCell = {
  /** `Date.toDateString()`, or null for a leading blank before the 1st. */
  key: string | null;
  day: number | null;
  isPast: boolean;
};

export type CalendarMonth = {
  date: Date;
  cells: CalendarCell[];
};

/**
 * Builds the grid for the month `monthOffset` away from today, with leading
 * blanks so the 1st lands under its weekday. Past days are marked, not omitted,
 * so the month keeps its shape.
 */
export function buildMonth(monthOffset: number, now = new Date()): CalendarMonth {
  const today = new Date(now);
  today.setHours(0, 0, 0, 0);

  const date = new Date(today.getFullYear(), today.getMonth() + monthOffset, 1);
  const daysInMonth = new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  const cells: CalendarCell[] = [];

  for (let i = 0; i < date.getDay(); i += 1) {
    cells.push({ key: null, day: null, isPast: true });
  }

  for (let day = 1; day <= daysInMonth; day += 1) {
    const d = new Date(date.getFullYear(), date.getMonth(), day);
    cells.push({ key: d.toDateString(), day, isPast: d < today });
  }

  return { date, cells };
}
