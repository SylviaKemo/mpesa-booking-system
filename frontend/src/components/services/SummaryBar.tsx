"use client";

import { Button } from "@/components/ui/Button";
import { Container } from "@/components/ui/Container";
import { money } from "@/lib/format";
import type { Summary } from "@/lib/pricing";
import styles from "./SummaryBar.module.css";

type SummaryBarProps = {
  summary: Summary;
  amount: number;
  /** Booking is only offered once a tier is chosen. */
  canBook: boolean;
  onBook: () => void;
};

export function SummaryBar({ summary, amount, canBook, onBook }: SummaryBarProps) {
  return (
    <div className={styles.bar}>
      <Container className={styles.inner}>
        <div className={styles.summary}>
          <p className={styles.line}>{summary.line}</p>
          <p className={styles.meta}>{summary.meta}</p>
        </div>
        <div className={styles.actions}>
          <p className={styles.total}>{money(amount)}</p>
          <Button size="bar" disabled={!canBook} onClick={onBook}>
            Book appointment
          </Button>
        </div>
      </Container>
    </div>
  );
}
