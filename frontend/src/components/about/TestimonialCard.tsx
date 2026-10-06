import type { Testimonial } from "@/data/testimonials";
import styles from "./TestimonialCard.module.css";

export function TestimonialCard({ quote, name, detail, rating }: Testimonial) {
  return (
    <figure className={styles.card}>
      <div className={styles.stars} aria-label={`${rating} out of 5 stars`}>
        {Array.from({ length: rating }, (_, i) => (
          <span key={i} aria-hidden="true">
            ★
          </span>
        ))}
      </div>
      <blockquote className={styles.quote}>{quote}</blockquote>
      <figcaption>
        <p className={styles.name}>{name}</p>
        <p className={styles.detail}>{detail}</p>
      </figcaption>
    </figure>
  );
}
