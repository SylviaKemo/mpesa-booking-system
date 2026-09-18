/**
 * Inline line icons, drawn to match the prototype's paths exactly.
 * Size and stroke weight come from the caller so one set serves every context.
 */

type IconProps = {
  size?: number;
  strokeWidth?: number;
  className?: string;
};

const base = (size: number, strokeWidth: number, className?: string) => ({
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth,
  width: size,
  height: size,
  className,
  "aria-hidden": true as const,
});

export function PinIcon({ size = 38, strokeWidth = 1.4, className }: IconProps) {
  return (
    <svg {...base(size, strokeWidth, className)}>
      <path d="M12 21s7-6.14 7-11a7 7 0 1 0-14 0c0 4.86 7 11 7 11z" />
      <circle cx="12" cy="10" r="2.6" />
    </svg>
  );
}

export function PhoneRectIcon({ size = 38, strokeWidth = 1.4, className }: IconProps) {
  return (
    <svg {...base(size, strokeWidth, className)}>
      <rect x="6.5" y="2.5" width="11" height="19" rx="2.2" />
      <line x1="10.5" y1="18.6" x2="13.5" y2="18.6" />
    </svg>
  );
}

export function InstagramIcon({ size = 38, strokeWidth = 1.4, className }: IconProps) {
  return (
    <svg {...base(size, strokeWidth, className)}>
      <rect x="3.5" y="3.5" width="17" height="17" rx="4.4" />
      <circle cx="12" cy="12" r="4" />
      <circle cx="16.8" cy="7.2" r="0.9" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function TikTokIcon({ size = 26, strokeWidth = 1.5, className }: IconProps) {
  return (
    <svg {...base(size, strokeWidth, className)}>
      <path d="M14.2 3.2v9.9a3.3 3.3 0 1 1-3.3-3.3" />
      <path d="M14.2 3.2c.4 2.3 2 3.8 4.3 4" />
    </svg>
  );
}

export function PhoneIcon({ size = 26, strokeWidth = 1.5, className }: IconProps) {
  return (
    <svg {...base(size, strokeWidth, className)}>
      <path d="M5 3.8h3.2l1.6 4-2 1.4a10.6 10.6 0 0 0 5 5l1.4-2 4 1.6V19a1.6 1.6 0 0 1-1.7 1.6A15.4 15.4 0 0 1 3.4 5.5 1.6 1.6 0 0 1 5 3.8z" />
    </svg>
  );
}

export function WhatsAppIcon({ size = 34, strokeWidth = 1.4, className }: IconProps) {
  return (
    <svg {...base(size, strokeWidth, className)}>
      <path d="M12 3a9 9 0 0 0-7.7 13.6L3.4 21l4.5-1.2A9 9 0 1 0 12 3z" />
      <path
        d="M9 9.4c0 3 2.1 5.1 5.1 5.1l1-1.2-1.7-1-.9.8c-1-.5-1.8-1.3-2.2-2.3l.8-.9-1-1.7-1.1.9z"
        fill="currentColor"
        stroke="none"
      />
    </svg>
  );
}
