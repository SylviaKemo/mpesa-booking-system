import type { ElementType, ReactNode } from "react";
import styles from "./Container.module.css";

type ContainerProps = {
  /** Defaults to `div`; pass `header`, `section` etc. where it aids semantics. */
  as?: ElementType;
  /** The services menu uses the narrower gutter; content pages use the wider one. */
  gutter?: "narrow" | "wide";
  className?: string;
  children: ReactNode;
};

/** Centres content at the site's max width and applies the page gutter. */
export function Container({
  as: Tag = "div",
  gutter = "narrow",
  className,
  children,
}: ContainerProps) {
  return (
    <Tag
      className={[styles.container, styles[gutter], className]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </Tag>
  );
}
