"use client";

import { SLOTS } from "@/data/services";
import type { Booking } from "@/hooks/useBooking";
import { money, prettyDate } from "@/lib/format";
import { Calendar } from "./Calendar";
import styles from "./steps.module.css";

type StepWhenProps = {
  booking: Booking;
  amount: number;
};

export function StepWhen({ booking, amount }: StepWhenProps) {
  const whenLine = booking.dayKey
    ? booking.slot
      ? `${prettyDate(booking.dayKey)} at ${booking.slot}`
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
          <div className={styles.slots} role="radiogroup" aria-label="Start time">
            {SLOTS.map((slot) => (
              <button
                key={slot}
                type="button"
                role="radio"
                aria-checked={booking.slot === slot}
                onClick={() => booking.pickSlot(slot)}
                className={[
                  styles.slot,
                  booking.slot === slot ? styles.slotSelected : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                {slot}
              </button>
            ))}
          </div>
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
