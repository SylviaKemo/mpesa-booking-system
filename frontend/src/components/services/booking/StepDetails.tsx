"use client";

import { Field } from "@/components/ui/Field";
import { SelectableCard } from "@/components/ui/SelectableCard";
import type { Booking } from "@/hooks/useBooking";
import { money } from "@/lib/format";
import styles from "./steps.module.css";

type StepDetailsProps = {
  booking: Booking;
  amount: number;
};

export function StepDetails({ booking, amount }: StepDetailsProps) {
  const dueLine =
    booking.pay === "mpesa"
      ? `${money(booking.deposit)} deposit now`
      : booking.pay === "studio"
        ? "Payable at the studio"
        : "Pick how you'd like to pay";

  return (
    <div>
      <p className={styles.sectionLabel}>Your details</p>

      <div className={styles.fields}>
        <Field
          label="Full name"
          value={booking.name}
          onChange={(name) => booking.patch({ name })}
          placeholder="Shamim Wanjiru"
        />
        <Field
          label="Phone (M-Pesa)"
          type="tel"
          value={booking.phone}
          onChange={(phone) => booking.patch({ phone })}
          placeholder="07XX XXX XXX"
        />
        <Field
          as="textarea"
          label="Anything I should know?"
          optional
          value={booking.notes}
          onChange={(notes) => booking.patch({ notes })}
          placeholder="First time, sensitive eyes, etc."
        />
      </div>

      <p className={styles.sectionLabel}>Deposit</p>
      <div className={styles.deposits} role="radiogroup" aria-label="Deposit method">
        <SelectableCard
          title="Pay deposit by M-Pesa"
          meta={`${money(booking.deposit)} — secures the slot`}
          selected={booking.pay === "mpesa"}
          onSelect={() => booking.patch({ pay: "mpesa" })}
        />
        <SelectableCard
          title="Pay at the studio"
          meta="Slot held for 30 min before your time"
          selected={booking.pay === "studio"}
          onSelect={() => booking.patch({ pay: "studio" })}
        />
      </div>

      <div className={styles.footer}>
        <button type="button" onClick={booking.backToWhen} className={styles.back}>
          Back
        </button>
        <div className={styles.detailsActions}>
          <div className={styles.detailsTotals}>
            <p className={styles.totalSmall}>{money(amount)}</p>
            <p className={styles.noteSmall}>{dueLine}</p>
          </div>
          <button
            type="button"
            disabled={!booking.canSubmit}
            onClick={booking.submit}
            className={`${styles.primary} ${styles.submit}`}
          >
            {booking.pay === "mpesa" ? "Pay deposit & book" : "Confirm booking"}
          </button>
        </div>
      </div>
    </div>
  );
}
