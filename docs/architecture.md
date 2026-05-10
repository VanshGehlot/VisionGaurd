# VisionGuard Architecture

```text
Hugging Face Space / Gradio UI
        ↓
Scanner Agent
        ↓
AMD MI300X + ROCm + vLLM
        ↓
Qwen2.5-VL-7B-Instruct
        ↓
Defect JSON Parser
        ↓
Severity + Action Engine
        ↓
Approximate Region Annotation
        ↓
SQLite Event Log
        ↓
MindsDB Analytics Layer
        ↓
Reporter Agent
        ↓
Shift Quality Report
        ↓
Operations Alert + Factory Recommendation
```

## Sponsor Mapping

- AMD → GPU compute + ROCm
- Qwen → multimodal model
- Hugging Face → model hub + Space demo
- MindsDB → analytics/reporting layer
- MVTec AD → industrial defect dataset

## Runtime notes

- The Gradio app can run locally or on a Hugging Face Space.
- vLLM stays on the AMD MI300X host and exposes an OpenAI-compatible `/v1/chat/completions` endpoint.
- SQLite is the primary logging layer for the MVP.
- MindsDB reads the same SQLite database for analytics and reporting workflows.
- Optional video inspection samples frames sequentially and reuses the same scanner/logger/reporter path.

## Factory Adaptation Studio

VisionGuard now includes an additive factory adaptation path. The core live inspection loop remains unchanged, but the platform can register factory-specific datasets, train adapters, and route inference to the deployed factory model.

Demo architecture:

```text
Factory profile
        ↓
Dataset intake (DeepPCB)
        ↓
Dataset readiness + fine-tuning estimate
        ↓
Zero-shot baseline evaluation
        ↓
LoRA / adapter training job
        ↓
Model registry
        ↓
Inference route
        ↓
Factory-specific inspection path
        ↓
Operator feedback queue
        ↓
Next dataset / adapter version
```

For the hackathon demo, the primary deployed adapter use case is `Precision Circuits Demo Plant` with `PCB Assembly Line A`, `DeepPCB v1`, and `PCB Adapter v1`.

NanoDefects adds a second, truth-safe factory route for the steel bottle QA pilot:

```text
NanoDefects images
        ↓
Normalized dataset + labels
        ↓
Baseline evaluation + false PASS report
        ↓
Adapter readiness check
        ↓
NanoDefects Bottle QA evaluation route
        ↓
Prototype LoRA training pending more clean/PASS data
```

The NanoDefects route is not presented as a trained LoRA deployment until real adapter weights exist.

The inspection workspace now includes a model selector so the demo can show base VisionGuard inference, the active factory route, or the deployed PCB adapter route while preserving the same core inspection engine.

Future production versions can train real factory-private LoRA adapters without retraining the full base model.
