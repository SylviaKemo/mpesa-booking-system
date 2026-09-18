"use client";

import { useMemo } from "react";
import { buildMonth } from "@/lib/calendar";
import { monthLabel, WEEKDAY_INITIALS } from "@/lib/format";
import styles from "./Calendar.module.css";

type CalendarProps = {
  monthOffset: number;
  selectedKey: string | null;
  onPickDay: (key: string) => void;
  onPrevMonth: () => void;
  onNextMonth: () => void;
};

export function Calendar({
  monthOffset,
  selectedKey,
  onPickDay,
  onPrevMonth,
  onNextMonth,
}: CalendarProps) {
  const { date, cells } = useMemo(() => buildMonth(monthOffset), [monthOffset]);

  return (
    <div>
      <div className={styles.nav}>
        <p className={styles.sectionLabel}>Date</p>
        <div className={styles.monthNav}>
          <button
            type="button"
            onClick={onPrevMonth}
            aria-label="Previous month"
            className={styles.arrow}
          >
            ‹
          </button>
          <p className={styles.month} aria-live="polite">
            {monthLabel(date)}
          </p>
          <button
            type="button"
            onClick={onNextMonth}
            aria-label="Next month"
            className={styles.arrow}
          >
            ›
          </button>
        </div>
      </div>

      <div className={styles.weekdays} aria-hidden="true">
        {WEEKDAY_INITIALS.map((day) => (
          <p key={day} className={styles.weekday}>
            {day}
          </p>
        ))}
      </div>

      <div className={styles.grid} role="grid" aria-label="Choose a date">
        {cells.map((cell, i) => {
          const selected = cell.key !== null && cell.key === selectedKey;
          return (
            <button
              key={cell.key ?? `blank-${i}`}
              type="button"
              disabled={cell.key === null || cell.isPast}
              aria-pressed={cell.key ? selected : undefined}
              onClick={() => cell.key && onPickDay(cell.key)}
              className={[
                styles.day,
                cell.key === null ? styles.blank : "",
                selected ? styles.selected : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {cell.day ?? ""}
            </button>
          );
        })}
      </div>
    </div>
  );
}
