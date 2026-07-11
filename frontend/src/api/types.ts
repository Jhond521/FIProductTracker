export interface User {
  id: string;
  email: string;
  name: string;
  picture_url: string | null;
}

export interface FinancialProduct {
  id: string;
  market: string;
  institution_name: string;
  credit_limit: number;
  ea_rate: number | null;
  day_count_basis: number;
  apr: number | null;
  penalty_rate: number | null;
  min_payment_flat_floor: number | null;
  installment_plan_available: boolean;
}

export interface FinancialProductCreate {
  market?: string;
  institution_name: string;
  credit_limit: number;
  ea_rate?: number | null;
  day_count_basis?: number;
  apr?: number | null;
  penalty_rate?: number | null;
  min_payment_flat_floor?: number | null;
  installment_plan_available?: boolean;
}

export interface FinancialProductUpdate {
  institution_name?: string;
  credit_limit?: number;
  ea_rate?: number;
  day_count_basis?: number;
  apr?: number;
  penalty_rate?: number;
  min_payment_flat_floor?: number;
  installment_plan_available?: boolean;
}

export interface Purchase {
  id: string;
  product_id: string;
  amount: number;
  currency: string;
  purchase_date: string;
  n_installments: number;
  interest_free_promo: boolean;
  description: string | null;
}

export interface PurchaseCreate {
  amount: number;
  currency?: string;
  purchase_date: string;
  n_installments?: number;
  interest_free_promo?: boolean;
  description?: string | null;
}

export interface PurchaseUpdate {
  amount?: number;
  currency?: string;
  purchase_date?: string;
  n_installments?: number;
  interest_free_promo?: boolean;
  description?: string | null;
}

export interface InstallmentEntry {
  installment_number: number;
  payment: number;
  principal_portion: number;
  interest_portion: number;
  remaining_balance: number;
}

export interface PurchaseSchedule {
  purchase_id: string;
  total_interest_cost: number;
  real_annualized_cost: number;
  schedule: InstallmentEntry[];
}
