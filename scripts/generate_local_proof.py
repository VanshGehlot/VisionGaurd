from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import inspect_image_ui, refresh_report


PROOF_DIR = Path("docs/proof")
GOOD_IMAGE = "examples/bottle_good_0.jpg"
DEFECT_IMAGE = "examples/bottle_broken_large_0.jpg"


def wrap_html(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    <style>
      body {{
        margin: 0;
        padding: 32px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background: linear-gradient(180deg, #eff6f6 0%, #f8fafc 100%);
        color: #0f172a;
      }}
      .shell {{
        max-width: 1100px;
        margin: 0 auto;
      }}
      h1 {{
        margin: 0 0 18px;
        font-size: 40px;
      }}
      .panel {{
        background: #ffffff;
        border: 1px solid #d8e3e6;
        border-radius: 22px;
        padding: 22px;
        box-shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
      }}
      table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
      }}
      th, td {{
        border: 1px solid #e2e8f0;
        padding: 10px 12px;
        text-align: left;
        vertical-align: top;
      }}
      th {{
        background: #f8fafc;
      }}
      pre {{
        white-space: pre-wrap;
        font-size: 15px;
        line-height: 1.6;
      }}
    </style>
  </head>
  <body>
    <div class="shell">
      <h1>{title}</h1>
      <div class="panel">
        {body}
      </div>
    </div>
  </body>
</html>
"""


def save_html(name: str, title: str, body: str) -> None:
    PROOF_DIR.mkdir(parents=True, exist_ok=True)
    (PROOF_DIR / name).write_text(wrap_html(title, body), encoding="utf-8")


def dataframe_to_html(df: pd.DataFrame) -> str:
    if df.empty:
        return "<p>No rows available.</p>"
    return df.to_html(index=False, escape=False)


def main() -> None:
    good_html, _, _, _ = inspect_image_ui(GOOD_IMAGE, "LINE-A1", "morning")
    defect_html, _, _, _ = inspect_image_ui(DEFECT_IMAGE, "LINE-A1", "morning")
    logs_df, report_text = refresh_report()

    save_html("gradio-good-result.html", "VisionGuard Good Result", good_html)
    save_html("gradio-defect-result.html", "VisionGuard Defect Result", defect_html)
    save_html("event-log.html", "VisionGuard Event Log", dataframe_to_html(logs_df))
    save_html("shift-report.html", "VisionGuard Shift Report", f"<pre>{report_text}</pre>")

    # Capture a short validation note for the blocked live endpoint.
    (PROOF_DIR / "vllm-validation.txt").write_text(
        "Live AMD vLLM validation is still pending the real MI300X endpoint.\n"
        "Run `.venv/bin/python scripts/validate_vllm.py` once `VLLM_URL` is available.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
