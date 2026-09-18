"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV_LINKS, NAV_SPLIT_INDEX, SITE } from "@/data/site";
import styles from "./SiteNav.module.css";

/**
 * `hero`     — transparent, sits over the hero image
 * `bordered` — hairline rule, used on the services menu
 * `sticky`   — pinned and frosted, for long scrolling pages
 * `warm`     — cream rules for the maroon shop page
 */
export type NavVariant = "hero" | "bordered" | "sticky" | "warm";

type SiteNavProps = {
  variant?: NavVariant;
};

export function SiteNav({ variant = "hero" }: SiteNavProps) {
  const pathname = usePathname();
  const left = NAV_LINKS.slice(0, NAV_SPLIT_INDEX);
  const right = NAV_LINKS.slice(NAV_SPLIT_INDEX);

  const renderGroup = (links: typeof NAV_LINKS) => (
    <div className={styles.group}>
      {links.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          aria-current={pathname === link.href ? "page" : undefined}
          className={[styles.link, pathname === link.href ? styles.active : ""]
            .filter(Boolean)
            .join(" ")}
        >
          {link.label}
        </Link>
      ))}
    </div>
  );

  return (
    <nav aria-label="Primary" className={`${styles.nav} ${styles[variant]}`}>
      {renderGroup(left)}
      <div className={styles.brand}>
        <Link href="/" aria-label={`${SITE.name} home`} className={styles.monogram}>
          {SITE.monogram}
        </Link>
      </div>
      {renderGroup(right)}
    </nav>
  );
}
