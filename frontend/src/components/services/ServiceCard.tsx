"use client";

import Image from "next/image";
import type { ReactNode } from "react";
import styles from "./ServiceCard.module.css";

type ServiceCardProps = {
  name: string;
  blurb: string;
  img: string;
  alt: string;
  /** Accessible grouping label for the options list. */
  optionsLabel: string;
  optionsRole: "radiogroup" | "group";
  children: ReactNode;
};

/** Shared shell for a lash set and for the additions card — same shape, different options. */
export function ServiceCard({
  name,
  blurb,
  img,
  alt,
  optionsLabel,
  optionsRole,
  children,
}: ServiceCardProps) {
  return (
    <article className={styles.card}>
      <div className={styles.media}>
        <Image
          src={img}
          alt={alt}
          fill
          sizes="(max-width: 700px) 100vw, (max-width: 1180px) 50vw, 380px"
          className={styles.image}
        />
      </div>
      <div className={styles.body}>
        <h2 className={styles.title}>{name}</h2>
        <p className={styles.blurb}>{blurb}</p>
        <div className={styles.options} role={optionsRole} aria-label={optionsLabel}>
          {children}
        </div>
      </div>
    </article>
  );
}
