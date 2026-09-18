import { Button } from "./Button";
import styles from "./CtaBanner.module.css";

type CtaBannerProps = {
  title?: string;
  description: string;
  ctaLabel?: string;
  href?: string;
};

/** The "Ready to Get Lashed?" panel that closes the About and Contact pages. */
export function CtaBanner({
  title = "Ready to Get Lashed?",
  description,
  ctaLabel = "Book Your Appointment",
  href = "/services",
}: CtaBannerProps) {
  return (
    <section className={styles.banner}>
      <h2 className={styles.title}>{title}</h2>
      <p className={styles.description}>{description}</p>
      <Button href={href}>{ctaLabel}</Button>
    </section>
  );
}
