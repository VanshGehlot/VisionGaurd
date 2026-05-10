export default function ShiftReportCard({ report, compact = false, featured = false }) {
  const text = report || "No shift report available yet.";
  const sentences = text
    .replace(/\s+/g, " ")
    .split(/(?<=[.!?])\s+/)
    .filter(Boolean);
  const summary = sentences.slice(0, compact ? 1 : 2).join(" ") || text;

  return (
    <article className={`content-card shift-report-card ${compact ? "is-compact" : ""} ${featured ? "is-featured" : ""}`}>
      <div className="card-heading-row">
        <div>
          <p className="eyebrow">Shift Quality Report</p>
          <h3>{featured ? "Plant-level reporter summary" : "Reporter agent summary"}</h3>
        </div>
      </div>
      <p className="report-text report-summary-line">{summary}</p>
      {report && sentences.length > (compact ? 1 : 2) ? (
        <details className="compact-details">
          <summary>View full report</summary>
          <p>{text}</p>
        </details>
      ) : null}
    </article>
  );
}
