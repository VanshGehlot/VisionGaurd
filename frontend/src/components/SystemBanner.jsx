export default function SystemBanner({
  tone = "info",
  title,
  body,
  actionLabel,
  onAction,
}) {
  if (!title && !body) {
    return null;
  }

  return (
    <section className={`system-banner system-banner-${tone}`}>
      <div className="system-banner-copy">
        <strong>{title}</strong>
        {body ? <p>{body}</p> : null}
      </div>
      {actionLabel && onAction ? (
        <button className="button button-secondary" type="button" onClick={onAction}>
          {actionLabel}
        </button>
      ) : null}
    </section>
  );
}
