"use client";

import { useCallback, useMemo, useState } from "react";
import { getDeposit } from "@/lib/pricing";

export type BookingStep = "when" | "details" | "done";
export type PaymentMethod = "mpesa" | "studio";

export type BookingState = {
  isOpen: boolean;
  step: BookingStep;
  /** `Date.toDateString()` of the chosen day. */
  dayKey: string | null;
  slot: string | null;
  monthOffset: number;
  name: string;
  phone: string;
  notes: string;
  pay: PaymentMethod | null;
  reference: string | null;
};

const INITIAL: BookingState = {
  isOpen: false,
  step: "when",
  dayKey: null,
  slot: null,
  monthOffset: 0,
  name: "",
  phone: "",
  notes: "",
  pay: null,
  reference: null,
};

function makeReference(): string {
  return `SS-${Math.random().toString(36).slice(2, 7).toUpperCase()}`;
}

/**
 * Owns the booking sheet's state machine. `amount` comes from the menu
 * selection so the deposit tracks whatever the client has picked.
 */
export function useBooking(amount: number) {
  const [state, setState] = useState<BookingState>(INITIAL);

  const patch = useCallback(
    (next: Partial<BookingState>) => setState((s) => ({ ...s, ...next })),
    [],
  );

  const open = useCallback(() => patch({ isOpen: true }), [patch]);

  /**
   * Closing keeps the chosen date, time and contact details so reopening does
   * not make the client start over; only the flow's own progress resets.
   */
  const close = useCallback(
    () => patch({ isOpen: false, step: "when", pay: null, reference: null }),
    [patch],
  );

  const pickDay = useCallback(
    (dayKey: string) => patch({ dayKey, slot: null }),
    [patch],
  );

  const deposit = useMemo(() => getDeposit(amount), [amount]);

  const canContinue = Boolean(state.dayKey && state.slot);
  const canSubmit = Boolean(state.name.trim() && state.phone.trim() && state.pay);

  const submit = useCallback(() => {
    setState((s) => {
      if (!(s.name.trim() && s.phone.trim() && s.pay)) return s;
      return { ...s, step: "done", reference: makeReference() };
    });
  }, []);

  const goToDetails = useCallback(() => {
    setState((s) => (s.dayKey && s.slot ? { ...s, step: "details" } : s));
  }, []);

  return {
    ...state,
    deposit,
    canContinue,
    canSubmit,
    open,
    close,
    patch,
    pickDay,
    pickSlot: useCallback((slot: string) => patch({ slot }), [patch]),
    prevMonth: useCallback(
      () => setState((s) => ({ ...s, monthOffset: s.monthOffset - 1 })),
      [],
    ),
    nextMonth: useCallback(
      () => setState((s) => ({ ...s, monthOffset: s.monthOffset + 1 })),
      [],
    ),
    goToDetails,
    backToWhen: useCallback(() => patch({ step: "when" }), [patch]),
    submit,
  };
}

export type Booking = ReturnType<typeof useBooking>;
