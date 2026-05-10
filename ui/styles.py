APP_CSS = """
.gradio-container {
  background:
    radial-gradient(circle at top left, rgba(35, 139, 146, 0.12), transparent 28%),
    radial-gradient(circle at top right, rgba(245, 158, 11, 0.08), transparent 24%),
    linear-gradient(180deg, #eff6f6 0%, #f8fafc 100%);
}

.vg-hero {
  padding: 20px 0 8px;
}

.vg-brand-lockup {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
}

.vg-brand-mark {
  width: 220px;
  height: auto;
  flex: 0 0 auto;
  filter: drop-shadow(0 16px 24px rgba(15, 23, 42, 0.12));
}

.vg-subtitle {
  margin: 0;
  color: #334155;
  font-size: 18px;
  line-height: 1.6;
}

.vg-badge-row,
.vg-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.vg-badge,
.vg-chip {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
}

.vg-badge {
  background: #e2f3f2;
  color: #155e75;
  border: 1px solid #bfdbfe;
}

.vg-chip-muted {
  background: #eef2ff;
  color: #334155;
}

.vg-banner {
  padding: 12px 16px;
  border-radius: 16px;
  margin-bottom: 14px;
  font-size: 14px;
  font-weight: 600;
}

.vg-demo-banner {
  background: #fff7ed;
  color: #9a3412;
  border: 1px solid #fdba74;
}

.vg-live-banner {
  background: #ecfeff;
  color: #155e75;
  border: 1px solid #67e8f9;
}

.vg-card {
  border: 1px solid #d8e3e6;
  border-radius: 22px;
  padding: 20px;
  background: #ffffff;
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
}

.vg-error {
  border-color: #fecaca;
  background: #fff7f7;
}

.vg-label {
  color: #64748b;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.vg-status {
  margin-top: 8px;
  font-size: 28px;
  font-weight: 800;
}

.vg-grid {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 14px;
  color: #0f172a;
}

.vg-explanation {
  margin-top: 16px;
  color: #334155;
  line-height: 1.6;
}

.vg-intel-section {
  margin-top: 14px;
  color: #334155;
  line-height: 1.6;
}

.vg-intel-section p {
  margin: 6px 0 0;
}

.vg-list {
  margin: 8px 0 0;
  padding-left: 18px;
}

.vg-list li {
  margin: 4px 0;
}

.vg-footer {
  margin-top: 18px;
  padding: 14px 16px;
  border-radius: 18px;
  background: #0f172a;
  color: #e2e8f0;
  font-size: 14px;
  line-height: 1.6;
}

@media (max-width: 720px) {
  .vg-brand-mark {
    width: 180px;
  }

  .vg-grid {
    grid-template-columns: 1fr;
  }
}
""".strip()
