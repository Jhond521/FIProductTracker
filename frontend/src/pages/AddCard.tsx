import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { productsApi } from "../api/products";
import { ApiError } from "../api/client";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { FormField } from "../components/FormField";
import { StatusBanner } from "../components/StatusBanner";

export function AddCard() {
  const navigate = useNavigate();
  const { t } = useTranslation();

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
      setError(err instanceof ApiError ? String(err.message) : t("addCard.error"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h1>{t("addCard.title")}</h1>
      <p style={{ color: "var(--color-text-muted)", marginTop: 8, marginBottom: 28 }}>
        {t("addCard.subtitle")}
      </p>

      <Card>
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <FormField label={t("addCard.institutionLabel")}>
            <input
              type="text"
              placeholder={t("addCard.institutionPlaceholder")}
              value={institutionName}
              onChange={(e) => setInstitutionName(e.target.value)}
              required
            />
          </FormField>

          <FormField label={t("addCard.creditLimitLabel")} hint={t("addCard.creditLimitHint")}>
            <input
              type="number"
              min={1}
              step="1"
              placeholder={t("addCard.creditLimitPlaceholder")}
              value={creditLimit}
              onChange={(e) => setCreditLimit(e.target.value)}
              required
            />
          </FormField>

          <FormField label={t("addCard.eaRateLabel")} hint={t("addCard.eaRateHint")}>
            <input
              type="number"
              min={0}
              step="0.01"
              placeholder={t("addCard.eaRatePlaceholder")}
              value={eaRatePercent}
              onChange={(e) => setEaRatePercent(e.target.value)}
              required
            />
          </FormField>

          <FormField label={t("addCard.dayCountLabel")} hint={t("addCard.dayCountHint")}>
            <select value={dayCountBasis} onChange={(e) => setDayCountBasis(e.target.value)}>
              <option value="365">{t("addCard.days365")}</option>
              <option value="360">{t("addCard.days360")}</option>
            </select>
          </FormField>

          {error && <StatusBanner kind="error">{error}</StatusBanner>}

          <div style={{ display: "flex", justifyContent: "flex-end", gap: 12, marginTop: 8 }}>
            <Button type="submit" disabled={submitting}>
              {submitting ? t("addCard.submitting") : t("addCard.submit")}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
