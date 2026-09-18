import type { CSSProperties } from "react";
import styles from "./AmbientOrbs.module.css";

export type Orb = {
  /** Any subset of edge offsets, e.g. `{ top: "10%", left: "15%" }`. */
  position: Pick<CSSProperties, "top" | "right" | "bottom" | "left">;
  size: string;
  colour: string;
  /** Seconds. */
  duration: number;
  delay: number;
};

export const ABOUT_ORBS: Orb[] = [
  {
    position: { top: "10%", left: "15%" },
    size: "200px",
    colour: "rgba(187,148,87,0.25)",
    duration: 6,
    delay: 0,
  },
  {
    position: { bottom: "20%", right: "20%" },
    size: "280px",
    colour: "rgba(111,29,27,0.2)",
    duration: 8,
    delay: 1,
  },
  {
    position: { top: "40%", left: "40%" },
    size: "150px",
    colour: "rgba(187,148,87,0.15)",
    duration: 7,
    delay: 2,
  },
];

export const CONTACT_ORBS: Orb[] = [
  {
    position: { top: "12%", left: "14%" },
    size: "200px",
    colour: "rgba(187,148,87,0.22)",
    duration: 6,
    delay: 0,
  },
  {
    position: { bottom: "18%", right: "18%" },
    size: "280px",
    colour: "rgba(111,29,27,0.2)",
    duration: 8,
    delay: 1,
  },
  {
    position: { top: "45%", left: "42%" },
    size: "150px",
    colour: "rgba(187,148,87,0.14)",
    duration: 7,
    delay: 2,
  },
];

/** Soft drifting glows behind the content pages. Decorative only. */
export function AmbientOrbs({ orbs }: { orbs: Orb[] }) {
  return (
    <div className={styles.orbs} aria-hidden="true">
      {orbs.map((orb, i) => (
        <div
          key={i}
          className={styles.orb}
          style={
            {
              ...orb.position,
              width: orb.size,
              background: `radial-gradient(circle, ${orb.colour} 0%, transparent 70%)`,
              "--orb-duration": `${orb.duration}s`,
              "--orb-delay": `${orb.delay}s`,
            } as CSSProperties
          }
        />
      ))}
    </div>
  );
}
