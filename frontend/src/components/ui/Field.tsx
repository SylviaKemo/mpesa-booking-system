import { useId } from "react";
import styles from "./Field.module.css";

type BaseProps = {
  label: string;
  /** Renders a dimmed "(optional)" after the label. */
  optional?: boolean;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
};

type FieldProps = BaseProps &
  (
    | { as?: "input"; type?: "text" | "tel"; rows?: never }
    | { as: "textarea"; type?: never; rows?: number }
  );

/** Labelled text input or textarea, styled from the shared token set. */
export function Field({
  label,
  optional,
  value,
  onChange,
  placeholder,
  ...rest
}: FieldProps) {
  const id = useId();
  const shared = {
    id,
    value,
    placeholder,
    className: styles.control,
    onChange: (
      e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
    ) => onChange(e.target.value),
  };

  return (
    <div className={styles.field}>
      <label className={styles.label} htmlFor={id}>
        {label}
        {optional ? <span className={styles.optional}> (optional)</span> : null}
      </label>
      {rest.as === "textarea" ? (
        <textarea {...shared} rows={rest.rows ?? 2} />
      ) : (
        <input {...shared} type={rest.type ?? "text"} />
      )}
    </div>
  );
}
