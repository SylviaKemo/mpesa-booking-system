import { SITE } from "@/data/site";
import styles from "./SiteFooter.module.css";

type SiteFooterProps = {
  /** `warm` is the cream-ruled treatment used on the maroon shop page. */
  variant?: "default" | "warm";
};

export function SiteFooter({ variant = "default" }: SiteFooterProps) {
  return (
    <footer className={`${styles.footer} ${styles[variant]}`}>
      <p>{SITE.copyright}</p>
    </footer>
  );
}
