import type { Metadata } from "next";
import { InfoItem, SocialCard } from "@/components/contact/ContactPieces";
import {
  InstagramIcon,
  PhoneIcon,
  PhoneRectIcon,
  PinIcon,
  TikTokIcon,
  WhatsAppIcon,
} from "@/components/contact/icons";
import { AmbientOrbs, CONTACT_ORBS } from "@/components/layout/AmbientOrbs";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { SiteNav } from "@/components/layout/SiteNav";
import { Container } from "@/components/ui/Container";
import { CtaBanner } from "@/components/ui/CtaBanner";
import { SITE, WORKING_HOURS } from "@/data/site";
import styles from "./page.module.css";

export const metadata: Metadata = {
  title: "Contact",
  description:
    "Find Shamim Styles in Nairobi — address, opening hours, WhatsApp and socials.",
};

export default function ContactPage() {
  return (
    <div className={styles.page}>
      <AmbientOrbs orbs={CONTACT_ORBS} />

      <div className={styles.content}>
        <SiteNav variant="sticky" />

        <Container gutter="wide" className={styles.main}>
          <section className={styles.intro}>
            <div className={styles.eyebrow}>Get in touch</div>
            <h1 className={styles.title}>Contact Us</h1>
            <p className={styles.lead}>
              Questions about a set, a booking, or lash aftercare? Reach out — we
              answer fast.
            </p>
          </section>

          <section className={styles.infoRow}>
            <InfoItem icon={<PinIcon />} label="Address">
              {SITE.addressLines[0]}
              <br />
              {SITE.addressLines[1]}
            </InfoItem>
            <InfoItem icon={<PhoneRectIcon />} label="Phone">
              <a href={SITE.phoneHref}>{SITE.phoneDisplay}</a>
            </InfoItem>
            <InfoItem icon={<InstagramIcon />} label="Social">
              @{SITE.handle}
            </InfoItem>
          </section>

          <section className={styles.panel}>
            <div className={styles.column}>
              <h2 className={styles.columnTitle}>Working Hours</h2>
              <div className={styles.columnList}>
                {WORKING_HOURS.map((row) => (
                  <p key={row.days}>
                    {row.days}:{" "}
                    <strong className={row.closed ? styles.closed : styles.strong}>
                      {row.hours}
                    </strong>
                  </p>
                ))}
              </div>
            </div>

            <div className={styles.column}>
              <h2 className={styles.columnTitle}>Location</h2>
              <div className={styles.columnList}>
                <p>
                  RNG Plaza or Umoja,
                  <br />
                  Nairobi, Kenya
                </p>
                <a href={SITE.phoneHref} className={styles.phoneLink}>
                  {SITE.phoneDisplay}
                </a>
              </div>
            </div>

            <div className={styles.columnCentred}>
              <WhatsAppIcon className={styles.whatsappIcon} />
              <h2 className={`${styles.columnTitle} ${styles.whatsappTitle}`}>
                Questions?
              </h2>
              <p className={styles.whatsappCopy}>
                Message us on WhatsApp for an instant reply.
              </p>
              <a
                href={SITE.whatsappHref}
                target="_blank"
                rel="noreferrer noopener"
                className={styles.whatsappButton}
              >
                {SITE.phoneDisplay}
              </a>
            </div>
          </section>

          <section className={styles.socials}>
            <SocialCard
              icon={<InstagramIcon size={26} strokeWidth={1.5} />}
              label="Instagram"
              value={`@${SITE.handle}`}
              href={SITE.instagramHref}
            />
            <SocialCard
              icon={<TikTokIcon />}
              label="TikTok"
              value={`@${SITE.handle}`}
              href={SITE.tiktokHref}
            />
            <SocialCard
              icon={<PhoneIcon />}
              label="Call"
              value={SITE.phoneDisplay}
              href={SITE.phoneHref}
            />
          </section>

          <CtaBanner description="Skip the back-and-forth — pick your set and book a slot in under a minute." />
        </Container>

        <SiteFooter />
      </div>
    </div>
  );
}
