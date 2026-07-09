import { api } from "./client";
import type {
  FinancialProduct,
  FinancialProductCreate,
  Purchase,
  PurchaseCreate,
  PurchaseSchedule,
} from "./types";

const BASE = "/api/v1/internal/products";

export const productsApi = {
  list: () => api.get<FinancialProduct[]>(BASE),
  get: (productId: string) => api.get<FinancialProduct>(`${BASE}/${productId}`),
  create: (payload: FinancialProductCreate) => api.post<FinancialProduct>(BASE, payload),

  listPurchases: (productId: string) => api.get<Purchase[]>(`${BASE}/${productId}/purchases`),
  createPurchase: (productId: string, payload: PurchaseCreate) =>
    api.post<Purchase>(`${BASE}/${productId}/purchases`, payload),

  getSchedule: (productId: string, purchaseId: string) =>
    api.get<PurchaseSchedule>(`${BASE}/${productId}/purchases/${purchaseId}/schedule`),
};
