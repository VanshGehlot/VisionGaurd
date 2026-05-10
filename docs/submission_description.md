# VisionGuard Submission Description

VisionGuard is an industrial defect detection agent powered by Qwen2.5-VL running on AMD MI300X.

It turns factory camera frames or product images into structured quality-control decisions. The Scanner Agent detects cracks, contamination, deformation, and broken parts. The Logger Agent records every inspection into SQLite and MindsDB-compatible tables. The Reporter Agent generates shift-level quality reports.

The system uses AMD MI300X through ROCm and vLLM for multimodal inference, Qwen-VL for visual reasoning, Hugging Face for model and demo distribution, and MindsDB for analytics.

## Demo

Upload a product image. VisionGuard returns:

- defect detected / product ok
- defect type
- severity
- confidence
- recommended action
- inspection latency
- shift report

## Why it matters

Small and mid-sized manufacturers cannot afford traditional industrial vision systems. VisionGuard makes AI-powered quality control accessible using open models and AMD GPUs.
