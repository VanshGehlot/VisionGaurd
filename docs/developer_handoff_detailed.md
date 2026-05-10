# VisionGuard Detailed Developer Handoff

This document is the full engineering handoff for any future AI developer or human engineer working on VisionGuard.

It explains:

- what VisionGuard is
- what has already been built
- how the current implementation works
- what was fixed during local validation
- what is still blocked
- what should happen next
- what to validate before pushing and submitting

## 1. Product Summary

VisionGuard is an industrial defect detection agent for manufacturing inspection workflows.

The target demo flow is:

```text
Upload product image
→ inspect with Qwen2.5-VL
→ classify defect type + severity
→ recommend action
→ log event in SQLite
→ expose analytics through MindsDB
→ generate shift-level report
```

The sponsor stack is:

- AMD MI300X: GPU inference host
- ROCm: AMD runtime
- vLLM: model serving layer
- Qwen2.5-VL-7B-Instruct: multimodal model
- Hugging Face: model + Space hosting
- MindsDB: analytics and reporting layer
- MVTec AD: industrial anomaly dataset

## 2. Current Status

Current state at handoff:

- local Python environment works
- dependencies are installed
- project compiles
- tests pass
- MVTec bottle subset is downloaded locally
- demo examples exist
- Gradio UI boots locally
- demo mode exists for non-blocking UI walkthroughs
- local screenshot proof exists
- demo-mode proof PNG artifacts exist
- AMD live inference validation is still blocked on the real `VLLM_URL`

In short:

```text
Local shell validated.
Remote AMD endpoint validation pending.
```

## 3. What Has Been Built

### Core application

- [app.py](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/app.py)
  Gradio product UI
- [main.py](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/main.py)
  CLI inspection pipeline over dataset images
- [config.py](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/config.py)
  central environment/config loader

### Agent layer

- [agents/scanner.py](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/agents/scanner.py)
  scanner agent calls multimodal inference
- [agents/logger.py](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/agents/logger.py)
  enriches and logs inspection events
- [agents/reporter.py](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/agents/reporter.py)
  generates shift report from SQLite logs

### Model layer

- [model/prompts.py](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/model/prompts.py)
  system and user prompts
- [model/qwen_client.py](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/model/qwen_client.py)
  OpenAI-compatible vLLM client
- [model/json_parser.py](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/model/json_parser.py)
  safe parser and normalization for model output

### Data layer

- [data/download_mvtec.py](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/data/download_mvtec.py)
  downloads and reconstructs local bottle subset
- [data/sample_loader.py](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/data/sample_loader.py)
  exports clean demo examples
- [mvtec_bottle](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/mvtec_bottle)
  local dataset artifact
- [examples](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/examples)
  demo images for good and defective products

### Database layer

- [db/sqlite_client.py](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/db/sqlite_client.py)
  SQLite primary logging client
- [db/schema.sql](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/db/schema.sql)
  SQLite schema
- [db/mindsdb_schema.sql](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/db/mindsdb_schema.sql)
  MindsDB database/table/view setup

### UI helper layer

- [ui/components.py](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/ui/components.py)
  result cards, mode banners, architecture footer
- [ui/styles.py](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/ui/styles.py)
  product styling
- [ui/mock_data.py](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/ui/mock_data.py)
  deterministic demo-mode inference

### Scripts and tests

- [scripts/validate_vllm.py](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/scripts/validate_vllm.py)
  readiness checker for the AMD endpoint
- [tests/test_json_parser.py](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/tests/test_json_parser.py)
- [tests/test_sqlite_client.py](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/tests/test_sqlite_client.py)
- [tests/test_reporter.py](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/tests/test_reporter.py)

### Demo and documentation assets

- [README.md](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/README.md)
- [docs/architecture.md](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/docs/architecture.md)
- [docs/architecture_ascii.txt](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/docs/architecture_ascii.txt)
- [docs/demo_script.md](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/docs/demo_script.md)
- [docs/submission_description.md](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/docs/submission_description.md)
- [docs/recording_checklist.md](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/docs/recording_checklist.md)
- [docs/social_posts.md](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/docs/social_posts.md)
- [docs/proof/README.md](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/docs/proof/README.md)
- [docs/proof/gradio-good-result.png](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/docs/proof/gradio-good-result.png)
- [docs/proof/gradio-defect-result.png](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/docs/proof/gradio-defect-result.png)
- [docs/proof/event-log.png](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/docs/proof/event-log.png)
- [docs/proof/shift-report.png](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/docs/proof/shift-report.png)
- [docs/screenshots/gradio-local-home.png](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/docs/screenshots/gradio-local-home.png)

