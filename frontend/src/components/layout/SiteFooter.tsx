import { SITE } from "@/data/site";
import styles from "./SiteFooter.module.css";

export function SiteFooter() {
  return (
    <footer className={styles.footer}>
      <p>{SITE.copyright}</p>
    </footer>
  );
}
