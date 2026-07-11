import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { productsApi } from "../api/products";
import { ApiError } from "../api/client";
import type { FinancialProduct, Purchase } from "../api/types";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { StatusBanner } from "../components/StatusBanner";
import { formatCOP, formatPercent } from "../lib/format";
import "./Dashboard.css";

interface CardWithPurchases extends FinancialProduct {
  purchases: Purchase[];
}

export function Dashboard() {
  const { t } = useTranslation();
  const [cards, setCards] = useState<CardWithPurchases[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setError(null);
      try {
        const products = await productsApi.list();
        const withPurchases = await Promise.all(
          products.map(async (product) => ({
            ...product,
            purchases: await productsApi.listPurchases(product.id),
          })),
        );
        if (!cancelled) setCards(withPurchases);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? String(err.message) : t("dashboard.loadError"));
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [t]);

  const totalCreditLimit = cards?.reduce((sum, c) => sum + c.credit_limit, 0) ?? 0;

  return (
    <div>
      <div className="dashboard-header">
        <div>
          <h1>{t("dashboard.title")}</h1>
          <p className="dashboard-subtitle">{t("dashboard.subtitle")}</p>
        </div>
        <Link to="/cards/new">
          <Button>{t("dashboard.addCard")}</Button>
        </Link>
      </div>

      {cards && cards.length > 0 && (
        <div className="dashboard-stats">
          <div className="dashboard-stat">
            <span className="dashboard-stat-value">{cards.length}</span>
            <span className="dashboard-stat-label">
              {t("dashboard.cardCount", { count: cards.length })}
            </span>
          </div>
          <div className="dashboard-stat">
            <span className="dashboard-stat-value">{formatCOP(totalCreditLimit)}</span>
            <span className="dashboard-stat-label">{t("dashboard.totalCreditLimit")}</span>
          </div>
        </div>
      )}

      {error && <StatusBanner kind="error">{error}</StatusBanner>}

      {!cards && !error && <StatusBanner kind="loading">{t("dashboard.loading")}</StatusBanner>}

      {cards && cards.length === 0 && (
        <Card className="dashboard-empty">
          <h3>{t("dashboard.emptyTitle")}</h3>
          <p className="dashboard-subtitle">{t("dashboard.emptyBody")}</p>
          <Link to="/cards/new">
            <Button>{t("dashboard.addFirstCard")}</Button>
          </Link>
        </Card>
      )}

      <div className="dashboard-card-list">
        {cards?.map((card) => (
          <Card key={card.id} className="product-card">
            <div className="product-card-header">
              <div>
                <h3>{card.institution_name}</h3>
                <span className="product-card-market">{t("dashboard.market")}</span>
              </div>
              <div className="product-card-actions">
                <span className="product-card-rate">
                  {t("dashboard.eaRateSuffix", { rate: formatPercent(card.ea_rate) })}
                </span>
                <Link to={`/cards/${card.id}/edit`} className="product-card-add-purchase">
                  {t("dashboard.editCard")}
                </Link>
              </div>
            </div>

            <div className="product-card-meta">
              <span>
                {t("dashboard.creditLimit")} <strong>{formatCOP(card.credit_limit)}</strong>
              </span>
              <span className="product-card-daycount">
                {t("dashboard.dayCountBasis", { days: card.day_count_basis })}
              </span>
            </div>

            <div className="product-card-purchases">
              <div className="product-card-purchases-header">
                <span>{t("dashboard.purchases")}</span>
                <Link to={`/cards/${card.id}/purchases/new`} className="product-card-add-purchase">
                  {t("dashboard.addPurchase")}
                </Link>
              </div>

              {card.purchases.length === 0 ? (
                <p className="dashboard-subtitle">{t("dashboard.noPurchases")}</p>
              ) : (
                <ul className="product-card-purchase-list">
                  {card.purchases.map((purchase) => (
                    <li key={purchase.id}>
                      <Link
                        to={`/cards/${card.id}/purchases/${purchase.id}`}
                        className="purchase-row"
                      >
                        <span className="purchase-row-desc">
                          {purchase.description || t("common.purchaseFallback")}
                        </span>
                        <span className="purchase-row-installments">
                          {purchase.n_installments}{" "}
                          {t("dashboard.installmentUnit", { count: purchase.n_installments })}
                        </span>
                        <span className="purchase-row-amount">{formatCOP(purchase.amount)}</span>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
