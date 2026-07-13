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
  statement_cutoff_day: number;
  payment_due_day: number;
  recurring_fee: number | null;
  insurance_opt_in: boolean;
  insurance_cost: number | null;
  fx_fee: number | null;
  co_single_installment_charges_interest: boolean;
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
  statement_cutoff_day?: number;
  payment_due_day?: number;
  recurring_fee?: number | null;
  insurance_opt_in?: boolean;
  insurance_cost?: number | null;
  fx_fee?: number | null;
  co_single_installment_charges_interest?: boolean;
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
  statement_cutoff_day?: number;
  payment_due_day?: number;
  recurring_fee?: number | null;
  insurance_opt_in?: boolean;
  insurance_cost?: number | null;
  fx_fee?: number | null;
  co_single_installment_charges_interest?: boolean;
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

export interface PurchaseContribution {
  purchase_id: string;
  description: string | null;
  principal_portion: number;
  interest_portion: number;
}

export interface StatementPeriodSummary {
  period_start: string;
  period_end: string;
  due_date: string;
  total_principal: number;
  total_interest: number;
  total_fees: number;
  total_due: number;
}

export interface StatementPeriodDetail extends StatementPeriodSummary {
  contributions: PurchaseContribution[];
}
