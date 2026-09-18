export type Tier = {
  id: string;
  label: string;
  /** Chair time in minutes. */
  mins: number;
  /** Price in KES. */
  amount: number;
  note?: string;
};

export type LashSet = {
  id: string;
  name: string;
  blurb: string;
  img: string;
  alt: string;
  tiers: Tier[];
};

export type Addition = {
  id: string;
  label: string;
  amount: number;
  mins: number;
};

export const SETS: LashSet[] = [
  {
    id: "wispy",
    name: "Wispy set",
    blurb: "Textured, feathered spikes for a soft fluttery finish.",
    img: "https://swiftill.co.ke/uploads/businesses/katiani-styles/services/basic-wispy/1de49dea14664f6588b3c30dda5455a4.jpeg",
    alt: "Wispy lash set",
    tiers: [
      { id: "wispy-basic", label: "Basic", mins: 20, amount: 600 },
      { id: "wispy-mid", label: "Mid volume", mins: 25, amount: 700 },
      { id: "wispy-vol", label: "Volume", mins: 30, amount: 800 },
    ],
  },
  {
    id: "cat",
    name: "Cat eye",
    blurb: "Length pushed to the outer corner for a lifted, elongated eye.",
    img: "https://swiftill.co.ke/uploads/businesses/katiani-styles/services/basiccat-eye/49424dc25df240d99faf214406ef98a1.jpeg",
    alt: "Cat eye lash set",
    tiers: [
      { id: "cat-basic", label: "Basic", mins: 20, amount: 600 },
      { id: "cat-mid", label: "Mid volume", mins: 25, amount: 700 },
      { id: "cat-vol", label: "Volume", mins: 30, amount: 900 },
    ],
  },
  {
    id: "classic",
    name: "Classic set",
    blurb:
      "One extension per natural lash — a simple, natural set. Best place to start.",
    img: "https://swiftill.co.ke/uploads/businesses/katiani-styles/services/mid-vol-classic/f3875edac0014d6fa2ecc06eb8426ef2.jpeg",
    alt: "Classic lash set",
    tiers: [
      {
        id: "classic",
        label: "Classic",
        mins: 20,
        amount: 600,
        note: "for beginners",
      },
    ],
  },
];

export const ADDITIONS: Addition[] = [
  { id: "removal", label: "Removal", amount: 300, mins: 15 },
  { id: "charms", label: "Lash charms", amount: 100, mins: 5 },
  { id: "colour", label: "Colour add-ons", amount: 100, mins: 5 },
  { id: "glitter", label: "Glitter spikes", amount: 100, mins: 5 },
];

/** The additions card sits last in the grid and mirrors a set card's shape. */
export const ADDITIONS_CARD = {
  name: "Additions",
  blurb: "Pick as many as you like — these stack on top of your set.",
  img: "https://swiftill.co.ke/uploads/businesses/katiani-styles/services/lash-removal/f1262cc673a8498c84a592c39a64cb7b.jpeg",
  alt: "Lash additions and removal",
} as const;

export const MENU_STEPS = [
  { n: 1, label: "Pick a volume" },
  { n: 2, label: "Add extras" },
  { n: 3, label: "Book" },
] as const;
