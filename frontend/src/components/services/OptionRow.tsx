"use client";

import { money } from "@/lib/format";
import styles from "./OptionRow.module.css";

type OptionRowProps = {
  /** `radio` for one-of-many tiers, `checkbox` for stackable additions. */
  kind: "radio" | "checkbox";
  label: string;
  meta?: string;
  amount: number;
  selected: boolean;
  onToggle: () => void;
};

export function OptionRow({
  kind,
  label,
  meta,
  amount,
  selected,
  onToggle,
}: OptionRowProps) {
  return (
    <button
      type="button"
      role={kind}
      aria-checked={selected}
      onClick={onToggle}
      className={[styles.row, styles[kind], selected ? styles.selected : ""]
        .filter(Boolean)
        .join(" ")}
    >
      <span className={styles.indicator} aria-hidden="true">
        <span className={styles.dot} />
      </span>
      <span className={styles.text}>
        <span className={styles.label}>{label}</span>
        {meta ? <span className={styles.meta}>{meta}</span> : null}
      </span>
      <span className={styles.price}>{money(amount)}</span>
    </button>
  );
}
