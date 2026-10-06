export type Testimonial = {
  quote: string;
  name: string;
  detail: string;
  rating: number;
};

export const TESTIMONIALS: Testimonial[] = [
  {
    quote:
      "Shamim gave me the confidence I didn't know I needed. These lashes are stunning and last forever.",
    name: "Grace M.",
    detail: "Regular client since 2023",
    rating: 5,
  },
  {
    quote:
      "The attention to detail is incredible. My lashes feel like they were designed just for me — because they were.",
    name: "Amina K.",
    detail: "First appointment this month",
    rating: 5,
  },
  {
    quote:
      "I came for lashes and stayed for the vibes. Shamim's salon feels like home.",
    name: "Victoria N.",
    detail: "Monthly appointments",
    rating: 5,
  },
];
