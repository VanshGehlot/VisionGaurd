import { NavLink } from "react-router-dom";
import BrandLogo from "./BrandLogo";

const items = [
  { to: "/dashboard", label: "Dashboard", meta: "Live command center", mark: "D" },
  { to: "/inspection", label: "Inspection", meta: "Single-frame decisions", mark: "I" },
  { to: "/reports", label: "Reports", meta: "Shift and batch review", mark: "R" },
  { to: "/adaptation", label: "Adaptation", meta: "Factory model rollout", mark: "A" },
  { to: "/settings", label: "Settings", meta: "Truth and controls", mark: "S" },
];

export default function Sidebar({
  isOpen,
  isPinned,
  isCompact,
  onToggleOpen,
  onTogglePinned,
  onToggleCompact,
}) {
  return (
    <aside className="sidebar" aria-label="Primary navigation" data-open={isOpen}>
      <div className="sidebar-top">
        <NavLink to="/" className="sidebar-brand" aria-label="VisionGuard landing">
          <BrandLogo variant="horizontal" size="sm" />
        </NavLink>
        <button
          className="sidebar-icon-button sidebar-close-button"
          type="button"
          onClick={onToggleOpen}
          aria-label={isOpen ? "Hide sidebar" : "Show sidebar"}
          title={isOpen ? "Hide sidebar" : "Show sidebar"}
        >
          {isOpen ? "‹" : "›"}
        </button>
      </div>

      <div className="sidebar-controls" aria-label="Sidebar controls">
        <button
          className={`sidebar-control ${isCompact ? "is-active" : ""}`}
          type="button"
          onClick={onToggleCompact}
          aria-pressed={isCompact}
          title={isCompact ? "Expand sidebar" : "Collapse to rail"}
        >
          <span className="sidebar-control-dot" />
          <span className="sidebar-control-label">{isCompact ? "Expand" : "Compact"}</span>
        </button>
        <button
          className={`sidebar-control ${isPinned ? "is-active" : ""}`}
          type="button"
          onClick={onTogglePinned}
          aria-pressed={isPinned}
          title={isPinned ? "Unpin sidebar" : "Pin sidebar"}
        >
          <span className="sidebar-control-dot" />
          <span className="sidebar-control-label">{isPinned ? "Pinned" : "Pin"}</span>
        </button>
      </div>

      <nav className="sidebar-nav" aria-label="VisionGuard sections">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `sidebar-link ${isActive ? "is-active" : ""}`
            }
            title={item.label}
          >
            <span className="sidebar-link-initial" aria-hidden="true">
              {item.mark}
            </span>
            <span className="sidebar-link-copy">
              <span className="sidebar-link-label">{item.label}</span>
              <span className="sidebar-link-meta">{item.meta}</span>
            </span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <span className="sidebar-status-dot" />
        <span>
          <span className="sidebar-footer-title">Runtime stack</span>
          <span className="sidebar-footer-subtitle">AMD MI300X · ROCm</span>
        </span>
      </div>
    </aside>
  );
}
