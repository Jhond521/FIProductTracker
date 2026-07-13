import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { productsApi } from "../api/products";
import { ApiError } from "../api/client";
import type { FinancialProduct, StatementPeriodDetail } from "../api/types";
import { Card } from "../components/Card";
import { StatusBanner } from "../components/StatusBanner";
import { formatCOP, formatDate, formatUSD } from "../lib/format";
import "./StatementPeriod.css";

export function StatementPeriod() {
  const { productId, periodEnd } = useParams<{ productId: string; periodEnd: string }>();
  const { t } = useTranslation();

  const [product, setProduct] = useState<FinancialProduct | null>(null);
  const [statement, setStatement] = useState<StatementPeriodDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!productId || !periodEnd) return;
    let cancelled = false;

    async function load() {
      setError(null);
      try {
        const [productData, statementData] = await Promise.all([
          productsApi.get(productId!),
          productsApi.getStatementPeriod(productId!, periodEnd!),
        ]);
        if (cancelled) return;
        setProduct(productData);
        setStatement(statementData);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError && err.status === 404
              ? t("statements.detailNotFound")
              : t("statements.loadError"),
          );
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [productId, periodEnd, t]);

  if (error) {
    return (
      <div>
        <h1>{t("statements.title")}</h1>
        <StatusBanner kind="error">{error}</StatusBanner>
        <p style={{ marginTop: 16 }}>
          <Link to={`/cards/${productId}/statements`} style={{ color: "var(--color-primary)", fontWeight: 600 }}>
            {t("common.backToDashboard")}
          </Link>
        </p>
      </div>
    );
  }

  if (!product || !statement) {
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
      <div className="statement-period-header">
        <h1>{t("statements.detailTitle", { end: formatDate(statement.period_end) })}</h1>
        <p className="statement-period-subtitle">
          {t("statements.periodRange", {
            start: formatDate(statement.period_start),
            end: formatDate(statement.period_end),
          })}{" "}
          · {t("statements.dueDate", { date: formatDate(statement.due_date) })}
        </p>
      </div>

      <div className="statement-period-totals">
        <Card className="statement-period-stat">
          <span className="statement-period-stat-label">{t("statements.principal")}</span>
          <span className="statement-period-stat-value statement-period-stat-accent">
            {formatAmount(statement.total_principal)}
          </span>
        </Card>
        <Card className="statement-period-stat">
          <span className="statement-period-stat-label">{t("statements.interest")}</span>
          <span className="statement-period-stat-value statement-period-stat-terracotta">
            {formatAmount(statement.total_interest)}
          </span>
        </Card>
        <Card className="statement-period-stat">
          <span className="statement-period-stat-label">{t("statements.fees")}</span>
          <span className="statement-period-stat-value">{formatAmount(statement.total_fees)}</span>
        </Card>
        <Card className="statement-period-stat">
          <span className="statement-period-stat-label">{t("statements.totalDue")}</span>
          <span className="statement-period-stat-value statement-period-stat-primary">
            {formatAmount(statement.total_due)}
          </span>
        </Card>
      </div>

      <Card className="statement-period-contributions">
        <h3>{t("statements.contributingPurchases")}</h3>

        {statement.contributions.length === 0 ? (
          <p className="statement-period-no-contributions">{t("statements.noContributions")}</p>
        ) : (
          <ul className="statement-period-contribution-list">
            {statement.contributions.map((contribution) => {
              const row = (
                <>
                  <span className="statement-period-contribution-desc">
                    {contribution.description || t("common.purchaseFallback")}
                  </span>
                  <span className="statement-period-contribution-amount">
                    {formatAmount(contribution.principal_portion + contribution.interest_portion)}
                  </span>
                </>
              );
              return (
                <li key={contribution.purchase_id}>
                  {product.market === "CO" ? (
                    <Link
                      to={`/cards/${productId}/purchases/${contribution.purchase_id}`}
                      className="statement-period-contribution-row"
                    >
                      {row}
                    </Link>
                  ) : (
                    <div className="statement-period-contribution-row">{row}</div>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </Card>
    </div>
  );
}
