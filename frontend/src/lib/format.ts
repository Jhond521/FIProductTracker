const cop = new Intl.NumberFormat("es-CO", {
  maximumFractionDigits: 0,
});

const percent = new Intl.NumberFormat("es-CO", {
  style: "percent",
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

export function formatCOP(amount: number): string {
  return `$${cop.format(amount)}`;
}

export function formatPercent(fraction: number): string {
  return percent.format(fraction);
}

export function formatDate(isoDate: string): string {
  return new Date(`${isoDate}T00:00:00`).toLocaleDateString("es-CO", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}
