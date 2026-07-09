import "./StatusBanner.css";

export function StatusBanner({
  kind,
  children,
}: {
  kind: "loading" | "error";
  children: React.ReactNode;
}) {
  return <div className={`status-banner status-banner-${kind}`}>{children}</div>;
}
