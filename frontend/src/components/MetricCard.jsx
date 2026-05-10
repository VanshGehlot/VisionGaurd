export default function MetricCard({ label, value, meta, tone = "default" }) {
  return (
    <article className={`metric-card metric-${tone}`}>
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      {meta ? <div className="metric-meta">{meta}</div> : null}
    </article>
  );
}
