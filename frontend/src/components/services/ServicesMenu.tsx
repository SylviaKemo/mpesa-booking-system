"use client";

import { useMemo, useState } from "react";
import { Container } from "@/components/ui/Container";
import type { Catalogue } from "@/lib/api";
import { useBooking } from "@/hooks/useBooking";
import { getSelection, getSummary, tierMeta } from "@/lib/pricing";
import { BookingFlow } from "./booking/BookingFlow";
import { OptionRow } from "./OptionRow";
import { ServiceCard } from "./ServiceCard";
import { SummaryBar } from "./SummaryBar";
import styles from "./ServicesMenu.module.css";

export function ServicesMenu({ catalogue }: { catalogue: Catalogue }) {
  const [tierId, setTierId] = useState<string | null>(null);
  const [addIds, setAddIds] = useState<string[]>([]);

  const selection = useMemo(
    () => getSelection(catalogue, tierId, addIds),
    [catalogue, tierId, addIds],
  );
  const summary = useMemo(() => getSummary(selection), [selection]);

  const booking = useBooking(selection.amount, { tierId, addIds });

  const toggleAddition = (id: string) =>
    setAddIds((current) =>
      current.includes(id) ? current.filter((x) => x !== id) : [...current, id],
    );

  return (
    <>
      <Container className={styles.grid}>
        {catalogue.sets.map((set) => (
          <ServiceCard
            key={set.id}
            name={set.name}
            blurb={set.blurb}
            img={set.image_url}
            alt={set.image_alt}
            optionsRole="radiogroup"
            optionsLabel={`${set.name} volumes`}
          >
            {set.tiers.map((tier) => (
              <OptionRow
                key={tier.id}
                kind="radio"
                label={tier.label}
                meta={tierMeta(tier)}
                amount={tier.amount_kes}
                selected={tierId === tier.id}
                onToggle={() => setTierId(tier.id)}
              />
            ))}
          </ServiceCard>
        ))}

        <ServiceCard
          name={catalogue.additions_card.name}
          blurb={catalogue.additions_card.blurb}
          img={catalogue.additions_card.image_url}
          alt={catalogue.additions_card.image_alt}
          optionsRole="group"
          optionsLabel="Additions"
        >
          {catalogue.additions.map((addition) => (
            <OptionRow
              key={addition.id}
              kind="checkbox"
              label={addition.label}
              amount={addition.amount_kes}
              selected={addIds.includes(addition.id)}
              onToggle={() => toggleAddition(addition.id)}
            />
          ))}
        </ServiceCard>
      </Container>

      <SummaryBar
        summary={summary}
        amount={selection.amount}
        canBook={selection.picked !== null}
        onBook={booking.open}
      />

      {booking.isOpen ? (
        <BookingFlow
          booking={booking}
          summary={summary}
          amount={selection.amount}
          chips={selection.chosenAdds}
          onRemoveChip={toggleAddition}
        />
      ) : null}
    </>
  );
}
