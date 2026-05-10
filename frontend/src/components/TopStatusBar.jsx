import StatusBadge from "./StatusBadge";
import { useAppContext } from "../state/AppContext";
import BrandLogo from "./BrandLogo";
import { getDataStatus, getRuntimeStatus, formatTimestamp } from "../lib/ui";

export default function TopStatusBar({ onToggleSidebar }) {
  const {
    health,
    metrics,
    frontendDemoMode,
    loading,
    serviceStatus,
    lastUpdated,
  } = useAppContext();
  const runtimeStatus = getRuntimeStatus({ health, metrics, frontendDemoMode, loading });
  const dataStatus = getDataStatus({ serviceStatus, loading });

  return (
    <div className="statusbar">
      <button
        className="statusbar-menu-button"
        type="button"
        onClick={onToggleSidebar}
        aria-label="Toggle sidebar"
      >
        ☰
      </button>
      <div className="statusbar-brand-block">
        <BrandLogo
          variant="horizontal"
          size="sm"
          subtitle={lastUpdated ? `Last sync ${formatTimestamp(lastUpdated)}` : "Runtime console"}
        />
      </div>
      <div className="statusbar-badges">
        <StatusBadge tone="amd">AMD MI300X</StatusBadge>
        <StatusBadge tone={runtimeStatus.tone}>{runtimeStatus.badge}</StatusBadge>
        <StatusBadge tone={dataStatus.tone}>{dataStatus.badge}</StatusBadge>
        <StatusBadge tone="neutral">Runtime: ROCm/vLLM</StatusBadge>
      </div>
    </div>
  );
}
