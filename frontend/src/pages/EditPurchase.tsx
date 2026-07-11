import { useEffect, useState, type FormEvent } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { productsApi } from "../api/products";
import { ApiError } from "../api/client";
import type { FinancialProduct } from "../api/types";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { FormField } from "../components/FormField";
import { StatusBanner } from "../components/StatusBanner";

export function EditPurchase() {
  const { productId, purchaseId } = useParams<{ productId: string; purchaseId: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const [product, setProduct] = useState<FinancialProduct | null>(null);

  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [purchaseDate, setPurchaseDate] = useState("");
  const [nInstallments, setNInstallments] = useState("1");
  const [interestFreePromo, setInterestFreePromo] = useState(false);

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!productId || !purchaseId) return;
    let cancelled = false;

    async function load() {
      try {
        const [productData, purchases] = await Promise.all([
          productsApi.get(productId!),
          productsApi.listPurchases(productId!),
        ]);
        if (cancelled) return;

        const purchase = purchases.find((p) => p.id === purchaseId);
        if (!purchase) {
          setLoadError(t("addPurchase.editPurchaseGone"));
          return;
        }

        setProduct(productData);
        setDescription(purchase.description ?? "");
        setAmount(String(purchase.amount));
        setPurchaseDate(purchase.purchase_date);
        setNInstallments(String(purchase.n_installments));
        setInterestFreePromo(purchase.interest_free_promo);
      } catch (err) {
        if (!cancelled) {
          setLoadError(
            err instanceof ApiError && err.status === 404
              ? t("addPurchase.editPurchaseGone")
              : t("addPurchase.cardLoadError"),
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [productId, purchaseId, t]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!productId || !purchaseId) return;
    setError(null);
    setSubmitting(true);

    try {
      await productsApi.updatePurchase(productId, purchaseId, {
        amount: Number(amount),
        purchase_date: purchaseDate,
        n_installments: Number(nInstallments),
        interest_free_promo: interestFreePromo,
        description: description || null,
      });
      navigate(`/cards/${productId}/purchases/${purchaseId}`);
    } catch (err) {
      setError(err instanceof ApiError ? String(err.message) : t("addPurchase.editError"));
    } finally {
      setSubmitting(false);
    }
  }

  if (loadError) {
    return (
      <div>
        <h1>{t("addPurchase.editTitle")}</h1>
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
      <h1>{t("addPurchase.editTitle")}</h1>
      <p style={{ color: "var(--color-text-muted)", marginTop: 8, marginBottom: 28 }}>
        {product
          ? t("addPurchase.toInstitution", { institutionName: product.institution_name })
          : t("addPurchase.loadingCard")}
      </p>

      <Card>
        {loading ? (
          <StatusBanner kind="loading">{t("common.loading")}</StatusBanner>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            <FormField label={t("addPurchase.descriptionLabel")} hint={t("addPurchase.descriptionHint")}>
              <input
                type="text"
                placeholder={t("addPurchase.descriptionPlaceholder")}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </FormField>

            <FormField label={t("addPurchase.amountLabel")}>
              <input
                type="number"
                min={1}
                step="1"
                placeholder={t("addPurchase.amountPlaceholder")}
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
              />
            </FormField>

            <FormField label={t("addPurchase.dateLabel")}>
              <input
                type="date"
                value={purchaseDate}
                onChange={(e) => setPurchaseDate(e.target.value)}
                required
              />
            </FormField>

            <FormField label={t("addPurchase.installmentsLabel")} hint={t("addPurchase.installmentsHint")}>
              <input
                type="number"
                min={1}
                step="1"
                value={nInstallments}
                onChange={(e) => setNInstallments(e.target.value)}
                required
              />
            </FormField>

            <FormField label={t("addPurchase.promoLabel")}>
              <input
                type="checkbox"
                checked={interestFreePromo}
                onChange={(e) => setInterestFreePromo(e.target.checked)}
              />
            </FormField>

            {error && <StatusBanner kind="error">{error}</StatusBanner>}

            <div style={{ display: "flex", justifyContent: "flex-end", gap: 12, marginTop: 8 }}>
              <Button type="submit" disabled={submitting}>
                {submitting ? t("addPurchase.editSubmitting") : t("addPurchase.editSubmit")}
              </Button>
            </div>
          </form>
        )}
      </Card>
    </div>
  );
}