## 4. Important Implementation Decisions

### SQLite is the primary logging layer

This is intentional.

The app should not depend on MindsDB being up in order to function.

Correct architecture:

```text
SQLite = primary operational log
MindsDB = analytics and sponsor integration layer
```

That means:

- `logger_agent()` always writes to SQLite
- `reporter_agent()` always reads from SQLite
- MindsDB can be attached after the core loop works

### Demo mode was intentionally added

`DEMO_MODE=true` exists so the UI can be tested or recorded even when the AMD endpoint is temporarily unavailable.

Important rule:

- demo mode is for UI walkthroughs and mock recording only
- live validation still requires the real AMD endpoint
- demo mode is clearly labeled in the UI to avoid accidental misrepresentation

### Config is centralized

All environment-driven runtime values were centralized into [config.py](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/config.py).

This was done to avoid inconsistent `os.getenv(...)` usage across multiple files and to make future changes safer.

The implementation uses `get_settings()` for env-sensitive modules so tests can override environment variables correctly.

## 5. What Was Fixed During Development

### 1. The repo started empty

The workspace was initially empty. The first pass built a pitch-style static demo, then the repo was converted into the actual Python/Gradio product scaffold.

### 2. MVTec loader was wrong

The original assumption was that `Voxel51/MVTec-AD` exposed a `bottle` builder config and a `test` split through the `datasets` API in the simple way we expected.

That was wrong.

What was discovered:

- Hugging Face exposed only a `default` builder config
- the plain streaming loader did not expose the defect/category metadata we needed
- Voxel51’s `samples.json` contained the actual metadata linking filepaths to:
  - category
  - defect label
  - split

So [data/download_mvtec.py](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/data/download_mvtec.py) was rewritten to:

1. fetch `samples.json`
2. filter to `category == bottle`
3. download the corresponding image assets directly
4. build a local Hugging Face dataset with:
   - `image`
   - `anomaly_class`
   - `split`
   - `source_path`

This is the reason the local bottle subset now works correctly.

### 3. Gradio 6 constructor warning

The original `Blocks(...)` usage passed `css` and `theme` in the wrong place for the installed Gradio version.

This was corrected by moving those values into `demo.launch(...)`.

### 4. Fallback inference UX

The fallback error state now explains exactly what is wrong when live inference is unavailable:

- the AMD endpoint is not connected or reachable
- `VLLM_URL` must be set
- `scripts/validate_vllm.py` should be run

### 5. Config caching vs tests

When config centralization was first introduced, test isolation broke because environment values were being bound too early.

This was fixed by:

- keeping the `Settings` dataclass
- introducing `get_settings()`
- making env-sensitive modules resolve settings at runtime where needed

### 6. Generated clutter removed

The repo contained generated Python cache directories and `.pytest_cache`.

Those were removed and `.gitignore` was tightened so the tree stays clean.

## 6. Current Runtime Modes

### Live mode

Controlled by:

```env
DEMO_MODE=false
```

Behavior:

- `scanner_agent()` calls the real vLLM endpoint
- `app.py` returns real inference results
- `main.py` tries to process the real dataset through the endpoint

### Demo mode

Controlled by:

```env
DEMO_MODE=true
```

Behavior:

- no external inference call is required
- the app returns deterministic mock outputs based on the example filename
- the UI is clearly labeled:
  `Demo Mode: simulated inference results are enabled.`

Mock mappings:

- `good` → `PASS`
- `broken_large` → `STOP_LINE`
- `broken_small` → `ALERT_OPERATOR`
- `contamination` → `ALERT_OPERATOR`

## 7. Local Validation Completed So Far

These have already been completed:

- virtualenv created
- dependencies installed
- compile checks passed
- tests passed
- bottle dataset downloaded and rebuilt
- example images exported
- Gradio app launched locally
- Gradio screenshot saved
- SQLite logging and reporter path validated

Proof assets currently in repo:

- [docs/screenshots/gradio-local-home.png](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/docs/screenshots/gradio-local-home.png)
- [docs/local_validation.md](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/docs/local_validation.md)
- [docs/proof/README.md](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/docs/proof/README.md)

