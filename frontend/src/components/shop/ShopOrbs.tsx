import type { CSSProperties } from "react";
import styles from "./ShopOrbs.module.css";

const ORBS = [
  { cx: 8, cy: 12, r: 16, fill: "rgba(187,148,87,0.22)", opacity: 0.6, duration: 8, delay: 0 },
  { cx: 92, cy: 80, r: 22, fill: "rgba(111,29,27,0.26)", opacity: 0.55, duration: 10, delay: 1.5 },
  { cx: 72, cy: 20, r: 14, fill: "rgba(187,148,87,0.18)", opacity: 0.5, duration: 9, delay: 3 },
];

/**
 * Blurred drifting circles behind the shop page. Uses an SVG filter rather than
 * the CSS gradients the content pages use, which is what gives the softer glow.
 */
export function ShopOrbs() {
  return (
    <svg
      className={styles.orbs}
      viewBox="0 0 100 100"
      preserveAspectRatio="xMidYMid slice"
      aria-hidden="true"
    >
      <defs>
        <filter id="shop-orb-glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="2" result="blurred" />
          <feMerge>
            <feMergeNode in="blurred" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      {ORBS.map((orb, i) => (
        <circle
          key={i}
          cx={orb.cx}
          cy={orb.cy}
          r={orb.r}
          fill={orb.fill}
          opacity={orb.opacity}
          filter="url(#shop-orb-glow)"
          className={styles.orb}
          style={
            {
              "--orb-duration": `${orb.duration}s`,
              "--orb-delay": `${orb.delay}s`,
            } as CSSProperties
          }
        />
      ))}
    </svg>
  );
}
