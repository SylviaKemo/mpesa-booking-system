import type { Metadata } from "next";
import Image from "next/image";
import { TestimonialCard } from "@/components/about/TestimonialCard";
import { ABOUT_ORBS, AmbientOrbs } from "@/components/layout/AmbientOrbs";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { SiteNav } from "@/components/layout/SiteNav";
import { Container } from "@/components/ui/Container";
import { CtaBanner } from "@/components/ui/CtaBanner";
import { ABOUT_PORTRAIT } from "@/data/site";
import { TESTIMONIALS } from "@/data/testimonials";
import styles from "./page.module.css";

export const metadata: Metadata = {
  title: "About",
  description:
    "How Shamim Styles began, and what clients say about the lashes — theeshamimeffect.",
};

export default function AboutPage() {
  return (
    <div className={styles.page}>
      <AmbientOrbs orbs={ABOUT_ORBS} />

      <div className={styles.content}>
        <SiteNav variant="sticky" />

        <Container gutter="wide" className={styles.main}>
          <section className={styles.story}>
            <div className={styles.portrait}>
              <Image
                src={ABOUT_PORTRAIT.image}
                alt={ABOUT_PORTRAIT.alt}
                fill
                sizes="(max-width: 768px) 100vw, 560px"
                className={styles.portraitImage}
              />
            </div>
            <div>
              <h2 className={styles.storyTitle}>A Passion Ignited</h2>
              <div className={styles.storyBody}>
                <p>
                  Shamim fell in love with lashes years ago — not just the
                  transformation, but the artistry. Every set is a conversation. Every
                  volume, every curve, tells the story of the person wearing them.
                </p>
                <p>
                  After training extensively in lash application and design, Shamim
                  realized that beauty salons often missed the mark: they treated
                  lashes as a service, not a craft. So she built{" "}
                  <strong className={styles.highlight}>Shamim Styles</strong> — a
                  sanctuary where precision meets passion.
                </p>
                <p>
                  Today, every client who walks through the door doesn&apos;t just get
                  lashes. They get{" "}
                  <em className={styles.highlight}>theeshamimeffect</em>: lashes that
                  last, that move, that make you feel like the best version of
                  yourself.
                </p>
              </div>
            </div>
          </section>

          <section className={styles.testimonials}>
            <h2 className={styles.sectionTitle}>What Clients Say</h2>
            <div className={styles.testimonialGrid}>
              {TESTIMONIALS.map((testimonial) => (
                <TestimonialCard key={testimonial.name} {...testimonial} />
              ))}
            </div>
          </section>

          <CtaBanner description="Your next lash look is waiting. Book a consultation and let's create something that feels like you." />
        </Container>

        <SiteFooter />
      </div>
    </div>
  );
}
