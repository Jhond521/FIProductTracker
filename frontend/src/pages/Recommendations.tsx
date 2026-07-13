import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { productsApi } from "../api/products";
import { ApiError } from "../api/client";
import type { FinancialProduct, RecommendationSet } from "../api/types";
import { Card } from "../components/Card";
import { StatusBanner } from "../components/StatusBanner";
import { formatCOP, formatPercent, formatUSD } from "../lib/format";
import "./Recommendations.css";

export function Recommendations() {
  const { productId } = useParams<{ productId?: string }>();
  const { t } = useTranslation();

  const [products, setProducts] = useState<FinancialProduct[] | null>(null);
  const [recs, setRecs] = useState<RecommendationSet | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setError(null);
      try {
        const [productList, recsData] = await Promise.all([
          productsApi.list(),
          productId ? productsApi.getProductRecommendations(productId) : productsApi.getRecommendations(),
        ]);
        if (!cancelled) {
          setProducts(productList);
          setRecs(recsData);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError && err.status === 404
              ? t("recommendations.cardGone")
              : t("recommendations.loadError"),
          );
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [productId, t]);

  if (error) {
    return (
      <div>
        <h1>{t("recommendations.title")}</h1>
        <StatusBanner kind="error">{error}</StatusBanner>
        <p style={{ marginTop: 16 }}>
          <Link to="/" style={{ color: "var(--color-primary)", fontWeight: 600 }}>
            {t("common.backToDashboard")}
          </Link>
        </p>
      </div>
    );
  }

  if (!products || !recs) {
    return (
      <div>
        <h1>{t("recommendations.title")}</h1>
        <StatusBanner kind="loading">{t("recommendations.loading")}</StatusBanner>
      </div>
    );
  }

  const productsById = new Map(products.map((p) => [p.id, p]));
  const scopedCard = productId ? productsById.get(productId) : undefined;

  function formatForProduct(productIdForFormat: string, amount: number): string {
    return productsById.get(productIdForFormat)?.market === "US" ? formatUSD(amount) : formatCOP(amount);
  }

  const isEmpty =
    recs.real_cost_exceeds_rate.length === 0 &&
    recs.pay_in_full_saves_interest.length === 0 &&
    recs.promo_expiring.length === 0 &&
    recs.avalanche_payoff_order.length === 0 &&
    recs.utilization_risk.length === 0;

  return (
    <div>
      <h1>{t("recommendations.title")}</h1>
      <p className="recommendations-subtitle">
        {scopedCard
          ? t("recommendations.cardSubtitle", { institution: scopedCard.institution_name })
          : t("recommendations.subtitle")}
      </p>

      {isEmpty && <Card className="recommendations-empty">{t("recommendations.empty")}</Card>}

      {recs.real_cost_exceeds_rate.length > 0 && (
        <Card className="recommendations-section">
          <h3>{t("recommendations.realCostExceedsRateTitle")}</h3>
          <ul className="recommendations-list">
            {recs.real_cost_exceeds_rate.map((flag) => (
              <li key={flag.purchase_id}>
                <Link to={`/cards/${flag.product_id}/purchases/${flag.purchase_id}`}>
                  {t("recommendations.realCostExceedsRateItem", {
                    description: flag.description || t("common.purchaseFallback"),
                    realCost: formatPercent(flag.real_annualized_cost),
                    disclosedRate: formatPercent(flag.disclosed_rate),
                  })}
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {recs.pay_in_full_saves_interest.length > 0 && (
        <Card className="recommendations-section">
          <h3>{t("recommendations.payInFullTitle")}</h3>
          <ul className="recommendations-list">
            {recs.pay_in_full_saves_interest.map((flag) => (
              <li key={flag.product_id}>
                <Link to={`/cards/${flag.product_id}/statements`}>
                  {t("recommendations.payInFullItem", {
                    balance: formatForProduct(flag.product_id, flag.statement_balance),
                    minimum: formatForProduct(flag.product_id, flag.minimum_payment),
                    interest: formatForProduct(flag.product_id, flag.current_period_interest),
                  })}
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {recs.promo_expiring.length > 0 && (
        <Card className="recommendations-section">
          <h3>{t("recommendations.promoExpiringTitle")}</h3>
          <ul className="recommendations-list">
            {recs.promo_expiring.map((flag) => (
              <li key={flag.purchase_id}>
                <Link to={`/cards/${flag.product_id}/purchases/${flag.purchase_id}`}>
                  {t("recommendations.promoExpiringItem", {
                    count: flag.installments_remaining,
                    description: flag.description || t("common.purchaseFallback"),
                  })}
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {recs.avalanche_payoff_order.length > 0 && (
        <Card className="recommendations-section">
          <h3>{t("recommendations.avalancheTitle")}</h3>
          <ol className="recommendations-list recommendations-list-numbered">
            {recs.avalanche_payoff_order.map((entry) => (
              <li key={entry.product_id}>
                <Link to={`/cards/${entry.product_id}/statements`}>
                  {t("recommendations.avalancheItem", {
                    institution: entry.institution_name,
                    rate: formatPercent(entry.disclosed_rate),
                    balance: formatForProduct(entry.product_id, entry.outstanding_balance),
                  })}
                </Link>
              </li>
            ))}
          </ol>
        </Card>
      )}

      {recs.utilization_risk.length > 0 && (
        <Card className="recommendations-section">
          <h3>{t("recommendations.utilizationTitle")}</h3>
          <ul className="recommendations-list">
            {recs.utilization_risk.map((flag) => (
              <li key={flag.product_id}>
                <Link to={`/cards/${flag.product_id}/statements`}>
                  {t("recommendations.utilizationItem", {
                    institution: productsById.get(flag.product_id)?.institution_name ?? "",
                    utilization: formatPercent(flag.utilization),
                    threshold: formatPercent(flag.threshold),
                  })}
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
