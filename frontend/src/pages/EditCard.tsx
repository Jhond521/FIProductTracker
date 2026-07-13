import { useEffect, useState, type FormEvent } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { productsApi } from "../api/products";
import { ApiError } from "../api/client";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { FormField } from "../components/FormField";
import { StatusBanner } from "../components/StatusBanner";

export function EditCard() {
  const { productId } = useParams<{ productId: string }>();
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

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!productId) return;
    let cancelled = false;

    productsApi
      .get(productId)
      .then((product) => {
        if (cancelled) return;
        setMarket(product.market as "CO" | "US");
        setInstitutionName(product.institution_name);
        setCreditLimit(String(product.credit_limit));
        setDayCountBasis(String(product.day_count_basis));
        if (product.ea_rate != null) setEaRatePercent(String(product.ea_rate * 100));
        if (product.apr != null) setAprPercent(String(product.apr * 100));
        if (product.penalty_rate != null) setPenaltyRatePercent(String(product.penalty_rate * 100));
        if (product.min_payment_flat_floor != null) {
          setMinPaymentFlatFloor(String(product.min_payment_flat_floor));
        }
        setInstallmentPlanAvailable(product.installment_plan_available);
        setStatementCutoffDay(String(product.statement_cutoff_day));
        setPaymentDueDay(String(product.payment_due_day));
      })
      .catch((err) => {
        if (!cancelled) {
          setLoadError(
            err instanceof ApiError && err.status === 404
              ? t("addCard.editCardGone")
              : t("addCard.editCardLoadError"),
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [productId, t]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!productId) return;
    setError(null);
    setSubmitting(true);

    try {
      await productsApi.update(productId, {
        institution_name: institutionName,
        credit_limit: Number(creditLimit),
        day_count_basis: Number(dayCountBasis),
        statement_cutoff_day: Number(statementCutoffDay),
        payment_due_day: Number(paymentDueDay),
        ...(market === "CO"
          ? { ea_rate: Number(eaRatePercent) / 100 }
          : {
              apr: Number(aprPercent) / 100,
              penalty_rate: penaltyRatePercent ? Number(penaltyRatePercent) / 100 : undefined,
              min_payment_flat_floor: minPaymentFlatFloor ? Number(minPaymentFlatFloor) : undefined,
              installment_plan_available: installmentPlanAvailable,
            }),
      });
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? String(err.message) : t("addCard.editError"));
    } finally {
      setSubmitting(false);
    }
  }

  if (loadError) {
    return (
      <div>
        <h1>{t("addCard.editTitle")}</h1>
        <StatusBanner kind="error">{loadError}</StatusBanner>
        <p style={{ marginTop: 16 }}>
          <Link to="/" style={{ color: "var(--color-primary)", fontWeight: 600 }}>
            {t("common.backToDashboard")}
          </Link>
        </p>
      </div>
    );
  }

  return (
    <div>
      <h1>{t("addCard.editTitle")}</h1>
      <p style={{ color: "var(--color-text-muted)", marginTop: 8, marginBottom: 28 }}>
        {market === "CO" ? t("addCard.subtitle") : t("addCard.subtitleUs")}
      </p>

      <Card>
        {loading ? (
          <StatusBanner kind="loading">{t("common.loading")}</StatusBanner>
        ) : (
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

                <FormField
                  label={t("addCard.installmentPlanLabel")}
                  hint={t("addCard.installmentPlanHint")}
                >
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

            {error && <StatusBanner kind="error">{error}</StatusBanner>}

            <div style={{ display: "flex", justifyContent: "flex-end", gap: 12, marginTop: 8 }}>
              <Button type="submit" disabled={submitting}>
                {submitting ? t("addCard.editSubmitting") : t("addCard.editSubmit")}
              </Button>
            </div>
          </form>
        )}
      </Card>
    </div>
  );
}
