import Image from "next/image";
import { Button } from "@/components/ui/Button";
import { SiteNav } from "@/components/layout/SiteNav";
import { HOME_HERO, SITE } from "@/data/site";
import styles from "./Hero.module.css";

export function Hero() {
  return (
    <section className={styles.hero}>
      <Image
        src={HOME_HERO.image}
        alt={HOME_HERO.alt}
        fill
        priority
        sizes="100vw"
        className={styles.image}
      />
      <div className={styles.scrim} aria-hidden="true" />

      <SiteNav variant="hero" />

      <div className={styles.content}>
        <p className={styles.eyebrow}>{SITE.handle}</p>
        <h1 className={styles.headline}>{SITE.name}</h1>
        <p className={styles.tagline}>{SITE.tagline}</p>

        <div className={styles.actions}>
          <Button href="/services">Book appointment</Button>
          <Button href="/shop" variant="outline">
            Shop lashes
          </Button>
        </div>
      </div>
    </section>
  );
}
