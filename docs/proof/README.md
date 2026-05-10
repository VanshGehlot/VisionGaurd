# Proof Artifacts

This folder contains local and live AMD validation artifacts for the VisionGuard demo.

## Already present locally

- `vllm-models.txt`: live vLLM `/v1/models` response from the AMD MI300X endpoint
- `vllm-validation.txt`: live endpoint validator output covering text, remote image, local image, and structured defect JSON
- `main-pipeline-output.txt`: live CLI pipeline output over the MVTec bottle subset
- `rocm-smi.txt`: ROCm proof from the AMD MI300X host
- `gradio-good-result.html`: browser-viewable proof page for a `PASS` result
- `gradio-defect-result.html`: browser-viewable proof page for an `ALERT_OPERATOR` or `STOP_LINE` result
- `event-log.html`: browser-viewable proof page for the populated inspection log
- `shift-report.html`: browser-viewable proof page for the generated shift report
- `gradio-good-result.png`: PNG capture of the good-result proof page
- `gradio-defect-result.png`: PNG capture of the defect-result proof page
- `event-log.png`: PNG capture of the populated log proof page
- `shift-report.png`: PNG capture of the shift-report proof page
- `premium-frontend-landing.png`: PNG capture of the redesigned React/Vite landing page
- `premium-frontend-dashboard.png`: PNG capture of the React/Vite command center
- `premium-frontend-reports.png`: PNG capture of the reports and operations intelligence page
- `premium-frontend-settings.png`: PNG capture of the settings/runtime page
- `premium-frontend-stop-line.png`: PNG capture of the React/Vite inspection workflow after a live AMD `STOP_LINE` result
- `premium-frontend-pass.png`: PNG capture of the React/Vite inspection workflow after a live AMD `PASS` result
- `amd-runtime-panel.png`: PNG capture of live AMD runtime metrics
- `event-log.png`: PNG capture of logged live inspection events
- `shift-report.png`: PNG capture of the generated shift report
- `operations-alert.png`: PNG capture of the operations alert
- `gradio-fallback.png`: PNG capture proving the fallback Gradio app still boots

## Current live endpoint

The AMD endpoint is accessed through the active SSH tunnel:

```text
http://localhost:8000/v1/chat/completions
```

The public droplet IP is `134.199.196.106`, but the local app should use the tunnel URL during recording.

## Cost Control

The AMD MI300X droplet costs money while running. Stop or destroy it after final validation and demo recording.
