import Link from "next/link";
import type { AnchorHTMLAttributes, ButtonHTMLAttributes } from "react";
import styles from "./Button.module.css";

export type ButtonVariant = "primary" | "outline";

/** `hero` is the default page-level padding; `bar` fits the sticky summary bar. */
export type ButtonSize = "hero" | "bar";

type CommonProps = {
  variant?: ButtonVariant;
  size?: ButtonSize;
  className?: string;
  children: React.ReactNode;
};

type ButtonAsLink = CommonProps & {
  href: string;
} & Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "href" | "className" | "children">;

type ButtonAsButton = CommonProps & {
  href?: undefined;
} & Omit<ButtonHTMLAttributes<HTMLButtonElement>, "className" | "children">;

export type ButtonProps = ButtonAsLink | ButtonAsButton;

/**
 * Pill action used across the site. Renders a Next `Link` when `href` is set,
 * otherwise a native `button`, so callers never have to pick the element.
 */
export function Button({
  variant = "primary",
  size = "hero",
  className,
  children,
  ...rest
}: ButtonProps) {
  const classes = [
    styles.base,
    styles[variant],
    size === "bar" ? styles.bar : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  if (typeof rest.href === "string") {
    const { href, ...anchorProps } = rest as ButtonAsLink;
    return (
      <Link href={href} className={classes} {...anchorProps}>
        {children}
      </Link>
    );
  }

  const { type = "button", ...buttonProps } = rest as ButtonAsButton;
  return (
    <button type={type} className={classes} {...buttonProps}>
      {children}
    </button>
  );
}
