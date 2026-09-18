"use client";

import type { Addition } from "@/data/services";
import type { Booking } from "@/hooks/useBooking";
import type { Summary } from "@/lib/pricing";
import { BookingSheet } from "./BookingSheet";
import { StepDetails } from "./StepDetails";
import { StepDone } from "./StepDone";
import { StepWhen } from "./StepWhen";

type BookingFlowProps = {
  booking: Booking;
  summary: Summary;
  amount: number;
  chips: Addition[];
  onRemoveChip: (id: string) => void;
};

/** Picks the step body; the sheet supplies the chrome all three share. */
export function BookingFlow({
  booking,
  summary,
  amount,
  chips,
  onRemoveChip,
}: BookingFlowProps) {
  return (
    <BookingSheet
      step={booking.step}
      summary={summary}
      chips={chips}
      onRemoveChip={onRemoveChip}
      onClose={booking.close}
    >
      {booking.step === "when" ? <StepWhen booking={booking} amount={amount} /> : null}
      {booking.step === "details" ? (
        <StepDetails booking={booking} amount={amount} />
      ) : null}
      {booking.step === "done" ? <StepDone booking={booking} amount={amount} /> : null}
    </BookingSheet>
  );
}
