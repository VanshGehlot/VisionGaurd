import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path

from config import get_settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS defect_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT,
  image_id TEXT,
  product_type TEXT,
  defect_detected INTEGER,
  defect_type TEXT,
  defect_category TEXT,
  severity TEXT,
  confidence REAL,
  location TEXT,
  region_horizontal TEXT,
  region_vertical TEXT,
  action_taken TEXT,
  line_id TEXT,
  shift TEXT,
  processing_ms INTEGER,
  model_name TEXT,
  visual_explanation TEXT,
  possible_causes TEXT,
  recommended_fix TEXT,
  prevention TEXT,
  factory_owner_summary TEXT
);
"""

EXPECTED_COLUMNS = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "timestamp": "TEXT",
    "image_id": "TEXT",
    "product_type": "TEXT",
    "defect_detected": "INTEGER",
    "defect_type": "TEXT",
    "defect_category": "TEXT",
    "severity": "TEXT",
    "confidence": "REAL",
    "location": "TEXT",
    "region_horizontal": "TEXT",
    "region_vertical": "TEXT",
    "action_taken": "TEXT",
    "line_id": "TEXT",
    "shift": "TEXT",
    "processing_ms": "INTEGER",
    "model_name": "TEXT",
    "visual_explanation": "TEXT",
    "possible_causes": "TEXT",
    "recommended_fix": "TEXT",
    "prevention": "TEXT",
    "factory_owner_summary": "TEXT",
}


def get_conn() -> sqlite3.Connection:
    settings = get_settings()
    Path(settings.sqlite_db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.sqlite_db_path)
    conn.execute(SCHEMA)
    _ensure_columns(conn)
    conn.commit()
    return conn


def _ensure_columns(conn: sqlite3.Connection) -> None:
    existing = {
        row[1]
        for row in conn.execute("PRAGMA table_info(defect_logs)").fetchall()
    }
    for column_name, column_type in EXPECTED_COLUMNS.items():
        if column_name not in existing and column_name != "id":
            conn.execute(f"ALTER TABLE defect_logs ADD COLUMN {column_name} {column_type}")


def insert_defect_log(event: dict) -> None:
    region = event.get("region") if isinstance(event.get("region"), dict) else {}
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO defect_logs (
            timestamp, image_id, product_type, defect_detected, defect_type,
            defect_category, severity, confidence, location, region_horizontal,
            region_vertical, action_taken, line_id, shift, processing_ms,
            model_name, visual_explanation, possible_causes, recommended_fix,
            prevention, factory_owner_summary
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now(timezone.utc).isoformat(),
            event.get("image_id"),
            event.get("product_type"),
            int(bool(event.get("defect_detected"))),
            event.get("defect_type"),
            event.get("defect_category"),
            event.get("severity"),
            float(event.get("confidence", 0.0)),
            event.get("location"),
            region.get("horizontal"),
            region.get("vertical"),
            event.get("action"),
            event.get("line_id"),
            event.get("shift"),
            int(event.get("processing_ms", 0)),
            event.get("model_name"),
            event.get("visual_explanation"),
            json.dumps(event.get("possible_causes", [])),
            json.dumps(event.get("recommended_fix", [])),
            json.dumps(event.get("prevention", [])),
            event.get("factory_owner_summary"),
        ),
    )
    conn.commit()
    conn.close()


def get_logs(limit: int = 100) -> tuple[list[str], list[tuple]]:
    conn = get_conn()
    cursor = conn.execute("SELECT * FROM defect_logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    columns = [column[0] for column in cursor.description] if cursor.description else []
    conn.close()
    return columns, rows


def get_analytics_summary() -> dict:
    conn = get_conn()
    try:
        row = conn.execute(
            """
            SELECT
              COUNT(*) AS total_inspected,
              SUM(CASE WHEN defect_detected THEN 1 ELSE 0 END) AS defects_found,
              SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) AS critical_events,
              AVG(processing_ms) AS avg_latency_ms,
              MAX(id) AS latest_id
            FROM defect_logs
            """
        ).fetchone()
        latest = conn.execute(
            """
            SELECT processing_ms, model_name
            FROM defect_logs
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
    finally:
        conn.close()

    total_inspected = int((row[0] or 0) if row else 0)
    defects_found = int((row[1] or 0) if row else 0)
    critical_events = int((row[2] or 0) if row else 0)
    avg_latency_ms = float((row[3] or 0.0) if row else 0.0)
    latest_latency_ms = int((latest[0] or 0) if latest else 0)
    model_name = latest[1] if latest and latest[1] else get_settings().model_name
    defect_rate = (defects_found / total_inspected * 100.0) if total_inspected else 0.0
    estimated_images_per_min = int(60000 / avg_latency_ms) if avg_latency_ms > 0 else 0

    return {
        "total_inspected": total_inspected,
        "defects_found": defects_found,
        "critical_events": critical_events,
        "avg_latency_ms": avg_latency_ms,
        "latest_latency_ms": latest_latency_ms,
        "defect_rate": defect_rate,
        "estimated_images_per_min": estimated_images_per_min,
        "model_name": model_name,
        "runtime": "AMD MI300X · ROCm · vLLM",
    }
