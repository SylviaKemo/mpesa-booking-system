"use client";

import { useCountdown } from "@/hooks/useCountdown";
import styles from "./Countdown.module.css";

const LABELS = ["Days", "Hours", "Minutes", "Seconds"] as const;

export function Countdown({ target }: { target: string }) {
  const units = useCountdown(target);

  // Placeholder for the pre-hydration frame; the boxes hold their size.
  const values = units
    ? [units.days, units.hours, units.minutes, units.seconds]
    : ["--", "--", "--", "--"];

  return (
    <div className={styles.countdown} role="timer" aria-label="Time until launch">
      {LABELS.map((label, i) => (
        <div key={label} className={styles.unit}>
          <div className={styles.box}>
            <span className={styles.value}>{values[i]}</span>
          </div>
          <span className={styles.label}>{label}</span>
        </div>
      ))}
    </div>
  );
}
