"use client";

import type { Booking } from "@/hooks/useBooking";
import { money, prettyDate } from "@/lib/format";
import { Calendar } from "./Calendar";
import styles from "./steps.module.css";

type StepWhenProps = {
  booking: Booking;
  amount: number;
};

export function StepWhen({ booking, amount }: StepWhenProps) {
  const slotLabel = booking.slots.find((s) => s.key === booking.slot)?.label;

  const whenLine = booking.dayKey
    ? slotLabel
      ? `${prettyDate(booking.dayKey)} at ${slotLabel}`
      : "Now pick a time"
    : "Pick a date to see available times";

  return (
    <div>
      <Calendar
        monthOffset={booking.monthOffset}
        selectedKey={booking.dayKey}
        onPickDay={booking.pickDay}
        onPrevMonth={booking.prevMonth}
        onNextMonth={booking.nextMonth}
      />

      {booking.dayKey ? (
        <div>
          <p className={styles.sectionLabel}>
            Time on {prettyDate(booking.dayKey)}
          </p>
          {booking.slotsError ? (
            <p className={styles.error} role="status">
              {booking.slotsError}
            </p>
          ) : booking.loadingSlots ? (
            <p className={styles.note}>Checking what&apos;s free…</p>
          ) : booking.slots.length === 0 ? (
            <p className={styles.note}>
              No times available on this day. Try another date.
            </p>
          ) : (
            <div className={styles.slots} role="radiogroup" aria-label="Start time">
              {booking.slots.map((slot) => (
                <button
                  key={slot.key}
                  type="button"
                  role="radio"
                  aria-checked={booking.slot === slot.key}
                  // A time someone else holds is shown disabled rather than
                  // hidden, so the day keeps its shape.
                  disabled={!slot.available}
                  onClick={() => booking.pickSlot(slot.key)}
                  className={[
                    styles.slot,
                    booking.slot === slot.key ? styles.slotSelected : "",
                    !slot.available ? styles.slotTaken : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                >
                  {slot.label}
                </button>
              ))}
            </div>
          )}
        </div>
      ) : null}

      <div className={styles.footer}>
        <div className={styles.totals}>
          <p className={styles.total}>{money(amount)}</p>
          <p className={styles.note}>{whenLine}</p>
        </div>
        <button
          type="button"
          disabled={!booking.canContinue}
          onClick={booking.goToDetails}
          className={styles.primary}
        >
          Continue
        </button>
      </div>
    </div>
  );
}
