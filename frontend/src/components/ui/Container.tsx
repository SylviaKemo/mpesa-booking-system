import type { ElementType, ReactNode } from "react";
import styles from "./Container.module.css";

type ContainerProps = {
  /** Defaults to `div`; pass `header`, `section` etc. where it aids semantics. */
  as?: ElementType;
  className?: string;
  children: ReactNode;
};

/** Centres content at the site's max width and applies the page gutter. */
export function Container({ as: Tag = "div", className, children }: ContainerProps) {
  return (
    <Tag className={[styles.container, className].filter(Boolean).join(" ")}>
      {children}
    </Tag>
  );
}
