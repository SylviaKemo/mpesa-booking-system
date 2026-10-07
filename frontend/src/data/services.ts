/**
 * UI-only catalogue constants.
 *
 * The sets, tiers, additions and slots now come from the API — the server is
 * the price authority, and a copy here could disagree with what it charges.
 * Only the menu's own step labels remain.
 */

export const MENU_STEPS = [
  { n: 1, label: "Pick a volume" },
  { n: 2, label: "Add extras" },
  { n: 3, label: "Book" },
] as const;
