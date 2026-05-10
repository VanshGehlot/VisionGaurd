---
title: VisionGuard - Industrial AI Defect Detection
emoji: 🔍
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 4.44.1
app_file: app.py
pinned: true
license: mit
---

# VisionGuard — Real-Time Industrial Visual AI on AMD MI300X

VisionGuard is an industrial AI inspection system that turns factory camera frames into real-time quality decisions: **PASS**, **ALERT_OPERATOR**, or **STOP_LINE**.

It uses **Qwen2.5-VL-7B-Instruct** served through **vLLM on AMD MI300X** with **ROCm**, wrapped inside a production-style inspection console, reporting layer, and factory-adaptation workflow.

## What We Built

VisionGuard demonstrates how modern vision-language models can be used for industrial quality inspection across products such as bottles, metal parts, PCB boards, and hardware components.

The system supports:

- Real-time image inspection
- Batch/video frame inspection
- Defect classification and severity routing
- Operator review and STOP_LINE decisions
- Annotated inspection overlays
- Shift reports and event logs
- AMD runtime visibility
- Factory-specific adaptation workflow
- Model routing between base and factory-specialized models

## Why It Matters

Industrial inspection is still heavily dependent on manual checks or narrow classical vision systems. These systems often fail when product shape, lighting, defect type, or factory conditions change.

VisionGuard takes a more flexible approach:

```text
Factory image/video frame
→ Vision-language inspection
→ Safety-aware decision
→ Operator/reporting workflow
→ Factory-specific adaptation path
```

The goal is not just defect detection, but a broader **factory quality intelligence platform**.

## Core Demo Flow

```text
1. Upload or select a product image
2. VisionGuard sends it to Qwen-VL on AMD MI300X
3. The model returns structured inspection output
4. Backend applies safety and verification logic
5. UI shows PASS / ALERT_OPERATOR / STOP_LINE
6. Inspection event is logged
7. Reports and operations alerts update automatically
```

## Architecture

```text
React/Vite Frontend
        ↓
FastAPI Backend
        ↓
Inspection Orchestrator
        ↓
Qwen-VL via vLLM OpenAI-compatible API
        ↓
AMD MI300X + ROCm Runtime
        ↓
SQLite Event Store + Reporting Layer
```

### Main Components

| Layer | Role |
| --- | --- |
| React/Vite | Premium inspection console and dashboard |
| FastAPI | API wrapper for inspection, reports, adaptation, metrics |
| Qwen-VL | Vision-language model for defect reasoning |
| vLLM | High-performance model serving |
| AMD MI300X | GPU acceleration through ROCm |
| SQLite | Local event, report, and adaptation data store |
| Safety Net | Prevents risky false-PASS behavior |
| Reporter | Shift reports, events, operations alerts |
| Adaptation Studio | Factory-specific dataset/model onboarding workflow |

## Key Features

### 1. Live Visual Inspection

VisionGuard accepts product images and returns structured decisions:

```json
{
  "action": "STOP_LINE",
  "defect_type": "crack",
  "severity": "critical",
  "confidence": 0.91,
  "location": "upper neck region"
}
```

Supported actions:

```text
PASS
ALERT_OPERATOR
STOP_LINE
```

### 2. Safety-Aware Post Processing

The model output is verified through additional safety logic to reduce dangerous false PASS outcomes.

The system handles:

- low-confidence PASS results
- visible contamination patterns
- structural defect hints
- operator-review fallback
- clear debug fields for every override

### 3. Inspection Overlay

The UI generates visual inspection overlays:

- PASS badge for clean products
- REVIEW badge for uncertain cases
- localized box for contamination clusters
- approximate region for structural defects

The overlay is intentionally honest: it avoids fake full-image boxes and marks approximate regions when exact localization is not available.

### 4. Reports and Operations Alerts

Every inspection can be logged and summarized into:

- event history
- shift report
- defect trends
- stop-line events
- operations alerts
- AMD runtime metrics

This makes the app feel like a real factory command center, not only a model demo.

## Factory Adaptation Studio

VisionGuard also includes a factory-specific adaptation workflow.

The idea:

```text
Generic zero-shot inspection
→ customer uploads factory dataset
→ dataset readiness analysis
→ LoRA/adapter estimate
→ model registry
→ deployed factory route
→ feedback loop
```

For the demo, the adaptation story uses a PCB inspection use case inspired by the **DeepPCB** dataset and a real steel-bottle QA pilot dataset called **NanoDefects**.

The adaptation page shows how a customer can:

1. choose a product/use case
2. attach a dataset or model link
3. define defect classes and severity rules
4. analyze dataset readiness
5. estimate adapter training effort
6. deploy a factory-specific model route
7. use that route from the inspection page

Current implementation includes the adaptation workflow, registry, and routing layer. Full GPU LoRA training is planned as the next production step.

### NanoDefects Steel Bottle QA

NanoDefects is a real factory QA image set from a steel bottle / thermos / food jar line. It has been normalized under:

```text
data/nano_defects/
  raw_unannotated/
  annotated_reference_only/
  labels.json
  annotated_reference_labels.json
  README.md
  splits/
```

The current NanoDefects route is intentionally truth-safe:

```text
Status: baseline evaluated
Adapter: prototype training pending
Route: NanoDefects Bottle QA evaluation route
```

The current deterministic evaluation compares three routes:

