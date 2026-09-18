import { MENU_STEPS } from "@/data/services";
import styles from "./ProgressSteps.module.css";

type ProgressStepsProps = {
  /** 1-based index of the step currently in progress. */
  current: number;
};

export function ProgressSteps({ current }: ProgressStepsProps) {
  return (
    <ol className={styles.steps}>
      {MENU_STEPS.map((step) => (
        <li
          key={step.n}
          className={[styles.step, step.n === current ? styles.active : ""]
            .filter(Boolean)
            .join(" ")}
          aria-current={step.n === current ? "step" : undefined}
        >
          <span className={styles.marker} aria-hidden="true">
            {step.n}
          </span>
          <span className={styles.label}>{step.label}</span>
        </li>
      ))}
    </ol>
  );
}
