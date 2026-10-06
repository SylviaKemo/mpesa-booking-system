export type NavLink = {
  label: string;
  href: string;
};

/** Order matters: the first three sit left of the brand mark, the rest sit right. */
export const NAV_LINKS: NavLink[] = [
  { label: "Home", href: "/" },
  { label: "Services", href: "/services" },
  { label: "Shop", href: "/shop" },
  { label: "About", href: "/about" },
  { label: "Contact", href: "/contact" },
];

export const NAV_SPLIT_INDEX = 3;

export const SITE = {
  name: "Shamim Styles",
  handle: "theeshamimeffect",
  tagline: "Let's get lashed shall we ?",
  monogram: "S",
  phoneDisplay: "0794 931 394",
  phoneHref: "tel:+254794931394",
  whatsappHref: "https://wa.me/254794931394",
  instagramHref: "https://instagram.com/theeshamimeffect",
  tiktokHref: "https://tiktok.com/@theeshamimeffect",
  addressLines: ["RNG Plaza, Umoja", "Nairobi, Kenya"],
  copyright: "© 2026 Shamim Styles. Located in RNG Plaza or Umoja, Nairobi.",
} as const;

export const WORKING_HOURS = [
  { days: "Mon – Fri", hours: "9.00 – 19.00", closed: false },
  { days: "Saturday", hours: "9.00 – 18.00", closed: false },
  { days: "Sunday", hours: "Closed", closed: true },
] as const;

/** Shop launch target used by the countdown. */
export const SHOP_LAUNCH_DATE = "2026-11-01T09:00:00+03:00";

export const HOME_HERO = {
  image:
    "https://swiftill.co.ke/uploads/businesses/katiani-styles/services/basic-wispy/1de49dea14664f6588b3c30dda5455a4.jpeg",
  alt: "Lash artistry close-up",
} as const;

export const ABOUT_PORTRAIT = {
  /** 960x1280 — exactly the 3:4 the About portrait slot expects, so nothing crops. */
  image: "/images/shamim-portrait.jpg",
  alt: "Shamim, founder of Shamim Styles",
} as const;
