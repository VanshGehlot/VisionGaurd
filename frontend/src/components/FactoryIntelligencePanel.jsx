function renderList(items, fallback) {
  if (Array.isArray(items) && items.length > 0) {
    return items.map((item) => <li key={item}>{item}</li>);
  }
  if (typeof items === "string" && items.trim()) {
    return <li>{items}</li>;
  }
  return <li>{fallback}</li>;
}

function isManualReview(result) {
  return result?.action === "ALERT_OPERATOR" && !result?.defect_detected;
}

function summaryHeading(result) {
  if (result?.action === "STOP_LINE" || result?.severity === "critical") {
    return "Why the line was stopped";
  }
  if (isManualReview(result)) {
    return "Why release was held for review";
  }
  if (result?.defect_detected) {
    return "Why the item was flagged";
  }
  return "Why the item was released";
}

export default function FactoryIntelligencePanel({ result }) {
  return (
    <div className="intelligence-stack">
      <article className="content-card intelligence-summary-panel">
        <p className="eyebrow">Factory intelligence</p>
        <h3>{summaryHeading(result)}</h3>
        <p className="summary-text">
          {result?.factory_owner_summary || "No factory-owner summary available."}
        </p>
      </article>
      <div className="intelligence-grid">
        <article className="content-card">
          <p className="eyebrow">Decision basis</p>
          <h3>What the model saw</h3>
          <p className="report-text">{result?.visual_explanation || "No explanation available."}</p>
        </article>
        <article className="content-card">
          <p className="eyebrow">Recommended next step</p>
          <h3>What the operator should do now</h3>
          <ul className="clean-list">
            {renderList(result?.recommended_fix, "No recommended next step available.")}
          </ul>
        </article>
        <article className="content-card">
          <p className="eyebrow">Process follow-up</p>
          <h3>What to investigate or improve</h3>
          <ul className="clean-list">
            {renderList(
              result?.possible_causes?.length ? result.possible_causes : result?.prevention,
              "No process follow-up guidance available."
            )}
          </ul>
        </article>
      </div>
    </div>
  );
}
