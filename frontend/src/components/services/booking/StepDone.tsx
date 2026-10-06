"use client";

import type { Booking } from "@/hooks/useBooking";
import { money, prettyDate } from "@/lib/format";
import styles from "./StepDone.module.css";

type StepDoneProps = {
  booking: Booking;
  amount: number;
};

export function StepDone({ booking, amount }: StepDoneProps) {
  const firstName = booking.name.trim().split(" ")[0];
  const phone = booking.phone.trim() || "your phone";

  const slotLabel = booking.slots.find((s) => s.key === booking.slot)?.label;

  const whenLine =
    booking.dayKey && slotLabel
      ? `${prettyDate(booking.dayKey)} at ${slotLabel}`
      : "—";

  // The server's view, once the callback has landed. Until then the prompt is
  // still out and the sheet is polling.
  const confirmed = booking.booking?.status === "confirmed";
  const awaitingPayment = booking.pay === "mpesa" && !confirmed;
  const receipt = booking.booking?.payments.at(-1)?.mpesa_receipt ?? null;

  const dueLine =
    booking.pay === "mpesa"
      ? `${money(booking.deposit)} deposit now`
      : "Payable at the studio";

  return (
    <div className={styles.done}>
      <div className={styles.tick} aria-hidden="true">
        ✓
      </div>

      <h3 className={styles.headline}>
        {awaitingPayment
          ? "Check your phone"
          : firstName
            ? `${firstName}, you're booked`
            : "You're booked"}
      </h3>

      <p className={styles.body}>
        {booking.error
          ? booking.error
          : awaitingPayment
            ? `An M-Pesa request for the deposit has been sent to ${phone}. Confirm it on your handset and the slot is locked in.`
            : booking.pay === "mpesa"
              ? `Deposit received${receipt ? ` — M-Pesa receipt ${receipt}` : ""}. Your slot is confirmed.`
              : `Your slot is held. Come a few minutes early and settle at the studio — a reminder lands on ${phone} the day before.`}
      </p>

      <dl className={styles.receipt}>
        <div className={styles.row}>
          <dt className={styles.rowLabel}>Reference</dt>
          <dd className={styles.reference}>{booking.reference ?? "—"}</dd>
        </div>
        <div className={styles.row}>
          <dt className={styles.rowLabel}>When</dt>
          <dd className={styles.rowValue}>{whenLine}</dd>
        </div>
        <div className={styles.row}>
          <dt className={styles.rowLabel}>Total</dt>
          <dd className={styles.rowValue}>
            {money(amount)} · {dueLine}
          </dd>
        </div>
      </dl>

      <button type="button" onClick={booking.close} className={styles.doneButton}>
        Done
      </button>
    </div>
  );
}
