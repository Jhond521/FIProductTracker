import { useEffect, useState, type FormEvent } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { productsApi } from "../api/products";
import { ApiError } from "../api/client";
import type { FinancialProduct } from "../api/types";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { FormField } from "../components/FormField";
import { StatusBanner } from "../components/StatusBanner";

export function AddPurchase() {
  const { productId } = useParams<{ productId: string }>();
  const navigate = useNavigate();

  const [product, setProduct] = useState<FinancialProduct | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [purchaseDate, setPurchaseDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [nInstallments, setNInstallments] = useState("1");
  const [interestFreePromo, setInterestFreePromo] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!productId) return;
    let cancelled = false;

    productsApi
      .get(productId)
      .then((p) => {
        if (!cancelled) setProduct(p);
      })
      .catch((err) => {
        if (!cancelled) {
          setLoadError(
            err instanceof ApiError && err.status === 404
              ? "This card no longer exists."
              : "Could not load this card.",
          );
        }
      });

    return () => {
      cancelled = true;
    };
  }, [productId]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!productId) return;
    setError(null);
    setSubmitting(true);

    try {
      await productsApi.createPurchase(productId, {
        amount: Number(amount),
        currency: "COP",
        purchase_date: purchaseDate,
        n_installments: Number(nInstallments),
        interest_free_promo: interestFreePromo,
        description: description || null,
      });
      navigate("/");
    } catch (err) {
      setError(
        err instanceof ApiError ? String(err.message) : "Could not add the purchase. Try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (loadError) {
    return (
      <div>
        <h1>Add a purchase</h1>
        <StatusBanner kind="error">{loadError}</StatusBanner>
        <p style={{ marginTop: 16 }}>
          <Link to="/" style={{ color: "var(--color-primary)", fontWeight: 600 }}>
            ← Back to dashboard
          </Link>
        </p>
      </div>
    );
  }

  return (
    <div>
      <h1>Add a purchase</h1>
      <p style={{ color: "var(--color-text-muted)", marginTop: 8, marginBottom: 28 }}>
        {product ? `To ${product.institution_name}` : "Loading card…"}
      </p>

      <Card>
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <FormField label="Description" hint="Optional — e.g. merchant name">
            <input
              type="text"
              placeholder="Electrodomestico"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </FormField>

          <FormField label="Amount (COP)">
            <input
              type="number"
              min={1}
              step="1"
              placeholder="600000"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              required
            />
          </FormField>

          <FormField label="Purchase date">
            <input
              type="date"
              value={purchaseDate}
              onChange={(e) => setPurchaseDate(e.target.value)}
              required
            />
          </FormField>

          <FormField label="Installments" hint="Number of cuotas">
            <input
              type="number"
              min={1}
              step="1"
              value={nInstallments}
              onChange={(e) => setNInstallments(e.target.value)}
              required
            />
          </FormField>

          <FormField label="Interest-free promo">
            <input
              type="checkbox"
              checked={interestFreePromo}
              onChange={(e) => setInterestFreePromo(e.target.checked)}
            />
          </FormField>

          {error && <StatusBanner kind="error">{error}</StatusBanner>}

          <div style={{ display: "flex", justifyContent: "flex-end", gap: 12, marginTop: 8 }}>
            <Button type="submit" disabled={submitting || !product}>
              {submitting ? "Adding…" : "Add purchase"}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
