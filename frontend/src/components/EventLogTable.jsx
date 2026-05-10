import {
  formatConfidence,
  formatDecisionLabel,
  formatSeverityLabel,
  formatTimestamp,
  truncateIdentifier,
} from "../lib/ui";

function severityClass(value) {
  const severity = String(value || "ok").toLowerCase();
  if (severity === "critical") return "critical";
  if (severity === "warning") return "warning";
  return "ok";
}

function actionClass(value) {
  const action = String(value || "PASS").toUpperCase();
  if (action === "STOP_LINE") return "critical";
  if (action === "ALERT_OPERATOR" || action === "LOG_WARNING") return "warning";
  return "ok";
}

export default function EventLogTable({ events = [], compact = false }) {
  return (
    <div className="table-shell">
      <table className="event-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Frame</th>
            <th>Finding</th>
            <th>Severity</th>
            <th>Decision</th>
            <th>Confidence</th>
            <th>Latency</th>
            {!compact ? <th>Model</th> : null}
          </tr>
        </thead>
        <tbody>
          {events.length ? (
            events.map((event) => (
              <tr key={event.image_id || event.id} className={`event-row-${actionClass(event.action)}`}>
                <td>{formatTimestamp(event.timestamp)}</td>
                <td title={event.image_id || event.id || ""}>{truncateIdentifier(event.image_id || event.id)}</td>
                <td>{event.defect_category || event.defect_type || "No confirmed defect"}</td>
                <td>
                  <span className={`table-badge ${severityClass(event.severity)}`}>
                    {formatSeverityLabel(event.severity)}
                  </span>
                </td>
                <td>
                  <span className={`table-badge ${actionClass(event.action)}`}>
                    {formatDecisionLabel(event.action)}
                  </span>
                </td>
                <td>{formatConfidence(event.confidence)}</td>
                <td>{event.processing_ms || 0}ms</td>
                {!compact ? <td>{event.model_name || "Qwen/Qwen2.5-VL-7B-Instruct"}</td> : null}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={compact ? 7 : 8} className="empty-row">
                No inspection events are available for this reporting window yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
