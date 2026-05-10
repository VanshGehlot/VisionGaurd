export default function StatusBadge({ tone = "neutral", children, compact = false }) {
  return (
    <span className={`vg-badge vg-badge-${tone} ${compact ? "is-compact" : ""}`}>
      {children}
    </span>
  );
}
