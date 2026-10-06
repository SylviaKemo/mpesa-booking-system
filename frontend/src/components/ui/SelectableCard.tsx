import styles from "./SelectableCard.module.css";

type SelectableCardProps = {
  title: string;
  meta: string;
  selected: boolean;
  onSelect: () => void;
};

/** Bordered radio-style panel used for the deposit choice. */
export function SelectableCard({
  title,
  meta,
  selected,
  onSelect,
}: SelectableCardProps) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={selected}
      onClick={onSelect}
      className={[styles.card, selected ? styles.selected : ""]
        .filter(Boolean)
        .join(" ")}
    >
      <span className={styles.title}>{title}</span>
      <span className={styles.meta}>{meta}</span>
    </button>
  );
}
