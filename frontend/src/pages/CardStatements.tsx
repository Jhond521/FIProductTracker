import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { productsApi } from "../api/products";
import { ApiError } from "../api/client";
import type { FinancialProduct, StatementPeriodSummary } from "../api/types";
import { Card } from "../components/Card";
import { StatusBanner } from "../components/StatusBanner";
import { formatCOP, formatDate, formatUSD } from "../lib/format";
import "./CardStatements.css";

export function CardStatements() {
  const { productId } = useParams<{ productId: string }>();
  const { t } = useTranslation();

  const [product, setProduct] = useState<FinancialProduct | null>(null);
  const [periods, setPeriods] = useState<StatementPeriodSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!productId) return;
    let cancelled = false;

    async function load() {
      setError(null);
      try {
        const [productData, periodsData] = await Promise.all([
          productsApi.get(productId!),
          productsApi.listStatements(productId!),
        ]);
        if (cancelled) return;
        setProduct(productData);
        setPeriods(periodsData);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError && err.status === 404
              ? t("statements.cardGone")
              : t("statements.loadError"),
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
        <h1>{t("statements.title")}</h1>
        <StatusBanner kind="error">{error}</StatusBanner>
        <p style={{ marginTop: 16 }}>
          <Link to="/" style={{ color: "var(--color-primary)", fontWeight: 600 }}>
            {t("common.backToDashboard")}
          </Link>
        </p>
      </div>
    );
  }

  if (!product || !periods) {
    return (
      <div>
        <h1>{t("statements.title")}</h1>
        <StatusBanner kind="loading">{t("statements.loading")}</StatusBanner>
      </div>
    );
  }

  const formatAmount = product.market === "US" ? formatUSD : formatCOP;

  return (
    <div>
      <h1>{t("statements.title")}</h1>
      <p className="card-statements-subtitle">
        {t("statements.subtitle", { institution: product.institution_name })}
      </p>

      {periods.length === 0 ? (
        <Card className="card-statements-empty">{t("statements.empty")}</Card>
      ) : (
        <div className="card-statements-list">
          {periods.map((period) => (
            <Link key={period.period_end} to={`/cards/${productId}/statements/${period.period_end}`}>
              <Card className="card-statements-period">
                <div className="card-statements-period-dates">
                  <span className="card-statements-period-range">
                    {t("statements.periodRange", {
                      start: formatDate(period.period_start),
                      end: formatDate(period.period_end),
                    })}
                  </span>
                  <span className="card-statements-period-due">
                    {t("statements.dueDate", { date: formatDate(period.due_date) })}
                  </span>
                </div>
                <div className="card-statements-period-total">
                  <span className="card-statements-period-total-label">
                    {t("statements.totalDue")}
                  </span>
                  <span className="card-statements-period-total-value">
                    {formatAmount(period.total_due)}
                  </span>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
