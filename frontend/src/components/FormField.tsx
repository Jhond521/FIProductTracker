import type { ReactNode } from "react";
import "./FormField.css";

export function FormField({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <label className="form-field">
      <span className="form-field-label">{label}</span>
      {children}
      {hint && <span className="form-field-hint">{hint}</span>}
    </label>
  );
}
