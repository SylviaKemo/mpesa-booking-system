import type { Metadata } from "next";
import Link from "next/link";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { SiteNav } from "@/components/layout/SiteNav";
import { Countdown } from "@/components/shop/Countdown";
import { NotifyForm } from "@/components/shop/NotifyForm";
import { ShopOrbs } from "@/components/shop/ShopOrbs";
import { SHOP_LAUNCH_DATE } from "@/data/site";
import styles from "./page.module.css";

export const metadata: Metadata = {
  title: "Shop",
  description:
    "Reusable strip lashes and customized sets, coming soon from Shamim Styles. Leave your number and we'll text you first.",
};

export default function ShopPage() {
  return (
    <div className={styles.page}>
      <ShopOrbs />

      <div className={styles.content}>
        <SiteNav variant="warm" />

        <main className={styles.main}>
          <div className={styles.slabs}>
            <div className={`${styles.slab} ${styles.slabDark}`}>
              <h1 className={styles.title}>Coming soon</h1>
            </div>
            <div className={`${styles.slab} ${styles.slabLight}`}>
              <p className={styles.subtitle}>Strip &amp; custom lashes</p>
            </div>
          </div>

          <Countdown target={SHOP_LAUNCH_DATE} />

          <p className={styles.copy}>
            Reusable strip lashes and customized sets mapped to your eye. Drop your
            number and we&apos;ll text you first.
          </p>

          <NotifyForm />

          <Link href="/" className={styles.back}>
            Back to homepage
          </Link>
        </main>

        <SiteFooter variant="warm" />
      </div>
    </div>
  );
}
