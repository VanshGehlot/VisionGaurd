export default function LoadingState({ title = "Inspecting product frame…", copy }) {
  return (
    <div className="loading-state">
      <div className="loading-spinner" />
      <div className="loading-title">{title}</div>
      <div className="loading-copy">
        {copy || "Running Qwen-VL inference on AMD MI300X and updating factory intelligence…"}
      </div>
    </div>
  );
}
