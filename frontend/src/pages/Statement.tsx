import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { productsApi } from "../api/products";
import { ApiError } from "../api/client";
import type { FinancialProduct, Purchase, PurchaseSchedule } from "../api/types";
import { Card } from "../components/Card";
import { StatusBanner } from "../components/StatusBanner";
import { formatCOP, formatDate, formatPercent } from "../lib/format";
import "./Statement.css";

export function Statement() {
  const { productId, purchaseId } = useParams<{ productId: string; purchaseId: string }>();

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
          setError("This purchase could not be found.");
          return;
        }

        setProduct(productData);
        setPurchase(matchingPurchase);
        setSchedule(scheduleData);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError && err.status === 404
              ? "This purchase could not be found."
              : "Could not load the statement.",
          );
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [productId, purchaseId]);

  if (error) {
    return (
      <div>
        <h1>Statement</h1>
        <StatusBanner kind="error">{error}</StatusBanner>
        <p style={{ marginTop: 16 }}>
          <Link to="/" style={{ color: "var(--color-primary)", fontWeight: 600 }}>
            ← Back to dashboard
          </Link>
        </p>
      </div>
    );
  }

  if (!product || !purchase || !schedule) {
    return (
      <div>
        <h1>Statement</h1>
        <StatusBanner kind="loading">Loading statement…</StatusBanner>
      </div>
    );
  }

  return (
    <div>
      <div className="statement-header">
        <h1>{purchase.description || "Purchase"}</h1>
        <p className="statement-subtitle">
          {product.institution_name} · {formatDate(purchase.purchase_date)} ·{" "}
          {formatCOP(purchase.amount)}
        </p>
      </div>

      <div className="statement-headline">
        <Card className="statement-stat">
          <span className="statement-stat-label">Total interest cost</span>
          <span className="statement-stat-value statement-stat-terracotta">
            {formatCOP(schedule.total_interest_cost)}
          </span>
        </Card>
        <Card className="statement-stat">
          <span className="statement-stat-label">Real annualized cost</span>
          <span className="statement-stat-value statement-stat-primary">
            {formatPercent(schedule.real_annualized_cost)}
          </span>
        </Card>
      </div>

      <Card className="statement-table-card">
        <div className="statement-table-header">
          <h3>Installment breakdown</h3>
          <div className="statement-legend">
            <span className="statement-legend-item">
              <span className="statement-legend-swatch statement-legend-principal" />
              Principal
            </span>
            <span className="statement-legend-item">
              <span className="statement-legend-swatch statement-legend-interest" />
              Interest
            </span>
          </div>
        </div>

        <div className="statement-table-scroll">
          <table className="statement-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Payment</th>
                <th>Split</th>
                <th className="statement-table-num">Principal</th>
                <th className="statement-table-num">Interest</th>
                <th className="statement-table-num">Balance</th>
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
