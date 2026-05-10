# Local Validation Proof

This repository is validated locally up to the point where remote AMD inference is required.

## Completed locally

- Python environment created and dependencies installed
- Project compiles under the local virtualenv
- Gradio app boots on port `7860`
- MVTec bottle subset downloaded and rebuilt locally
- Example bottle images exported for demo use
- SQLite logging and reporting path verified independently

## Local proof artifact

- Gradio screenshot: [gradio-local-home.png](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/docs/screenshots/gradio-local-home.png)

## AMD handoff

Set `VLLM_URL` in `.env` to the live MI300X endpoint:

```env
VLLM_URL=http://<AMD_IP>:8000/v1/chat/completions
MODEL_NAME=Qwen/Qwen2.5-VL-7B-Instruct
```

Then run:

```bash
.venv/bin/python scripts/validate_vllm.py
.venv/bin/python main.py
.venv/bin/python app.py
```
