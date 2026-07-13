import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { productsApi } from "../api/products";
import { ApiError } from "../api/client";
import type { DashboardSummary, FinancialProduct, Purchase } from "../api/types";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { StatusBanner } from "../components/StatusBanner";
import { formatCOP, formatPercent, formatUSD } from "../lib/format";
import "./Dashboard.css";

interface CardWithPurchases extends FinancialProduct {
  purchases: Purchase[];
}

export function Dashboard() {
  const { t } = useTranslation();
  const [cards, setCards] = useState<CardWithPurchases[] | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setError(null);
      try {
        const [products, summaryData] = await Promise.all([
          productsApi.list(),
          productsApi.getDashboardSummary(),
        ]);
        const withPurchases = await Promise.all(
          products.map(async (product) => ({
            ...product,
            purchases: await productsApi.listPurchases(product.id),
          })),
        );
        if (!cancelled) {
          setCards(withPurchases);
          setSummary(summaryData);
        }
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

  const coCards = cards?.filter((c) => c.market === "CO") ?? [];
  const usCards = cards?.filter((c) => c.market === "US") ?? [];
  const coCreditLimit = coCards.reduce((sum, c) => sum + c.credit_limit, 0);
  const usCreditLimit = usCards.reduce((sum, c) => sum + c.credit_limit, 0);

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
        </div>
      )}

      {summary && coCards.length > 0 && (
        <Card className="dashboard-market-summary">
          <h3>{t("dashboard.marketCo")}</h3>
          <div className="dashboard-market-summary-stats">
            <div className="dashboard-stat">
              <span className="dashboard-stat-value">{formatCOP(coCreditLimit)}</span>
              <span className="dashboard-stat-label">{t("dashboard.totalCreditLimit")}</span>
            </div>
            <div className="dashboard-stat">
              <span className="dashboard-stat-value">{formatCOP(summary.co.total_balance)}</span>
              <span className="dashboard-stat-label">{t("dashboard.totalBalance")}</span>
            </div>
            <div className="dashboard-stat">
              <span className="dashboard-stat-value">{formatCOP(summary.co.total_interest)}</span>
              <span className="dashboard-stat-label">{t("dashboard.totalInterest")}</span>
            </div>
            <div className="dashboard-stat">
              <span className="dashboard-stat-value">{formatCOP(summary.co.total_fees)}</span>
              <span className="dashboard-stat-label">{t("dashboard.totalFees")}</span>
            </div>
          </div>
        </Card>
      )}

      {summary && usCards.length > 0 && (
        <Card className="dashboard-market-summary">
          <h3>{t("dashboard.marketUs")}</h3>
          <div className="dashboard-market-summary-stats">
            <div className="dashboard-stat">
              <span className="dashboard-stat-value">{formatUSD(usCreditLimit)}</span>
              <span className="dashboard-stat-label">{t("dashboard.totalCreditLimit")}</span>
            </div>
            <div className="dashboard-stat">
              <span className="dashboard-stat-value">{formatUSD(summary.us.total_balance)}</span>
              <span className="dashboard-stat-label">{t("dashboard.totalBalance")}</span>
            </div>
            <div className="dashboard-stat">
              <span className="dashboard-stat-value">{formatUSD(summary.us.total_interest)}</span>
              <span className="dashboard-stat-label">{t("dashboard.totalInterest")}</span>
            </div>
            <div className="dashboard-stat">
              <span className="dashboard-stat-value">{formatUSD(summary.us.total_fees)}</span>
              <span className="dashboard-stat-label">{t("dashboard.totalFees")}</span>
            </div>
          </div>
        </Card>
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
                <h3>
                  {card.institution_name}
                  {summary?.highest_cost_product_id === card.id && (
                    <span className="product-card-highest-cost">
                      {t("dashboard.highestCost")}
                    </span>
                  )}
                </h3>
                <span className="product-card-market">
                  {card.market === "US" ? t("dashboard.marketUs") : t("dashboard.marketCo")}
                </span>
              </div>
              <div className="product-card-actions">
                <span className="product-card-rate">
                  {card.market === "US"
                    ? t("dashboard.aprSuffix", { rate: formatPercent(card.apr ?? 0) })
                    : t("dashboard.eaRateSuffix", { rate: formatPercent(card.ea_rate ?? 0) })}
                </span>
                <Link to={`/cards/${card.id}/statements`} className="product-card-add-purchase">
                  {t("dashboard.viewStatements")}
                </Link>
                <Link to={`/cards/${card.id}/edit`} className="product-card-add-purchase">
                  {t("dashboard.editCard")}
                </Link>
              </div>
            </div>

            <div className="product-card-meta">
              <span>
                {t("dashboard.creditLimit")}{" "}
                <strong>
                  {card.market === "US" ? formatUSD(card.credit_limit) : formatCOP(card.credit_limit)}
                </strong>
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
                        to={
                          card.market === "CO"
                            ? `/cards/${card.id}/purchases/${purchase.id}`
                            : `/cards/${card.id}/statements`
                        }
                        className="purchase-row"
                      >
                        <span className="purchase-row-desc">
                          {purchase.description || t("common.purchaseFallback")}
                        </span>
                        {card.market === "CO" && (
                          <span className="purchase-row-installments">
                            {purchase.n_installments}{" "}
                            {t("dashboard.installmentUnit", { count: purchase.n_installments })}
                          </span>
                        )}
                        <span className="purchase-row-amount">
                          {purchase.currency === "USD" ? formatUSD(purchase.amount) : formatCOP(purchase.amount)}
                        </span>
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
