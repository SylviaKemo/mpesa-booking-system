import type { Metadata, Viewport } from "next";
import { Merriweather, Rubik } from "next/font/google";
import { SITE } from "@/data/site";
import "@/styles/globals.css";

const merriweather = Merriweather({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-merriweather",
  display: "swap",
});

const rubik = Rubik({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
  variable: "--font-rubik",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: `${SITE.name} — Lash artistry in Nairobi`,
    template: `%s — ${SITE.name}`,
  },
  description:
    "Lash sets, volumes and add-ons by Shamim Styles in Nairobi. Pick your set and book a slot in under a minute.",
};

export const viewport: Viewport = {
  themeColor: "#14100c",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${merriweather.variable} ${rubik.variable}`}>
      <body>{children}</body>
    </html>
  );
}
