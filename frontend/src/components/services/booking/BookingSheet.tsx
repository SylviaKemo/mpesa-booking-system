"use client";

import { useEffect, useRef } from "react";
import type { Addition } from "@/data/services";
import type { Summary } from "@/lib/pricing";
import type { BookingStep } from "@/hooks/useBooking";
import styles from "./BookingSheet.module.css";

const STEP_LABEL: Record<BookingStep, string> = {
  when: "Step 1 of 3",
  details: "Step 2 of 3",
  done: "Booked",
};

const STEP_TITLE: Record<BookingStep, string> = {
  when: "Choose a date & time",
  details: "Your details",
  done: "You're on the books",
};

type BookingSheetProps = {
  step: BookingStep;
  summary: Summary;
  chips: Addition[];
  onRemoveChip: (id: string) => void;
  onClose: () => void;
  children: React.ReactNode;
};

/**
 * Overlay, sheet and the header/summary block that every step shares.
 * Closes on Escape and on overlay click, and locks page scroll while open.
 */
export function BookingSheet({
  step,
  summary,
  chips,
  onRemoveChip,
  onClose,
  children,
}: BookingSheetProps) {
  const sheetRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    sheetRef.current?.focus();

    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [onClose]);

  return (
    <div
      className={styles.overlay}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={sheetRef}
        role="dialog"
        aria-modal="true"
        aria-label={STEP_TITLE[step]}
        tabIndex={-1}
        className={styles.sheet}
      >
        <div className={styles.header}>
          <div className={styles.headings}>
            <p className={styles.stepLabel}>{STEP_LABEL[step]}</p>
            <h2 className={styles.stepTitle}>{STEP_TITLE[step]}</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close booking"
            className={styles.close}
          >
            ×
          </button>
        </div>

        <div className={styles.summary}>
          <p className={styles.summaryLine}>{summary.line}</p>
          <p className={styles.summaryMeta}>{summary.meta}</p>
          {chips.length > 0 ? (
            <div className={styles.chips}>
              {chips.map((chip) => (
                <button
                  key={chip.id}
                  type="button"
                  onClick={() => onRemoveChip(chip.id)}
                  aria-label={`Remove ${chip.label}`}
                  className={styles.chip}
                >
                  {chip.label} ×
                </button>
              ))}
            </div>
          ) : null}
        </div>

        {children}
      </div>
    </div>
  );
}
