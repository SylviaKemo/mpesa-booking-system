import { ADDITIONS, SETS, type Addition, type LashSet, type Tier } from "@/data/services";

export type PickedTier = {
  set: LashSet;
  tier: Tier;
};

export type Selection = {
  picked: PickedTier | null;
  chosenAdds: Addition[];
  /** Combined price in KES. */
  amount: number;
  /** Combined chair time in minutes. */
  mins: number;
};

export function findTier(tierId: string | null): PickedTier | null {
  if (!tierId) return null;
  for (const set of SETS) {
    const tier = set.tiers.find((t) => t.id === tierId);
    if (tier) return { set, tier };
  }
  return null;
}

export function getSelection(tierId: string | null, addIds: string[]): Selection {
  const picked = findTier(tierId);
  const chosenAdds = ADDITIONS.filter((a) => addIds.includes(a.id));

  return {
    picked,
    chosenAdds,
    amount:
      (picked?.tier.amount ?? 0) + chosenAdds.reduce((n, a) => n + a.amount, 0),
    mins: (picked?.tier.mins ?? 0) + chosenAdds.reduce((n, a) => n + a.mins, 0),
  };
}

export type Summary = {
  line: string;
  meta: string;
};

/** The two-line description shown in the summary bar and the booking sheet. */
export function getSummary({ picked, chosenAdds, mins }: Selection): Summary {
  if (picked) {
    return {
      line: `${picked.set.name} · ${picked.tier.label}`,
      meta: chosenAdds.length
        ? `About ${mins} min · ${chosenAdds.map((a) => a.label).join(", ")}`
        : `About ${mins} min in the chair`,
    };
  }

  if (chosenAdds.length) {
    return {
      line: chosenAdds.map((a) => a.label).join(", "),
      meta: `About ${mins} min · add a set for the full look`,
    };
  }

  return { line: "Pick a volume to start", meta: "Nothing selected yet" };
}

/** Tier meta line, e.g. "25 min" or "20 min · for beginners". */
export function tierMeta(tier: Tier): string {
  return tier.note ? `${tier.mins} min · ${tier.note}` : `${tier.mins} min`;
}

/**
 * Half the total, rounded to the nearest 50 KES, never below 100.
 *
 * Mirrors the prototype's arithmetic. Note the written handoff says "rounded up
 * to the nearest 50", but the prototype rounds to nearest; the prototype wins.
 */
export function getDeposit(amount: number): number {
  return Math.max(100, Math.round((amount * 0.5) / 50) * 50);
}
