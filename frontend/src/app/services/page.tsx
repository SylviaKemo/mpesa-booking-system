import type { Metadata } from "next";
import { SiteNav } from "@/components/layout/SiteNav";
import { ProgressSteps } from "@/components/services/ProgressSteps";
import { ServicesMenu } from "@/components/services/ServicesMenu";
import { Container } from "@/components/ui/Container";
import styles from "./page.module.css";

export const metadata: Metadata = {
  title: "Services",
  description:
    "Wispy, cat eye and classic lash sets with optional removal, charms, colour and glitter. Pick a volume and book.",
};

export default function ServicesPage() {
  return (
    <div className={styles.page}>
      <SiteNav variant="bordered" />

      <Container as="header" className={styles.header}>
        <p className={styles.eyebrow}>Lash menu</p>
        <h1 className={styles.title}>Choose your set</h1>
        <p className={styles.intro}>
          Pick one volume from a set, then add any extras. Your total and chair time
          build up as you go.
        </p>
        <ProgressSteps current={1} />
      </Container>

      <ServicesMenu />
    </div>
  );
}
