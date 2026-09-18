import Link from "next/link";
import type { ReactNode } from "react";
import styles from "./ContactPieces.module.css";

type InfoItemProps = {
  icon: ReactNode;
  label: string;
  children: ReactNode;
};

export function InfoItem({ icon, label, children }: InfoItemProps) {
  return (
    <div className={styles.info}>
      {icon}
      <div className={styles.infoLabel}>{label}</div>
      <p className={styles.infoValue}>{children}</p>
    </div>
  );
}

type SocialCardProps = {
  icon: ReactNode;
  label: string;
  value: string;
  href: string;
};

export function SocialCard({ icon, label, value, href }: SocialCardProps) {
  const external = href.startsWith("http");
  const content = (
    <>
      <span className={styles.socialIcon}>{icon}</span>
      <span>
        <span className={styles.socialLabel}>
          {label}
        </span>
        <span className={styles.socialValue}>
          {value}
        </span>
      </span>
    </>
  );

  return external ? (
    <a
      href={href}
      target="_blank"
      rel="noreferrer noopener"
      className={styles.social}
    >
      {content}
    </a>
  ) : (
    <Link href={href} className={styles.social}>
      {content}
    </Link>
  );
}
