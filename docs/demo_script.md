# 3-Minute Demo Script

## 0:00-0:20 Hook

Open on the VisionGuard landing page.

Factories lose money when defects are detected too late, but traditional industrial vision systems are expensive and rigid. VisionGuard turns factory camera frames into inspection decisions, operator actions, and shift-level quality intelligence.

## 0:20-0:40 Architecture

Click into the Dashboard.

VisionGuard uses a three-agent architecture. The Scanner Agent sends images to Qwen2.5-VL running on AMD MI300X through ROCm and vLLM. The Logger Agent records results into SQLite and MindsDB-compatible tables. The Reporter Agent generates a shift-level quality summary and operations alert.

## 0:40-1:20 Defective Product Demo

Open the Inspection workspace. Select the broken bottle sample, run live inspection, and show the verdict-first result card. Emphasize `STOP_LINE`, defect category, confidence, latency, and the AMD MI300X runtime badge. Mention that the image is sent through the live `localhost:8000` SSH tunnel into the MI300X vLLM server.

## 1:20-1:50 Good Product Demo

Select the normal bottle image and show a clean `PASS` result. Emphasize that the system is distinguishing normal products from defective ones rather than flagging everything.

## 1:50-2:20 Event Log

Open Reports. Point to the event log table and explain that every inspection is persisted with defect type, severity, confidence, location, action, line ID, shift, and model metadata.

## 2:20-2:45 Shift Report

Show the shift report and factory operations alert. Explain that the Reporter Agent summarizes total inspections, defect rate, dominant defect type, likely cause, highest severity, and the recommended production action.

## Optional 60-90 second add-on: Factory Adaptation

Open Factory Adaptation.

VisionGuard starts with zero-shot inspection, but each factory has different products, tolerances, and defect taxonomies. This page shows the factory-specific path: DeepPCB demonstrates the adapter lifecycle, while NanoDefects is a real steel-bottle QA evaluation route imported from factory images. NanoDefects now separates raw factory inputs from annotated/circled label references; on the raw evaluation subset, the generic baseline false-passes 13 defective images, while safe and balanced NanoDefects modes reduce false PASS to 0 in the deterministic evaluation. LoRA training is intentionally pending until the dataset has more balanced raw clean and defect examples.

Use this if the demo has enough time or if judges ask how the system improves beyond the initial model.

## 2:45-3:00 Close

VisionGuard makes industrial AI inspection accessible using open models and AMD GPUs. The same architecture scales from single-image inspection to high-throughput manufacturing lines.

After recording, stop or destroy the AMD GPU droplet to avoid extra cost.
