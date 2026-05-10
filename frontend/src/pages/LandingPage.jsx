import { Link } from "react-router-dom";
import StatusBadge from "../components/StatusBadge";
import BrandLogo from "../components/BrandLogo";
import SystemBanner from "../components/SystemBanner";
import { useAppContext } from "../state/AppContext";
import { getDataStatus, getRuntimeStatus } from "../lib/ui";

const stack = ["AMD MI300X", "ROCm", "vLLM", "Qwen-VL", "MindsDB"];

const proofPoints = [
  { label: "Decision system", value: "Release / Review / Stop line", meta: "One canonical decision language for every frame" },
  { label: "Operator evidence", value: "Frame + reason + next step", meta: "Explain why the item moved and what happens next" },
  { label: "Factory learning", value: "Feedback to model route", meta: "Turn review decisions into better factory-specific behavior" },
];

const workflow = [
  ["01", "Inspect", "Upload a product frame from a factory camera or QA station."],
  ["02", "Reason", "Qwen-VL classifies severity and explains visible evidence."],
  ["03", "Act", "VisionGuard routes PASS, operator review, or STOP_LINE decisions."],
  ["04", "Improve", "Reports, feedback, and adapters turn events into factory learning."],
];

const capabilities = [
  "Inspection decisions stay readable for operators instead of exposing raw model jargon.",
  "Live system status is explicit so demo, offline, and live states are not confused.",
  "Shift reporting and event review sit beside inspection, not in a separate analyst workflow.",
  "Factory adaptation is guided as a rollout path instead of a registry dump.",
];

export default function LandingPage() {
  const { health, metrics, loading, serviceStatus, error, refreshSystemData } = useAppContext();
  const runtimeStatus = getRuntimeStatus({ health, metrics, loading });
  const dataStatus = getDataStatus({ serviceStatus, loading });
  const latency = metrics?.latest_latency_ms ? `${metrics.latest_latency_ms}ms` : "Live-ready";
  const bannerTone = error ? dataStatus.tone : runtimeStatus.id === "live" ? null : runtimeStatus.tone;
  const bannerTitle = error
    ? dataStatus.badge
    : runtimeStatus.id !== "live"
      ? runtimeStatus.badge
      : "";
  const bannerBody = error || (runtimeStatus.id !== "live" ? runtimeStatus.description : "");

  return (
    <div className="home-shell">
      <header className="home-nav">
        <Link to="/" className="home-brand" aria-label="VisionGuard home">
          <BrandLogo variant="horizontal" size="md" subtitle="Industrial visual AI" />
        </Link>
        <nav className="home-links" aria-label="Product navigation">
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/inspection">Inspection</Link>
          <Link to="/reports">Reports</Link>
          <Link to="/adaptation">Adaptation</Link>
          <Link to="/settings">Settings</Link>
        </nav>
        <div className="home-nav-status">
          <StatusBadge tone={runtimeStatus.tone}>{runtimeStatus.badge}</StatusBadge>
          <StatusBadge tone={dataStatus.tone}>{dataStatus.badge}</StatusBadge>
          <StatusBadge tone="amd">AMD MI300X</StatusBadge>
        </div>
      </header>

      <main>
        {bannerTitle ? (
          <SystemBanner
            tone={bannerTone}
            title={bannerTitle}
            body={bannerBody}
            actionLabel={error ? "Refresh status" : undefined}
            onAction={error ? () => refreshSystemData() : undefined}
          />
        ) : null}
        <section className="home-hero">
          <div className="home-hero-copy">
            <div className="home-kicker">
              <span />
              Industrial AI inspection for every factory camera
            </div>
            <h1>Quality decisions at line speed.</h1>
            <p>
              VisionGuard turns one product frame into a clear release decision,
              supporting evidence, and the next factory action using Qwen-VL on
              AMD MI300X.
            </p>
            <div className="home-actions">
              <Link to="/inspection" className="button button-primary">Run inspection</Link>
              <Link to="/dashboard" className="button button-secondary">Open command center</Link>
            </div>
            <div className="home-stack-strip" aria-label="Runtime stack">
              {stack.map((item) => (
                <StatusBadge key={item} tone={item === "AMD MI300X" ? "amd" : "neutral"} compact>
                  {item}
                </StatusBadge>
              ))}
            </div>
          </div>

          <div className="home-console" aria-label="VisionGuard inspection preview">
            <div className="home-console-top">
              <div>
                <span>Line A1</span>
                <strong>Inspection command</strong>
              </div>
              <StatusBadge tone="critical" compact>Stop line</StatusBadge>
            </div>
            <div className="home-console-body">
              <div className="home-product-frame">
                <img src="/examples/bottle_broken_large_1.jpg" alt="Defective bottle preview" />
                <div className="home-region-tag">Approximate region</div>
              </div>
              <div className="home-verdict-panel">
                <span>Operator evidence</span>
                <strong>Structural crack near bottle neck</strong>
                <p>Critical issue detected. Hold the item, inspect nearby units, and review transfer or cooling impact.</p>
              </div>
            </div>
            <div className="home-console-metrics">
              <div>
                <span>Latency</span>
                <strong>{latency}</strong>
              </div>
              <div>
                <span>Runtime</span>
                <strong>ROCm / vLLM</strong>
              </div>
              <div>
                <span>Model route</span>
                <strong>Qwen-VL</strong>
              </div>
            </div>
          </div>
        </section>

        <section className="home-proof-grid" aria-label="Product proof points">
          {proofPoints.map((item) => (
            <article className="home-proof-card" key={item.label}>
              <span>{item.label}</span>
              <strong>{item.value}</strong>
              <p>{item.meta}</p>
            </article>
          ))}
        </section>

        <section className="home-section home-workflow-section">
          <div className="home-section-heading">
            <p className="eyebrow">How it works</p>
            <h2>From camera frame to factory action in four steps.</h2>
          </div>
          <div className="home-workflow-grid">
            {workflow.map(([number, title, body]) => (
              <article className="home-workflow-card" key={number}>
                <span>{number}</span>
                <h3>{title}</h3>
                <p>{body}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="home-section home-split-section">
          <article className="home-dark-panel">
            <p className="eyebrow">Why it matters</p>
            <h2>Built for operators, quality leads, and factory owners.</h2>
            <p>
              The product does not stop at classification. It explains what happened,
              what should happen next, and whether the system is live, demo, or degraded.
            </p>
          </article>
          <article className="home-capability-panel">
            <p className="eyebrow">Product capabilities</p>
            <ul>
              {capabilities.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </article>
        </section>

        <section className="home-final-cta">
          <div>
            <p className="eyebrow">Ready for demo</p>
            <h2>Run an inspection, review the event trail, then open factory adaptation.</h2>
          </div>
          <div className="home-actions">
            <Link to="/inspection" className="button button-primary">Run inspection</Link>
            <Link to="/reports" className="button button-secondary">Open reports</Link>
          </div>
        </section>
      </main>
    </div>
  );
}
