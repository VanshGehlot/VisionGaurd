import MetricCard from "./MetricCard";
import { getRuntimeStatus } from "../lib/ui";

export default function RuntimePanel({ metrics, health, frontendDemoMode, loading }) {
  const latestLatency = Math.round(Number(metrics?.latest_latency_ms || 0));
  const averageLatency = Math.round(Number(metrics?.avg_latency_ms || 0));
  const estimatedThroughput = Math.round(Number(metrics?.estimated_images_per_min || 0));
  const runtimeStatus = getRuntimeStatus({ health, metrics, frontendDemoMode, loading });

  return (
    <div className="runtime-panel">
      <div className="section-copy">
        <p className="eyebrow">AMD Runtime Performance</p>
        <h2>Qwen-VL served through vLLM on AMD MI300X with ROCm.</h2>
      </div>
      <div className="metric-grid metric-grid-runtime">
        <MetricCard label="Inference State" value={runtimeStatus.label} />
        <MetricCard label="Model Name" value={metrics?.model_name || "Qwen/Qwen2.5-VL-7B-Instruct"} />
        <MetricCard label="Latest Latency" value={`${latestLatency}ms`} />
        <MetricCard label="Average Latency" value={`${averageLatency}ms`} />
        <MetricCard label="Estimated Images / Minute" value={String(estimatedThroughput)} />
        <MetricCard label="Total Images Inspected" value={String(metrics?.total_inspected || 0)} />
      </div>
    </div>
  );
}
