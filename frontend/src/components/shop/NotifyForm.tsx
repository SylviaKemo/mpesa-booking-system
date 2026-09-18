"use client";

import { useState } from "react";
import styles from "./NotifyForm.module.css";

export function NotifyForm() {
  const [phone, setPhone] = useState("");
  const [sent, setSent] = useState(false);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (phone.trim()) setSent(true);
  };

  return (
    <>
      <form className={styles.form} onSubmit={submit}>
        <input
          type="tel"
          value={phone}
          onChange={(e) => {
            setPhone(e.target.value);
            setSent(false);
          }}
          placeholder="07XX XXX XXX"
          aria-label="Phone number"
          className={styles.input}
        />
        <button type="submit" className={styles.button}>
          {sent ? "You're in" : "Notify me"}
        </button>
      </form>
      <p className={styles.note} role="status">
        {sent ? "We'll text you the moment the shop opens." : ""}
      </p>
    </>
  );
}
