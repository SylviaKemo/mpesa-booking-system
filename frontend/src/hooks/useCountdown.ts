"use client";

import { useEffect, useState } from "react";

export type CountdownUnits = {
  days: string;
  hours: string;
  minutes: string;
  seconds: string;
};

const pad = (n: number) => String(n).padStart(2, "0");

function split(remainingMs: number): CountdownUnits {
  const s = Math.floor(Math.max(0, remainingMs) / 1000);
  return {
    days: pad(Math.floor(s / 86400)),
    hours: pad(Math.floor(s / 3600) % 24),
    minutes: pad(Math.floor(s / 60) % 60),
    seconds: pad(s % 60),
  };
}

/**
 * Ticks once a second toward `target`, and stops at zero.
 *
 * Returns null until mounted: the remaining time differs between the server
 * render and the client, so rendering it during hydration would mismatch.
 * Callers show a placeholder for that first frame.
 */
export function useCountdown(target: string | Date): CountdownUnits | null {
  const [units, setUnits] = useState<CountdownUnits | null>(null);

  useEffect(() => {
    const targetMs = new Date(target).getTime();
    if (Number.isNaN(targetMs)) return;

    const tick = () => setUnits(split(targetMs - Date.now()));
    tick();

    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [target]);

  return units;
}
