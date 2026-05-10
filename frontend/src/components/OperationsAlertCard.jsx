export default function OperationsAlertCard({ alert }) {
  const fallback = "No active operations alert right now.";
  const text = alert || fallback;
  const sentences = text
    .replace(/\s+/g, " ")
    .split(/(?<=[.!?])\s+/)
    .filter(Boolean);
  const summary = sentences[0] || fallback;
  const bullets = sentences.slice(1, 4);

  return (
    <article className="content-card content-card-alert operations-alert-card">
      <div className="card-heading-row">
        <div>
          <p className="eyebrow">Factory Operations Alert</p>
          <h3>Operational risk signal</h3>
        </div>
      </div>
      <p className="report-text report-summary-line">{summary}</p>
      {bullets.length ? (
        <ul className="clean-list clean-list-tight operations-alert-list">
          {bullets.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : null}
      {alert && sentences.length > 4 ? (
        <details className="compact-details">
          <summary>View full alert</summary>
          <p>{text}</p>
        </details>
      ) : null}
    </article>
  );
}
