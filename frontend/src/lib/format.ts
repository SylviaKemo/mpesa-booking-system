/**
 * Formats a KES amount as "Ksh 3,000".
 *
 * Deliberately does not use `toLocaleString`: the services menu renders on the
 * server and hydrates on the client, and locale data can differ between the two,
 * which produces a hydration mismatch. Manual grouping is identical everywhere.
 */
export function money(amount: number): string {
  const grouped = Math.round(amount)
    .toString()
    .replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return `Ksh ${grouped}`;
}