## 8. What Is Still Blocked

The only meaningful blocker is the real AMD endpoint.

Still missing:

- AMD MI300X host/IP or public inference URL
- live vLLM server for `Qwen/Qwen2.5-VL-7B-Instruct`
- final real multimodal inference validation

Until that exists, these cannot be completed truthfully:

- real endpoint readiness proof
- real `main.py` inference output
- real good product `PASS` screenshot
- real defective product `STOP_LINE` or `ALERT_OPERATOR` screenshot
- real populated event log from live model runs
- real shift report from live model runs

## 9. Exactly What To Do When AMD Endpoint Arrives

### Step 1. Update `.env`

Edit [`.env`](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/.env):

```env
VLLM_URL=http://<AMD_IP>:8000/v1/chat/completions
MODEL_NAME=Qwen/Qwen2.5-VL-7B-Instruct
DEMO_MODE=false
```

### Step 2. Validate endpoint

Run:

```bash
.venv/bin/python scripts/validate_vllm.py | tee docs/proof/vllm-validation.txt
```

Expected:

- text request passes
- remote image request passes
- local image request passes
- structured defect prompt passes

### Step 3. Validate CLI pipeline

Run:

```bash
.venv/bin/python main.py | tee docs/proof/main-pipeline-output.txt
```

Expected:

- good bottle images trend toward `PASS`
- broken/contamination images trend toward `ALERT_OPERATOR` or `STOP_LINE`
- latencies appear in output

### Step 4. Validate Gradio app

Run:

```bash
.venv/bin/python app.py
```

Then manually test:

- upload `examples/bottle_good_0.jpg`
- upload `examples/bottle_broken_large_0.jpg`
- upload `examples/bottle_broken_small_0.jpg`
- upload `examples/bottle_contamination_0.jpg`

Capture screenshots into [docs/proof](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/docs/proof):

- `gradio-good-result.png`
- `gradio-defect-result.png`
- `event-log.png`
- `shift-report.png`

### Step 5. Start MindsDB only after inference works

Run:

```bash
./docker/run_mindsdb.sh
```

Then apply:

- [db/mindsdb_schema.sql](/Users/vanshgehlot/Downloads/just_hire/AMDxVision/db/mindsdb_schema.sql)

This step is secondary. Do not block the demo on MindsDB.

## 10. What Should Be Pushed Next

Nothing here should be fundamentally re-architected before AMD validation.

The next push should happen after:

1. real AMD endpoint is connected
2. validator passes
3. `main.py` produces real inference output
4. `app.py` is tested with live inference
5. proof artifacts are captured
6. any small endpoint-specific fixes are applied

Recommended push sequence:

### Push 1

After real endpoint validation and proof artifacts:

- updated `.env.example` only if needed
- any minor inference fixes
- updated docs/proof artifacts
- final README adjustments

### Push 2

After MindsDB validation and final demo capture:

- final screenshots
- final recording assets
- final submission text

## 11. What Should Not Be Done Right Now

Do not spend time on:

- replacing the current React/Vite shell with a more ambitious framework migration
- authentication
- live CCTV streaming
- fine-tuning
- bounding boxes
- mobile app
- payments
- unrelated dashboards
- infra sprawl outside the hackathon demo path

The winning path remains:

```text
working demo > ambitious broken system
```

## 12. Quick Command Reference

### Install and test

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

### Rebuild dataset artifacts

```bash
python data/download_mvtec.py
python data/sample_loader.py
```

### Run demo mode locally

```bash
DEMO_MODE=true .venv/bin/python app.py
```

### Run live mode locally

```bash
DEMO_MODE=false .venv/bin/python app.py
```

### Validate live AMD endpoint

```bash
.venv/bin/python scripts/validate_vllm.py
```

### Run CLI pipeline

```bash
.venv/bin/python main.py
```

## 13. Final Summary

VisionGuard is not waiting on product design anymore.

It already has:

- structured codebase
- dataset
- Gradio shell
- demo mode
- validator
- tests
- proof folder
- docs

The only remaining high-risk dependency is:

```text
real AMD MI300X vLLM endpoint availability
```

Once that arrives, the repo is set up so a future AI developer can move directly into:

1. endpoint validation
2. real pipeline run
3. proof capture
4. MindsDB attachment
5. demo recording
6. final push and submission
