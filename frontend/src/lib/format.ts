import i18n from "../i18n";

// Currency and dates are for a Colombia-only product, so the country stays
// fixed — only the language subtag follows the UI language, which shifts
// month names and grouping/decimal conventions without changing the market.
function currentLocale(): string {
  return i18n.language?.startsWith("es") ? "es-CO" : "en-CO";
}

export function formatCOP(amount: number): string {
  const cop = new Intl.NumberFormat(currentLocale(), { maximumFractionDigits: 0 });
  return `$${cop.format(amount)}`;
}

export function formatUSD(amount: number): string {
  const usd = new Intl.NumberFormat(currentLocale(), {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `US$${usd.format(amount)}`;
}

export function formatPercent(fraction: number): string {
  const percent = new Intl.NumberFormat(currentLocale(), {
    style: "percent",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
  return percent.format(fraction);
}

export function formatDate(isoDate: string): string {
  return new Date(`${isoDate}T00:00:00`).toLocaleDateString(currentLocale(), {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}
