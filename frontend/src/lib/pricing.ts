import type { Addition, Catalogue, LashSet, Tier } from "@/lib/api";

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

export function findTier(
  catalogue: Catalogue,
  tierId: string | null,
): PickedTier | null {
  if (!tierId) return null;
  for (const set of catalogue.sets) {
    const tier = set.tiers.find((t) => t.id === tierId);
    if (tier) return { set, tier };
  }
  return null;
}

export function getSelection(
  catalogue: Catalogue,
  tierId: string | null,
  addIds: string[],
): Selection {
  const picked = findTier(catalogue, tierId);
  const chosenAdds = catalogue.additions.filter((a) => addIds.includes(a.id));

  return {
    picked,
    chosenAdds,
    amount:
      (picked?.tier.amount_kes ?? 0) +
      chosenAdds.reduce((n, a) => n + a.amount_kes, 0),
    mins:
      (picked?.tier.minutes ?? 0) + chosenAdds.reduce((n, a) => n + a.minutes, 0),
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
  return tier.note ? `${tier.minutes} min · ${tier.note}` : `${tier.minutes} min`;
}

/**
 * Half the total to the nearest 50 KES, floored at 100.
 *
 * Shown before submitting so the client knows what they are agreeing to. The
 * server recomputes it from its own catalogue and that figure is the one
 * charged; this must agree with it, so the arithmetic is integer-only and
 * matches the backend's deposit_for exactly.
 */
export function getDeposit(amount: number): number {
  const halfSteps = Math.floor((2 * amount + 100) / 200);
  return Math.max(100, halfSteps * 50);
}
