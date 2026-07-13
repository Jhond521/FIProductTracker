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

  const [market, setMarket] = useState<"CO" | "US">("CO");
  const [institutionName, setInstitutionName] = useState("");
  const [creditLimit, setCreditLimit] = useState("");
  const [eaRatePercent, setEaRatePercent] = useState("");
  const [dayCountBasis, setDayCountBasis] = useState("365");
  const [aprPercent, setAprPercent] = useState("");
  const [penaltyRatePercent, setPenaltyRatePercent] = useState("");
  const [minPaymentFlatFloor, setMinPaymentFlatFloor] = useState("");
  const [installmentPlanAvailable, setInstallmentPlanAvailable] = useState(false);
  const [statementCutoffDay, setStatementCutoffDay] = useState("1");
  const [paymentDueDay, setPaymentDueDay] = useState("15");
  const [recurringFee, setRecurringFee] = useState("");
  const [fxFeePercent, setFxFeePercent] = useState("");
  const [insuranceOptIn, setInsuranceOptIn] = useState(false);
  const [insuranceCost, setInsuranceCost] = useState("");
  const [coSingleInstallmentChargesInterest, setCoSingleInstallmentChargesInterest] =
    useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      await productsApi.create({
        market,
        institution_name: institutionName,
        credit_limit: Number(creditLimit),
        day_count_basis: Number(dayCountBasis),
        statement_cutoff_day: Number(statementCutoffDay),
        payment_due_day: Number(paymentDueDay),
        recurring_fee: recurringFee ? Number(recurringFee) : undefined,
        fx_fee: fxFeePercent ? Number(fxFeePercent) / 100 : undefined,
        insurance_opt_in: insuranceOptIn,
        insurance_cost: insuranceOptIn ? Number(insuranceCost) : undefined,
        ...(market === "CO"
          ? {
              ea_rate: Number(eaRatePercent) / 100,
              co_single_installment_charges_interest: coSingleInstallmentChargesInterest,
            }
          : {
              apr: Number(aprPercent) / 100,
              penalty_rate: penaltyRatePercent ? Number(penaltyRatePercent) / 100 : undefined,
              min_payment_flat_floor: minPaymentFlatFloor ? Number(minPaymentFlatFloor) : undefined,
              installment_plan_available: installmentPlanAvailable,
            }),
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
        {market === "CO" ? t("addCard.subtitle") : t("addCard.subtitleUs")}
      </p>

      <Card>
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <FormField label={t("addCard.marketLabel")} hint={t("addCard.marketHint")}>
            <select value={market} onChange={(e) => setMarket(e.target.value as "CO" | "US")}>
              <option value="CO">{t("addCard.marketCo")}</option>
              <option value="US">{t("addCard.marketUs")}</option>
            </select>
          </FormField>

          <FormField label={t("addCard.institutionLabel")}>
            <input
              type="text"
              placeholder={t("addCard.institutionPlaceholder")}
              value={institutionName}
              onChange={(e) => setInstitutionName(e.target.value)}
              required
            />
          </FormField>

          <FormField
            label={market === "CO" ? t("addCard.creditLimitLabel") : t("addCard.creditLimitLabelUs")}
            hint={t("addCard.creditLimitHint")}
          >
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

          {market === "CO" ? (
            <>
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

              <FormField
                label={t("addCard.coSingleInstallmentLabel")}
                hint={t("addCard.coSingleInstallmentHint")}
              >
                <input
                  type="checkbox"
                  checked={coSingleInstallmentChargesInterest}
                  onChange={(e) => setCoSingleInstallmentChargesInterest(e.target.checked)}
                />
              </FormField>
            </>
          ) : (
            <>
              <FormField label={t("addCard.aprLabel")} hint={t("addCard.aprHint")}>
                <input
                  type="number"
                  min={0}
                  step="0.01"
                  placeholder={t("addCard.aprPlaceholder")}
                  value={aprPercent}
                  onChange={(e) => setAprPercent(e.target.value)}
                  required
                />
              </FormField>

              <FormField label={t("addCard.penaltyRateLabel")} hint={t("addCard.penaltyRateHint")}>
                <input
                  type="number"
                  min={0}
                  step="0.01"
                  placeholder={t("addCard.penaltyRatePlaceholder")}
                  value={penaltyRatePercent}
                  onChange={(e) => setPenaltyRatePercent(e.target.value)}
                />
              </FormField>

              <FormField
                label={t("addCard.minPaymentFloorLabel")}
                hint={t("addCard.minPaymentFloorHint")}
              >
                <input
                  type="number"
                  min={0}
                  step="1"
                  placeholder={t("addCard.minPaymentFloorPlaceholder")}
                  value={minPaymentFlatFloor}
                  onChange={(e) => setMinPaymentFlatFloor(e.target.value)}
                />
              </FormField>

              <FormField label={t("addCard.installmentPlanLabel")} hint={t("addCard.installmentPlanHint")}>
                <input
                  type="checkbox"
                  checked={installmentPlanAvailable}
                  onChange={(e) => setInstallmentPlanAvailable(e.target.checked)}
                />
              </FormField>
            </>
          )}

          <FormField label={t("addCard.dayCountLabel")} hint={t("addCard.dayCountHint")}>
            <select value={dayCountBasis} onChange={(e) => setDayCountBasis(e.target.value)}>
              <option value="365">{t("addCard.days365")}</option>
              <option value="360">{t("addCard.days360")}</option>
            </select>
          </FormField>

          <FormField label={t("addCard.cutoffDayLabel")} hint={t("addCard.cutoffDayHint")}>
            <input
              type="number"
              min={1}
              max={28}
              step="1"
              value={statementCutoffDay}
              onChange={(e) => setStatementCutoffDay(e.target.value)}
              required
            />
          </FormField>

          <FormField label={t("addCard.dueDayLabel")} hint={t("addCard.dueDayHint")}>
            <input
              type="number"
              min={1}
              max={28}
              step="1"
              value={paymentDueDay}
              onChange={(e) => setPaymentDueDay(e.target.value)}
              required
            />
          </FormField>

          <FormField label={t("addCard.recurringFeeLabel")} hint={t("addCard.recurringFeeHint")}>
            <input
              type="number"
              min={0}
              step="1"
              placeholder={t("addCard.recurringFeePlaceholder")}
              value={recurringFee}
              onChange={(e) => setRecurringFee(e.target.value)}
            />
          </FormField>

          <FormField label={t("addCard.fxFeeLabel")} hint={t("addCard.fxFeeHint")}>
            <input
              type="number"
              min={0}
              step="0.01"
              placeholder={t("addCard.fxFeePlaceholder")}
              value={fxFeePercent}
              onChange={(e) => setFxFeePercent(e.target.value)}
            />
          </FormField>

          <FormField label={t("addCard.insuranceOptInLabel")} hint={t("addCard.insuranceOptInHint")}>
            <input
              type="checkbox"
              checked={insuranceOptIn}
              onChange={(e) => setInsuranceOptIn(e.target.checked)}
            />
          </FormField>

          {insuranceOptIn && (
            <FormField label={t("addCard.insuranceCostLabel")} hint={t("addCard.insuranceCostHint")}>
              <input
                type="number"
                min={0}
                step="1"
                placeholder={t("addCard.insuranceCostPlaceholder")}
                value={insuranceCost}
                onChange={(e) => setInsuranceCost(e.target.value)}
                required
              />
            </FormField>
          )}

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
