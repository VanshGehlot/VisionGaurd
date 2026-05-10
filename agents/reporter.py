import json
import sqlite3
from collections import Counter
from pathlib import Path

from config import get_settings

SEVERITY_RANK = {
    "ok": 0,
    "warning": 1,
    "critical": 2,
}


def reporter_agent() -> str:
    """
    Summarize the current shift using locally logged inspection data.
    """
    events = load_logged_events()
    if not events:
        return "No inspection data available yet."
    return summarize_events(events)


def operations_alert_agent() -> str:
    events = load_logged_events()
    if not events:
        return "Operations Alert:\nNo defect spike or line-level risk has been detected yet."
    return build_operations_alert(events)


def load_logged_events() -> list[dict]:
    settings = get_settings()
    if not Path(settings.sqlite_db_path).exists():
        return []

    conn = sqlite3.connect(settings.sqlite_db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT * FROM defect_logs").fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()

    return [_row_to_event(row) for row in rows]


def summarize_events(events: list[dict]) -> str:
    if not events:
        return "No inspection data available yet."

    total = len(events)
    defects = [event for event in events if event.get("defect_detected")]
    total_defects = len(defects)
    defect_rate = (total_defects / total) * 100 if total else 0.0

    defect_types = Counter(event.get("defect_type") for event in defects if event.get("defect_type"))
    most_common_defect = defect_types.most_common(1)[0][0] if defect_types else "none"
    defect_categories = Counter(
        event.get("defect_category") for event in defects if event.get("defect_category")
    )
    most_common_category = defect_categories.most_common(1)[0][0] if defect_categories else "none"

    highest_severity = max(
        (str(event.get("severity", "ok")) for event in events),
        key=lambda severity: SEVERITY_RANK.get(severity, 0),
        default="ok",
    )
    avg_latency = sum(int(event.get("processing_ms", 0) or 0) for event in events) / total
    stop_line_count = len([event for event in events if event.get("action") == "STOP_LINE"])

    causes = Counter()
    preventions = Counter()
    for event in defects:
        for item in event.get("possible_causes", []):
            if item:
                causes[str(item)] += 1
        for item in event.get("prevention", []):
            if item:
                preventions[str(item)] += 1

    recommendation = (
        "pause the affected line, inspect the nearby batch, and review process settings before continuing full-speed production"
        if stop_line_count
        else "continue production while monitoring warning-level defects and validating preventive controls"
    )

    return (
        f"VisionGuard inspected {total} product images this shift and detected "
        f"{total_defects} potential defects, giving a defect rate of {defect_rate:.1f}%.\n\n"
        f'The most common defect type was "{most_common_defect}" and the most common defect '
        f'category was "{most_common_category}". The highest severity observed was '
        f'"{highest_severity}". Average Qwen-VL inference latency was {avg_latency:.0f}ms '
        f"per image on AMD MI300X.\n\n"
        f"The likely recurring causes include {_format_counter(causes)}. "
        f"Recommended action: {recommendation}. "
        f"Prevention summary: {_format_counter(preventions)}."
    )


def build_operations_alert(events: list[dict]) -> str:
    defects = [event for event in events if event.get("defect_detected")]
    if not defects:
        return (
            "Operations Alert:\n"
            "No defect spike or line-level risk has been detected yet. Continue production while maintaining normal inspection cadence."
        )

    line_risk = Counter(event.get("line_id", "unknown") for event in defects)
    highest_risk_line = line_risk.most_common(1)[0][0]
    defect_types = Counter(event.get("defect_type", "unknown") for event in defects)
    most_common_defect = defect_types.most_common(1)[0][0]
    likely_causes = Counter()
    preventions = Counter()
    immediate_actions = Counter()

    for event in defects:
        for cause in event.get("possible_causes", []):
            if cause:
                likely_causes[str(cause)] += 1
        for prevention in event.get("prevention", []):
            if prevention:
                preventions[str(prevention)] += 1
        for fix in event.get("recommended_fix", []):
            if fix:
                immediate_actions[str(fix)] += 1

    alert_prefix = (
        f"{most_common_defect.capitalize()}-related defects increased in the latest inspection batch."
    )
    return (
        "Operations Alert:\n"
        f"{alert_prefix}\n\n"
        f"Risk:\nCritical or warning-level defects are concentrated on Line {highest_risk_line}.\n\n"
        f"Most common likely cause:\n{_format_counter(likely_causes)}.\n\n"
        f"Recommended immediate action:\n{_format_counter(immediate_actions)}.\n\n"
        f"Prevention:\n{_format_counter(preventions)}."
    )


def _row_to_event(row: sqlite3.Row) -> dict:
    return {
        "defect_detected": bool(row["defect_detected"]),
        "defect_type": row["defect_type"],
        "defect_category": row["defect_category"],
        "severity": row["severity"],
        "confidence": row["confidence"],
        "processing_ms": row["processing_ms"],
        "action": row["action_taken"],
        "line_id": row["line_id"],
        "shift": row["shift"],
        "possible_causes": _parse_json_list(row["possible_causes"]),
        "recommended_fix": _parse_json_list(row["recommended_fix"]),
        "prevention": _parse_json_list(row["prevention"]),
    }


def _parse_json_list(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    try:
        value = json.loads(raw_value)
    except Exception:
        return []
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _format_counter(counter: Counter) -> str:
    if not counter:
        return "no recurring causes identified yet"
    return ", ".join(item for item, _ in counter.most_common(3))
