# Final Handoff

Primary detailed handoff:

- [docs/developer_handoff_detailed.md](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/docs/developer_handoff_detailed.md)

## Current Status

Local app ready. Dataset ready. Live AMD validation completed.

AMD droplet received:

- GPU: AMD MI300X
- Public IPv4: `134.199.196.106`
- Target endpoint: `http://134.199.196.106:8000/v1/chat/completions`

Live endpoint access is through the active local SSH tunnel:

```text
VLLM_URL=http://localhost:8000/v1/chat/completions
MODEL_NAME=Qwen/Qwen2.5-VL-7B-Instruct
DEMO_MODE=false
```

Validation results:

- `/v1/models` returns `Qwen/Qwen2.5-VL-7B-Instruct`
- `scripts/validate_vllm.py` passes text, remote image, local image, and schema-constrained JSON checks
- `main.py` completed 20 live MVTec inspections
- React/Vite frontend produced live `PASS`, `ALERT_OPERATOR`, and `STOP_LINE` results
- SQLite event log, shift report, operations alert, and AMD runtime metrics update correctly
- Gradio fallback boots with HTTP 200

## To Finish

1. Keep the SSH tunnel active during recording.
2. Start FastAPI with `.venv/bin/python -m uvicorn api:app --host 127.0.0.1 --port 8013`.
3. Start Gradio fallback only if needed with `.venv/bin/python app.py`.
4. Record the demo using the React/Vite frontend as the primary interface.
5. Start MindsDB if sponsor-specific SQL analytics need to be shown live.
6. Stop or destroy the AMD droplet after recording to avoid extra cost.

## Final Submission Assets

- GitHub repo
- Hugging Face Space
- 3-minute demo video
- README
- architecture diagram
- proof screenshots in `docs/proof/`
