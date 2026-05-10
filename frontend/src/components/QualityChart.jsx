function severityClass(severity) {
  const value = String(severity || "ok").toLowerCase();
  if (value === "critical") return "critical";
  if (value === "warning") return "warning";
  return "ok";
}

export function SeverityDistribution({ events = [] }) {
  const counts = events.reduce(
    (acc, event) => {
      acc[severityClass(event.severity)] += 1;
      return acc;
    },
    { ok: 0, warning: 0, critical: 0 }
  );
  const total = Math.max(1, events.length);
  const rows = [
    ["PASS", "ok", counts.ok],
    ["Warning", "warning", counts.warning],
    ["Critical", "critical", counts.critical],
  ];

  return (
    <article className="content-card chart-card">
      <div>
        <p className="eyebrow">Severity distribution</p>
        <h3>Inspection quality mix</h3>
      </div>
      <div className="bar-stack">
        {rows.map(([label, tone, count]) => (
          <div className="bar-row" key={label}>
            <div className="bar-row-label">
              <span>{label}</span>
              <strong>{count}</strong>
            </div>
            <div className="bar-track">
              <div
                className={`bar-fill bar-${tone}`}
                style={{ width: `${Math.max(4, (count / total) * 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </article>
  );
}

export function InspectionTimeline({ events = [] }) {
  const latest = events.slice(0, 8).reverse();
  return (
    <article className="content-card chart-card">
      <div>
        <p className="eyebrow">Inspection timeline</p>
        <h3>Recent line signal</h3>
      </div>
      <div className="timeline-strip">
        {latest.length ? (
          latest.map((event, index) => (
            <span
              key={event.image_id || event.id || index}
              className={`timeline-dot timeline-${severityClass(event.severity)}`}
              title={`${event.defect_category || event.defect_type || "none"} · ${event.action || "PASS"}`}
            />
          ))
        ) : (
          <span className="timeline-empty">No inspection signal yet</span>
        )}
      </div>
    </article>
  );
}
