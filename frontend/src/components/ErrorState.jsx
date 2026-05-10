import { sanitizeOperatorError } from "../lib/ui";

function inferTitle(message) {
  const copy = String(message || "").toLowerCase();
  if (copy.includes("inference endpoint unavailable") || copy.includes("live amd inference is unavailable")) {
    return "Live inference unavailable.";
  }
  if (copy.includes("parsed as an image") || copy.includes("valid image")) {
    return "Invalid image file.";
  }
  return "Inspection issue.";
}

export default function ErrorState({ title, message, actionLabel, onAction }) {
  const safeMessage = sanitizeOperatorError(message, "VisionGuard could not complete this step. Please try again.");

  return (
    <div className="error-state">
      <div className="error-title">{title || inferTitle(safeMessage)}</div>
      <div className="error-copy">{safeMessage}</div>
      {actionLabel ? (
        <button className="button button-secondary" onClick={onAction}>
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}