| Route | False PASS | Defect recall | Clean PASS accuracy |
| --- | ---: | ---: | ---: |
| Generic raw baseline | 13 | 35.00% | 83.33% |
| NanoDefects safe mode | 0 | 100% | 0% |
| NanoDefects balanced mode | 0 | 100% | 83.33% |

Raw-image proof is saved in `docs/proof/nano-defects-raw-baseline.json` and `docs/proof/nano-defects-raw-vs-tuned.json`. Annotated/circled images are stored only as label references under `annotated_reference_only/` and are not used as model or evaluation input.

The earlier full-pilot live Qwen/AMD NanoDefects baseline was also run separately through the `NanoDefects Bottle QA — Evaluation Route` before the raw/reference split:

```text
Live Qwen/AMD baseline: 50/50 images processed
False PASS: 12
Defect recall: 72.73%
Clean PASS accuracy: 66.67%
```

The deterministic raw tuned-policy proof remains separate from the live Qwen baseline. `NanoDefects Bottle QA — Evaluation Route` is not a trained LoRA adapter. A production LoRA/adapter should wait until the factory has collected a more balanced raw dataset, with a minimum next target of 100 clean + 300 defect images and an ideal pilot target of 500-1,000 labeled images.

## AMD Usage

VisionGuard is designed around AMD acceleration:

```text
AMD MI300X
ROCm
vLLM
Qwen2.5-VL-7B-Instruct
```

The live model endpoint is served through vLLM using an OpenAI-compatible API.

Example endpoint:

```text
http://localhost:8000/v1/chat/completions
```

## Project Structure

```text
.
├── api.py                     # FastAPI app and API routes
├── app.py                     # Gradio fallback UI
├── main.py                    # CLI inspection pipeline
├── agents/
│   ├── reporter.py            # Reports and operations alerts
│   └── adaptation.py          # Factory adaptation workflow
├── model/
│   ├── qwen_client.py         # vLLM/Qwen API client
│   ├── prompts.py             # Inspection prompts/schema
│   └── json_parser.py         # Structured output fallback
├── utils/
│   ├── annotation.py          # Inspection overlays
│   ├── safety_net.py          # False-PASS safety layer
│   ├── pass_verifier.py       # PASS verification logic
│   └── visual_heuristics.py   # Visual defect heuristics
├── db/
│   └── sqlite_client.py       # Local event store
├── frontend/
│   └── src/                   # React/Vite frontend
├── tests/                     # Regression and safety tests
└── docs/
    └── proof/                 # Demo proof artifacts
```

## Running Locally

### 1. Install backend dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Install frontend dependencies

```bash
cd frontend
npm install
npm run build
cd ..
```

### 3. Run FastAPI

```bash
DEMO_MODE=true \
SQLITE_DB_PATH=/tmp/visionguard.db \
python -m uvicorn api:app --host 127.0.0.1 --port 8013
```

Open:

```text
http://127.0.0.1:8013
```

## Running With AMD MI300X / vLLM

Set the model endpoint:

```bash
export VLLM_URL=http://localhost:8000/v1/chat/completions
export MODEL_NAME=Qwen/Qwen2.5-VL-7B-Instruct
export DEMO_MODE=false
```

Then run:

```bash
python -m uvicorn api:app --host 127.0.0.1 --port 8013
```

Health check:

```bash
curl http://127.0.0.1:8013/health
```

Expected live state:

```json
{
  "api": "online",
  "demo_mode": false,
  "vllm_reachable": true
}
```

## Validation

Run tests:

```bash
python -m pytest
```

Build frontend:

```bash
cd frontend
npm run build
```

Compile check:

```bash
python -m compileall api.py agents model utils db tests
```

## Demo Script

Recommended judge demo:

```text
1. Show VisionGuard landing/dashboard
2. Open Image Inspection
3. Run clean product → PASS
4. Run defective product → ALERT_OPERATOR / STOP_LINE
5. Show overlay + factory intelligence explanation
6. Open reports/events
7. Show AMD runtime and live vLLM status
8. Open Factory Adaptation Studio
9. Analyze DeepPCB/PCB dataset route
10. Show NanoDefects Bottle QA — Evaluation Route
11. Open inspection with PCB Adapter or NanoDefects route selected
```

## What Makes This Different

VisionGuard is not just a UI around a model.

It combines:

- real AMD MI300X inference
- structured VLM inspection
- safety-aware decision logic
- operator-facing UI
- reporting and alerting
- video/batch inspection
- factory-specific adaptation workflow
- model registry and routing concept

This creates a path from hackathon prototype to real industrial AI platform.

## Current Status

Implemented:

```text
✅ Live Qwen-VL inspection path
✅ AMD MI300X/vLLM integration
✅ React inspection console
✅ FastAPI backend
✅ SQLite logging
✅ Reports and operations alerts
✅ Defect overlay generation
✅ Safety-net and PASS verification
✅ Factory Adaptation Studio
✅ Model selector and route metadata
✅ Regression tests
```

Planned next:

```text
□ Real DeepPCB LoRA/adapter training
□ Saved adapter weights
□ Adapter loading into vLLM
□ Real before/after evaluation
□ Multi-factory deployment
□ Supabase/cloud backend for production users
```

## Team Note

VisionGuard was built for the AMD Developer Hackathon to demonstrate how AMD MI300X can power practical, real-time, vision-language industrial inspection workflows.

The project is designed to be demoable today and expandable into a production-ready factory quality platform.
