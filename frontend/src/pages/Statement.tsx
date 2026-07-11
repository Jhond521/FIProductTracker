import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { productsApi } from "../api/products";
import { ApiError } from "../api/client";
import type { FinancialProduct, Purchase, PurchaseSchedule } from "../api/types";
import { Card } from "../components/Card";
import { StatusBanner } from "../components/StatusBanner";
import { formatCOP, formatDate, formatPercent } from "../lib/format";
import "./Statement.css";

export function Statement() {
  const { productId, purchaseId } = useParams<{ productId: string; purchaseId: string }>();
  const { t } = useTranslation();

  const [product, setProduct] = useState<FinancialProduct | null>(null);
  const [purchase, setPurchase] = useState<Purchase | null>(null);
  const [schedule, setSchedule] = useState<PurchaseSchedule | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!productId || !purchaseId) return;
    let cancelled = false;

    async function load() {
      setError(null);
      try {
        const [productData, purchases, scheduleData] = await Promise.all([
          productsApi.get(productId!),
          productsApi.listPurchases(productId!),
          productsApi.getSchedule(productId!, purchaseId!),
        ]);
        if (cancelled) return;

        const matchingPurchase = purchases.find((p) => p.id === purchaseId);
        if (!matchingPurchase) {
          setError(t("statement.notFound"));
          return;
        }

        setProduct(productData);
        setPurchase(matchingPurchase);
        setSchedule(scheduleData);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError && err.status === 404
              ? t("statement.notFound")
              : t("statement.loadError"),
          );
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [productId, purchaseId, t]);

  if (error) {
    return (
      <div>
        <h1>{t("statement.title")}</h1>
        <StatusBanner kind="error">{error}</StatusBanner>
        <p style={{ marginTop: 16 }}>
          <Link to="/" style={{ color: "var(--color-primary)", fontWeight: 600 }}>
            {t("common.backToDashboard")}
          </Link>
        </p>
      </div>
    );
  }

  if (!product || !purchase || !schedule) {
    return (
      <div>
        <h1>{t("statement.title")}</h1>
        <StatusBanner kind="loading">{t("statement.loading")}</StatusBanner>
      </div>
    );
  }

  return (
    <div>
      <div className="statement-header">
        <h1>{purchase.description || t("common.purchaseFallback")}</h1>
        <p className="statement-subtitle">
          {t("statement.subtitle", {
            institution: product.institution_name,
            date: formatDate(purchase.purchase_date),
            amount: formatCOP(purchase.amount),
          })}
        </p>
      </div>

      <div className="statement-headline">
        <Card className="statement-stat">
          <span className="statement-stat-label">{t("statement.totalInterestCost")}</span>
          <span className="statement-stat-value statement-stat-terracotta">
            {formatCOP(schedule.total_interest_cost)}
          </span>
        </Card>
        <Card className="statement-stat">
          <span className="statement-stat-label">{t("statement.realAnnualizedCost")}</span>
          <span className="statement-stat-value statement-stat-primary">
            {formatPercent(schedule.real_annualized_cost)}
          </span>
        </Card>
      </div>

      <Card className="statement-table-card">
        <div className="statement-table-header">
          <h3>{t("statement.breakdown")}</h3>
          <div className="statement-legend">
            <span className="statement-legend-item">
              <span className="statement-legend-swatch statement-legend-principal" />
              {t("statement.principal")}
            </span>
            <span className="statement-legend-item">
              <span className="statement-legend-swatch statement-legend-interest" />
              {t("statement.interest")}
            </span>
          </div>
        </div>

        <div className="statement-table-scroll">
          <table className="statement-table">
            <thead>
              <tr>
                <th>{t("statement.columnNumber")}</th>
                <th>{t("statement.columnPayment")}</th>
                <th>{t("statement.columnSplit")}</th>
                <th className="statement-table-num">{t("statement.principal")}</th>
                <th className="statement-table-num">{t("statement.interest")}</th>
                <th className="statement-table-num">{t("statement.columnBalance")}</th>
              </tr>
            </thead>
            <tbody>
              {schedule.schedule.map((entry) => {
                const principalPct = (entry.principal_portion / entry.payment) * 100;
                return (
                  <tr key={entry.installment_number}>
                    <td>{entry.installment_number}</td>
                    <td className="statement-table-payment">{formatCOP(entry.payment)}</td>
                    <td>
                      <div className="statement-split-bar">
                        <div
                          className="statement-split-principal"
                          style={{ width: `${principalPct}%` }}
                        />
                        <div
                          className="statement-split-interest"
                          style={{ width: `${100 - principalPct}%` }}
                        />
                      </div>
                    </td>
                    <td className="statement-table-num statement-table-principal">
                      {formatCOP(entry.principal_portion)}
                    </td>
                    <td className="statement-table-num statement-table-interest">
                      {formatCOP(entry.interest_portion)}
                    </td>
                    <td className="statement-table-num">{formatCOP(entry.remaining_balance)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
