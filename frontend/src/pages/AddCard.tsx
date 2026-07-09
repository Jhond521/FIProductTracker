import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { productsApi } from "../api/products";
import { ApiError } from "../api/client";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { FormField } from "../components/FormField";
import { StatusBanner } from "../components/StatusBanner";

export function AddCard() {
  const navigate = useNavigate();

  const [institutionName, setInstitutionName] = useState("");
  const [creditLimit, setCreditLimit] = useState("");
  const [eaRatePercent, setEaRatePercent] = useState("");
  const [dayCountBasis, setDayCountBasis] = useState("365");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      await productsApi.create({
        market: "CO",
        institution_name: institutionName,
        credit_limit: Number(creditLimit),
        ea_rate: Number(eaRatePercent) / 100,
        day_count_basis: Number(dayCountBasis),
      });
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? String(err.message) : "Could not create the card. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h1>Add a card</h1>
      <p style={{ color: "var(--color-text-muted)", marginTop: 8, marginBottom: 28 }}>
        Colombia market · full rate and fee details from your card agreement
      </p>

      <Card>
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <FormField label="Institution name">
            <input
              type="text"
              placeholder="Banco Demo"
              value={institutionName}
              onChange={(e) => setInstitutionName(e.target.value)}
              required
            />
          </FormField>

          <FormField label="Credit limit (COP)" hint="Cupo — the maximum balance the card allows">
            <input
              type="number"
              min={1}
              step="1"
              placeholder="5000000"
              value={creditLimit}
              onChange={(e) => setCreditLimit(e.target.value)}
              required
            />
          </FormField>

          <FormField label="EA rate (%)" hint="Effective annual rate, e.g. 36 for 36%">
            <input
              type="number"
              min={0}
              step="0.01"
              placeholder="36"
              value={eaRatePercent}
              onChange={(e) => setEaRatePercent(e.target.value)}
              required
            />
          </FormField>

          <FormField label="Day-count basis" hint="Bank-specific — check your card agreement">
            <select value={dayCountBasis} onChange={(e) => setDayCountBasis(e.target.value)}>
              <option value="365">365 days</option>
              <option value="360">360 days</option>
            </select>
          </FormField>

          {error && <StatusBanner kind="error">{error}</StatusBanner>}

          <div style={{ display: "flex", justifyContent: "flex-end", gap: 12, marginTop: 8 }}>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Adding…" : "Add card"}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
