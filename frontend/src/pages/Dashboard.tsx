import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
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
          setError(err instanceof ApiError ? String(err.message) : "Could not load your cards.");
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const totalCreditLimit = cards?.reduce((sum, c) => sum + c.credit_limit, 0) ?? 0;

  return (
    <div>
      <div className="dashboard-header">
        <div>
          <h1>Dashboard</h1>
          <p className="dashboard-subtitle">Your cards, at a glance</p>
        </div>
        <Link to="/cards/new">
          <Button>+ Add card</Button>
        </Link>
      </div>

      {cards && cards.length > 0 && (
        <div className="dashboard-stats">
          <div className="dashboard-stat">
            <span className="dashboard-stat-value">{cards.length}</span>
            <span className="dashboard-stat-label">{cards.length === 1 ? "card" : "cards"}</span>
          </div>
          <div className="dashboard-stat">
            <span className="dashboard-stat-value">{formatCOP(totalCreditLimit)}</span>
            <span className="dashboard-stat-label">total credit limit</span>
          </div>
        </div>
      )}

      {error && <StatusBanner kind="error">{error}</StatusBanner>}

      {!cards && !error && <StatusBanner kind="loading">Loading your cards…</StatusBanner>}

      {cards && cards.length === 0 && (
        <Card className="dashboard-empty">
          <h3>No cards yet</h3>
          <p className="dashboard-subtitle">Add your first card to see its real cost breakdown.</p>
          <Link to="/cards/new">
            <Button>+ Add your first card</Button>
          </Link>
        </Card>
      )}

      <div className="dashboard-card-list">
        {cards?.map((card) => (
          <Card key={card.id} className="product-card">
            <div className="product-card-header">
              <div>
                <h3>{card.institution_name}</h3>
                <span className="product-card-market">Colombia</span>
              </div>
              <span className="product-card-rate">{formatPercent(card.ea_rate)} EA</span>
            </div>

            <div className="product-card-meta">
              <span>
                Credit limit <strong>{formatCOP(card.credit_limit)}</strong>
              </span>
              <span className="product-card-daycount">{card.day_count_basis}-day basis</span>
            </div>

            <div className="product-card-purchases">
              <div className="product-card-purchases-header">
                <span>Purchases</span>
                <Link to={`/cards/${card.id}/purchases/new`} className="product-card-add-purchase">
                  + Add purchase
                </Link>
              </div>

              {card.purchases.length === 0 ? (
                <p className="dashboard-subtitle">No purchases yet.</p>
              ) : (
                <ul className="product-card-purchase-list">
                  {card.purchases.map((purchase) => (
                    <li key={purchase.id}>
                      <Link
                        to={`/cards/${card.id}/purchases/${purchase.id}`}
                        className="purchase-row"
                      >
                        <span className="purchase-row-desc">
                          {purchase.description || "Purchase"}
                        </span>
                        <span className="purchase-row-installments">
                          {purchase.n_installments}{" "}
                          {purchase.n_installments === 1 ? "cuota" : "cuotas"}
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
