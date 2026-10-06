"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ApiError,
  createBooking,
  getAvailability,
  getBooking,
  type BookingStatusResponse,
  type PaymentMethod,
  type Slot,
} from "@/lib/api";
import { getDeposit } from "@/lib/pricing";

export type BookingStep = "when" | "details" | "done";
export type { PaymentMethod };

/** How often the sheet asks whether an M-Pesa deposit has cleared. */
const POLL_INTERVAL_MS = 3000;
/** Giving up after this long; the hold outlives it, so nothing is lost. */
const POLL_TIMEOUT_MS = 120_000;

export type BookingState = {
  isOpen: boolean;
  step: BookingStep;
  /** `Date.toDateString()` of the chosen day. */
  dayKey: string | null;
  /** The slot's key, as the API names it — not its label. */
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

/** `Date.toDateString()` to the `YYYY-MM-DD` the API expects. */
function toIsoDate(dayKey: string): string {
  const d = new Date(dayKey);
  const month = `${d.getMonth() + 1}`.padStart(2, "0");
  const day = `${d.getDate()}`.padStart(2, "0");
  return `${d.getFullYear()}-${month}-${day}`;
}

export function useBooking(
  amount: number,
  selection: { tierId: string | null; addIds: string[] },
) {
  const [state, setState] = useState<BookingState>(INITIAL);

  // Keyed by the day they describe, so a slow answer for a day the client has
  // already moved on from is ignored rather than shown against the new one.
  const [fetched, setFetched] = useState<{ dayKey: string; slots: Slot[] } | null>(
    null,
  );
  const [slotsError, setSlotsError] = useState<{
    dayKey: string;
    message: string;
  } | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [booking, setBooking] = useState<BookingStatusResponse | null>(null);
  const [pollTimedOut, setPollTimedOut] = useState(false);

  const patch = useCallback(
    (next: Partial<BookingState>) => setState((s) => ({ ...s, ...next })),
    [],
  );

  const open = useCallback(() => patch({ isOpen: true }), [patch]);

  /**
   * Closing keeps the chosen date, time and contact details so reopening does
   * not make the client start over; only the flow's own progress resets.
   */
  const close = useCallback(() => {
    setError(null);
    setBooking(null);
    setPollTimedOut(false);
    // Not carried into the next attempt: a failure from last time is not news
    // about this one, and keeping it would hide times that now load fine.
    setSlotsError(null);
    setFetched(null);
    patch({ isOpen: false, step: "when", pay: null, reference: null });
  }, [patch]);

  const pickDay = useCallback(
    (dayKey: string) => patch({ dayKey, slot: null }),
    [patch],
  );

  const deposit = useMemo(() => getDeposit(amount), [amount]);

  // Real availability, so a time another client has taken cannot be picked.
  useEffect(() => {
    if (!state.isOpen || !state.dayKey) return;

    const dayKey = state.dayKey;
    let cancelled = false;

    getAvailability(toIsoDate(dayKey))
      .then((data) => {
        if (cancelled) return;
        setFetched({ dayKey, slots: data.slots });
        // A retry that works has to clear the earlier failure, or the day stays
        // unbookable however many times it is reloaded.
        setSlotsError((previous) =>
          previous?.dayKey === dayKey ? null : previous,
        );
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          setSlotsError({
            dayKey,
            message:
              e instanceof ApiError ? e.message : "Could not load times.",
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [state.isOpen, state.dayKey]);

  // All derived: setting any of this from inside the effect would cascade a
  // render, and keying on the day makes a stale response simply not match.
  const forCurrentDay = fetched?.dayKey === state.dayKey;
  const slots = forCurrentDay ? (fetched?.slots ?? []) : [];
  const slotsErrorMessage =
    slotsError?.dayKey === state.dayKey ? slotsError.message : null;
  const loadingSlots = Boolean(state.dayKey) && !forCurrentDay && !slotsErrorMessage;

  const canContinue = Boolean(state.dayKey && state.slot);
  const canSubmit = Boolean(
    state.name.trim() && state.phone.trim() && state.pay && !submitting,
  );

  const submit = useCallback(async () => {
    if (!state.dayKey || !state.slot || !state.pay || !selection.tierId) return;
    if (!(state.name.trim() && state.phone.trim())) return;

    setSubmitting(true);
    setError(null);

    try {
      // No amount is sent: the server prices this from the ids and its own
      // catalogue, and that figure is what gets charged.
      const created = await createBooking({
        tier_id: selection.tierId,
        addition_ids: selection.addIds,
        booking_date: toIsoDate(state.dayKey),
        slot_key: state.slot,
        name: state.name.trim(),
        phone: state.phone.trim(),
        notes: state.notes.trim() || null,
        payment_method: state.pay,
      });

      setBooking(created);
      patch({ step: "done", reference: created.reference });
    } catch (e: unknown) {
      if (e instanceof ApiError && e.reference) {
        // The slot is held but the prompt failed. Show the reference rather
        // than losing it: without it the client cannot be helped.
        patch({ step: "done", reference: e.reference });
        setError(e.message);

        // Load the booking too. Polling watches `booking`, so without this the
        // screen would say "check your phone" while nothing was watching, and
        // a payment that did go through would never show.
        try {
          setBooking(await getBooking(e.reference));
        } catch {
          // The reference is still on screen; that is the part that matters.
        }
      } else {
        setError(
          e instanceof ApiError ? e.message : "Could not complete the booking.",
        );
      }
    } finally {
      setSubmitting(false);
    }
  }, [state, selection, patch]);

  // An M-Pesa deposit confirms out of band, so watch for it.
  const startedPollingAt = useRef<number | null>(null);

  useEffect(() => {
    const reference = state.reference;
    const waiting = booking?.status === "pending_payment" && state.pay === "mpesa";

    if (state.step !== "done" || !reference || !waiting) return;

    startedPollingAt.current = Date.now();

    const id = setInterval(() => {
      if (Date.now() - (startedPollingAt.current ?? 0) > POLL_TIMEOUT_MS) {
        clearInterval(id);
        // Say so. Leaving "check your phone" up forever tells the client to
        // expect something that is not coming, and their hold lapses anyway.
        setPollTimedOut(true);
        return;
      }

      getBooking(reference)
        .then((latest) => setBooking(latest))
        .catch(() => {
          // A blip here is not worth a message: the hold outlives the poll and
          // the client can check again.
        });
    }, POLL_INTERVAL_MS);

    return () => clearInterval(id);
  }, [state.step, state.reference, state.pay, booking?.status]);

  return {
    ...state,
    deposit,
    slots,
    loadingSlots,
    slotsError: slotsErrorMessage,
    submitting,
    error,
    booking,
    pollTimedOut,
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
    goToDetails: useCallback(() => {
      setState((s) => (s.dayKey && s.slot ? { ...s, step: "details" } : s));
    }, []),
    backToWhen: useCallback(() => patch({ step: "when" }), [patch]),
    submit,
  };
}

export type Booking = ReturnType<typeof useBooking>;
