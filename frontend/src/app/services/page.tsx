import type { Metadata } from "next";
import { SiteNav } from "@/components/layout/SiteNav";
import { ProgressSteps } from "@/components/services/ProgressSteps";
import { ServicesMenu } from "@/components/services/ServicesMenu";
import { Container } from "@/components/ui/Container";
import { ApiError, getCatalogue, type Catalogue } from "@/lib/api";
import styles from "./page.module.css";

export const metadata: Metadata = {
  title: "Services",
  description:
    "Wispy, cat eye and classic lash sets with optional removal, charms, colour and glitter. Pick a volume and book.",
};

// The menu lives in the database now, so this cannot be baked at build time.
export const dynamic = "force-dynamic";

export default async function ServicesPage() {
  let catalogue: Catalogue | null = null;
  let loadError: string | null = null;

  try {
    catalogue = await getCatalogue();
  } catch (error) {
    // The page still renders its heading and the reason, rather than a crash:
    // somebody looking at a blank screen cannot tell a broken deploy from a
    // slow one.
    loadError =
      error instanceof ApiError
        ? error.message
        : "The lash menu could not be loaded.";
  }

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

      {catalogue ? (
        <ServicesMenu catalogue={catalogue} />
      ) : (
        <Container as="section" className={styles.header}>
          <p className={styles.intro} role="status">
            {loadError} Please try again in a moment.
          </p>
        </Container>
      )}
    </div>
  );
}
