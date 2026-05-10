import json
import sqlite3
from datetime import datetime, timezone

from db.sqlite_client import get_conn


ADAPTATION_SCHEMA = """
CREATE TABLE IF NOT EXISTS factories (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  industry TEXT,
  location TEXT,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS product_lines (
  id TEXT PRIMARY KEY,
  factory_id TEXT NOT NULL,
  name TEXT NOT NULL,
  product_type TEXT,
  description TEXT,
  created_at TEXT,
  FOREIGN KEY(factory_id) REFERENCES factories(id)
);

CREATE TABLE IF NOT EXISTS adaptation_datasets (
  id TEXT PRIMARY KEY,
  factory_id TEXT NOT NULL,
  product_line_id TEXT NOT NULL,
  name TEXT NOT NULL,
  source TEXT,
  version TEXT,
  status TEXT,
  sample_count INTEGER,
  train_count INTEGER,
  validation_count INTEGER,
  resolution TEXT,
  format TEXT,
  defect_classes_json TEXT,
  created_at TEXT,
  FOREIGN KEY(factory_id) REFERENCES factories(id),
  FOREIGN KEY(product_line_id) REFERENCES product_lines(id)
);

CREATE TABLE IF NOT EXISTS baseline_evaluations (
  id TEXT PRIMARY KEY,
  dataset_id TEXT NOT NULL,
  base_model TEXT,
  accuracy REAL,
  precision_score REAL,
  recall REAL,
  false_pass_rate REAL,
  false_alert_rate REAL,
  latency_ms INTEGER,
  summary_json TEXT,
  created_at TEXT,
  FOREIGN KEY(dataset_id) REFERENCES adaptation_datasets(id)
);

CREATE TABLE IF NOT EXISTS training_jobs (
  id TEXT PRIMARY KEY,
  dataset_id TEXT NOT NULL,
  base_model TEXT,
  training_method TEXT,
  status TEXT,
  epochs INTEGER,
  learning_rate REAL,
  output_model_version TEXT,
  metrics_json TEXT,
  created_at TEXT,
  completed_at TEXT,
  FOREIGN KEY(dataset_id) REFERENCES adaptation_datasets(id)
);

CREATE TABLE IF NOT EXISTS model_registry (
  id TEXT PRIMARY KEY,
  model_name TEXT,
  base_model TEXT,
  adapter_type TEXT,
  dataset_version TEXT,
  factory_id TEXT,
  product_line_id TEXT,
  validation_score REAL,
  deployment_status TEXT,
  is_active INTEGER,
  created_at TEXT,
  FOREIGN KEY(factory_id) REFERENCES factories(id),
  FOREIGN KEY(product_line_id) REFERENCES product_lines(id)
);

CREATE TABLE IF NOT EXISTS inference_routes (
  id TEXT PRIMARY KEY,
  factory_id TEXT NOT NULL,
  product_line_id TEXT NOT NULL,
  active_model_registry_id TEXT,
  fallback_model_name TEXT,
  status TEXT,
  updated_at TEXT,
  FOREIGN KEY(factory_id) REFERENCES factories(id),
  FOREIGN KEY(product_line_id) REFERENCES product_lines(id),
  FOREIGN KEY(active_model_registry_id) REFERENCES model_registry(id)
);

CREATE TABLE IF NOT EXISTS operator_feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  factory_id TEXT,
  product_line_id TEXT,
  image_ref TEXT,
  predicted_verdict TEXT,
  corrected_verdict TEXT,
  predicted_defect_type TEXT,
  corrected_defect_type TEXT,
  notes TEXT,
  status TEXT,
  created_at TEXT
);
"""


DEEPPCB_CLASSES = [
    "open circuit",
    "short",
    "mousebite",
    "spur",
    "pin hole",
    "missing copper",
]

NANO_DEFECTS_CLASSES = [
    "small_dent",
    "impact_pit",
    "broad_shallow_dent",
    "reflection_deformation",
    "creased_dent",
    "scratch_scuff",
    "coating_damage",
    "internal_dent",
    "base_region_defect",
    "shoulder_deformation",
    "rim_thread_defect",
    "unknown_defect",
    "clean",
]

MODEL_OPTIONS = [
    {
        "id": "base_visionguard",
        "label": "Base VisionGuard Model",
        "description": "Global zero-shot Qwen-VL route for generic product inspection.",
        "status": "active",
        "registry_id": "visionguard_zero_shot_base",
    },
    {
        "id": "factory_finetuned",
        "label": "Factory Fine-Tuned Model",
        "description": "Use the active model route configured for the selected factory line.",
        "status": "route_active",
        "registry_id": "pcb_adapter_v1",
    },
    {
        "id": "pcb_adapter_v1",
        "label": "PCB Adapter v1",
        "description": "DeepPCB LoRA adapter for the PCB demo line.",
        "status": "deployed",
        "registry_id": "pcb_adapter_v1",
    },
    {
        "id": "nano_defects_eval",
        "label": "NanoDefects Bottle QA — Evaluation Route",
        "description": "Raw steel-bottle QA evaluation route. Tuned policy reduces false PASS risk; adapter training pending more raw clean/defect data.",
        "status": "baseline_evaluated",
        "registry_id": "nano_defects_eval_route",
    },
]

ADAPTATION_STAGES = [
    {"name": "Queued", "status": "complete"},
    {"name": "Dataset validation", "status": "complete"},
    {"name": "Baseline evaluation", "status": "complete"},
    {"name": "Adapter training", "status": "complete"},
    {"name": "Validation", "status": "complete"},
    {"name": "Model registry", "status": "complete"},
    {"name": "Deployment", "status": "complete"},
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dict_row(cursor: sqlite3.Cursor, row: sqlite3.Row | tuple | None) -> dict | None:
    if row is None:
        return None
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))


def _rows(cursor: sqlite3.Cursor) -> list[dict]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _ensure_incremental_seed(conn: sqlite3.Connection) -> None:
    created_at = _now()
    conn.execute(
        "INSERT OR IGNORE INTO factories (id, name, industry, location, created_at) VALUES (?, ?, ?, ?, ?)",
        (
            "nanodefects_factory",
            "NanoDefects Bottle Manufacturing Line",
            "Steel Bottle Manufacturing",
            "Factory QA pilot",
            created_at,
        ),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO product_lines (id, factory_id, name, product_type, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "nano_bottle_line",
            "nanodefects_factory",
            "NanoDefects Steel Bottle Line",
            "steel_bottle",
            "Thermos, food jar, and brushed steel bottle QA for dents, coating damage, and base defects.",
            created_at,
        ),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO adaptation_datasets (
          id, factory_id, product_line_id, name, source, version, status,
          sample_count, train_count, validation_count, resolution, format,
          defect_classes_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "nano_defects_v1",
            "nanodefects_factory",
            "nano_bottle_line",
            "NanoDefects",
            "Raw factory QA images from NanoDefects steel bottle manufacturing line; annotated references excluded from evaluation input",
            "NanoDefects v1",
            "baseline_evaluated",
            26,
            18,
            4,
            "Raw WhatsApp factory camera frames",
            "JPEG",
            json.dumps(NANO_DEFECTS_CLASSES),
            created_at,
        ),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO baseline_evaluations (
          id, dataset_id, base_model, accuracy, precision_score, recall,
          false_pass_rate, false_alert_rate, latency_ms, summary_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "nano_defects_baseline_eval",
            "nano_defects_v1",
            "VisionGuard NanoDefects raw local baseline / Qwen-VL pending",
            0.4615,
            0.72,
            0.35,
            0.65,
            0.17,
            None,
            json.dumps(
                {
                    "weaknesses": [
                        "Raw pilot evaluation subset has 26 images and needs more raw clean/PASS examples.",
                        "Reflection-based dents are hard for generic zero-shot inspection without controlled lighting.",
                        "False PASS risk remains the key metric before adapter training.",
                    ],
                    "adaptation_need": "NanoDefects is ready for raw-image baseline tracking and adapter experiment planning, not production deployment.",
                }
            ),
            created_at,
        ),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO training_jobs (
          id, dataset_id, base_model, training_method, status, epochs,
          learning_rate, output_model_version, metrics_json, created_at, completed_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "nano_adapter_job_pending",
            "nano_defects_v1",
            "Qwen/Qwen2.5-VL-7B-Instruct",
            "LoRA adapter readiness check",
            "prototype_training_pending",
            0,
            None,
            "NanoDefects Bottle QA Prototype",
            json.dumps(
                {
                    "recommendation": "Collect 300-500 labeled images with more clean/PASS examples before production training.",
                    "current_stage": "baseline evaluated",
                }
            ),
            created_at,
            None,
        ),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO model_registry (
          id, model_name, base_model, adapter_type, dataset_version,
          factory_id, product_line_id, validation_score, deployment_status,
          is_active, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "nano_defects_eval_route",
            "NanoDefects Bottle QA — Evaluation Route",
            "Qwen/Qwen2.5-VL-7B-Instruct",
            "Evaluation Route",
            "NanoDefects v1",
            "nanodefects_factory",
            "nano_bottle_line",
            0.50,
            "baseline_evaluated",
            0,
            created_at,
        ),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO inference_routes (
          id, factory_id, product_line_id, active_model_registry_id,
          fallback_model_name, status, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "route_nano_bottle_line",
            "nanodefects_factory",
            "nano_bottle_line",
            "nano_defects_eval_route",
            "VisionGuard Zero-Shot Base",
            "evaluation_ready",
            created_at,
        ),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO model_registry (
          id, model_name, base_model, adapter_type, dataset_version,
          factory_id, product_line_id, validation_score, deployment_status,
          is_active, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "factory_custom_adapter",
            "Factory Custom Adapter",
            "Qwen/Qwen2.5-VL-7B-Instruct",
            "LoRA Adapter",
            "Customer dataset draft",
            "customer_factory",
            "custom_line",
            None,
            "training",
            0,
            created_at,
        ),
    )


def ensure_adaptation_seed() -> None:
    conn = get_conn()
    try:
        conn.executescript(ADAPTATION_SCHEMA)
        existing = conn.execute("SELECT COUNT(*) FROM factories WHERE id = ?", ("pcb_demo_plant",)).fetchone()[0]
        if existing:
            _ensure_incremental_seed(conn)
            conn.commit()
            return

        created_at = _now()
        conn.execute(
            "INSERT INTO factories (id, name, industry, location, created_at) VALUES (?, ?, ?, ?, ?)",
            ("pcb_demo_plant", "Precision Circuits Demo Plant", "Electronics Manufacturing", "Demo facility", created_at),
        )
        conn.execute(
            """
            INSERT INTO product_lines (id, factory_id, name, product_type, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "pcb_line_a",
                "pcb_demo_plant",
                "PCB Assembly Line A",
                "pcb_board",
                "Printed circuit board inspection line for open/short/copper pattern defects.",
                created_at,
            ),
        )
        conn.execute(
            """
            INSERT INTO adaptation_datasets (
              id, factory_id, product_line_id, name, source, version, status,
              sample_count, train_count, validation_count, resolution, format,
              defect_classes_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "deeppcb_v1",
                "pcb_demo_plant",
                "pcb_line_a",
                "DeepPCB",
                "Open-source real-world PCB defect inspection dataset",
                "DeepPCB v1",
                "ingested",
                1500,
                1200,
                300,
                "640x640 aligned template/test image pairs",
                "JPG + bounding-box annotations",
                json.dumps(DEEPPCB_CLASSES),
                created_at,
            ),
        )
        conn.execute(
            """
            INSERT INTO baseline_evaluations (
              id, dataset_id, base_model, accuracy, precision_score, recall,
              false_pass_rate, false_alert_rate, latency_ms, summary_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "deeppcb_zero_shot_eval",
                "deeppcb_v1",
                "VisionGuard Zero-Shot Base / Qwen-VL",
                0.82,
                0.79,
                0.76,
                0.14,
                0.08,
                318,
                json.dumps(
                    {
                        "weaknesses": [
                            "Fine copper breaks can be missed without PCB-specific defect vocabulary.",
                            "Small pin holes and spurs need tighter production-line tolerance than generic visual QA.",
                            "False alerts occur on normal traces when the baseline model lacks factory context.",
                        ],
                        "adaptation_need": "PCB line A benefits from a factory-specific adapter tuned to the six DeepPCB defect classes.",
                    }
                ),
                created_at,
            ),
        )
        conn.execute(
            """
            INSERT INTO training_jobs (
              id, dataset_id, base_model, training_method, status, epochs,
              learning_rate, output_model_version, metrics_json, created_at, completed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "pcb_lora_job_001",
                "deeppcb_v1",
                "Qwen/Qwen2.5-VL-7B-Instruct",
                "LoRA adapter fine-tuning",
                "completed",
                6,
                0.0002,
                "PCB Adapter v1",
                json.dumps(
                    {
                        "validation_accuracy": 0.93,
                        "defect_recall": 0.91,
                        "false_pass_rate": 0.04,
                        "false_alert_rate": 0.05,
                        "training_runtime": "AMD MI300X adapter job lifecycle",
                    }
                ),
                created_at,
                created_at,
            ),
        )
        registry_rows = [
            (
                "visionguard_zero_shot_base",
                "VisionGuard Zero-Shot Base",
                "Qwen/Qwen2.5-VL-7B-Instruct",
                "None",
                "-",
                "global",
                "generic_visual_qa",
                0.82,
                "active",
                1,
            ),
            (
                "pcb_adapter_v1",
                "PCB Adapter v1",
                "Qwen/Qwen2.5-VL-7B-Instruct",
                "LoRA Adapter",
                "DeepPCB v1",
                "pcb_demo_plant",
                "pcb_line_a",
                0.93,
                "deployed",
                1,
            ),
            (
                "bottle_line_adapter_future",
                "Bottle Line Adapter vFuture",
                "Qwen/Qwen2.5-VL-7B-Instruct",
                "LoRA Adapter",
                "MVTec Bottle",
                "future_demo",
                "bottle_line",
                None,
                "planned",
                0,
            ),
            (
                "factory_custom_adapter",
                "Factory Custom Adapter",
                "Qwen/Qwen2.5-VL-7B-Instruct",
                "LoRA Adapter",
                "Customer dataset draft",
                "customer_factory",
                "custom_line",
                None,
                "training",
                0,
            ),
        ]
        conn.executemany(
            """
            INSERT INTO model_registry (
              id, model_name, base_model, adapter_type, dataset_version,
              factory_id, product_line_id, validation_score, deployment_status,
              is_active, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [(*row, created_at) for row in registry_rows],
        )
        conn.execute(
            """
            INSERT INTO inference_routes (
              id, factory_id, product_line_id, active_model_registry_id,
              fallback_model_name, status, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "route_pcb_line_a",
                "pcb_demo_plant",
                "pcb_line_a",
                "pcb_adapter_v1",
                "VisionGuard Zero-Shot Base",
                "deployed",
                created_at,
            ),
        )
        feedback_rows = [
            ("pcb_demo_plant", "pcb_line_a", "deeppcb/sample_0412.jpg", "PASS", "ALERT_OPERATOR", "none", "pin hole", "Operator corrected missed pin hole.", "queued"),
            ("pcb_demo_plant", "pcb_line_a", "deeppcb/sample_0771.jpg", "ALERT_OPERATOR", "PASS", "spur", "none", "Normal trace bend marked as acceptable.", "reviewed"),
            ("pcb_demo_plant", "pcb_line_a", "deeppcb/sample_0888.jpg", "ALERT_OPERATOR", "STOP_LINE", "open circuit", "open circuit", "Escalated open circuit severity for production hold.", "included_next_training"),
        ]
        conn.executemany(
            """
            INSERT INTO operator_feedback (
              factory_id, product_line_id, image_ref, predicted_verdict,
              corrected_verdict, predicted_defect_type, corrected_defect_type,
              notes, status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [(*row, created_at) for row in feedback_rows],
        )
        conn.commit()
        _ensure_incremental_seed(conn)
        conn.commit()
    finally:
        conn.close()


def get_adaptation_overview() -> dict:
    ensure_adaptation_seed()
    factory = get_factory_profile()
    datasets = get_datasets()
    dataset = next((item for item in datasets if item["id"] == "deeppcb_v1"), datasets[0])
    baseline = get_baseline_evaluation()
    route = get_inference_routing()
    feedback = get_feedback_summary()
    return {
        "title": "Factory Adaptation Studio",
        "subtitle": "Adapt VisionGuard to specific factories, products, and defect taxonomies without replacing the core inspection engine.",
        "use_case": "DeepPCB factory-specific PCB inspection adapter",
        "status_badges": ["Dataset: DeepPCB", "Factory: PCB Demo Line", "Method: LoRA Adapter", "Status: Deployed"],
        "model_options": get_model_options(),
        "adaptation_stages": ADAPTATION_STAGES,
        "factory": factory,
        "dataset": dataset,
        "baseline": baseline,
        "routing": route,
        "feedback": feedback,
        "kpis": {
            "baseline_accuracy": baseline["metrics"]["accuracy"],
            "adapted_validation_score": route["active_model"]["validation_score"],
            "false_pass_reduction": "14% → 4%",
            "defect_classes": len(dataset["defect_classes"]),
        },
    }


def get_model_options() -> list[dict]:
    return MODEL_OPTIONS


def resolve_model_route(model_route: str | None) -> dict:
    ensure_adaptation_seed()
    route_id = model_route or "base_visionguard"
    option = next((item for item in MODEL_OPTIONS if item["id"] == route_id), MODEL_OPTIONS[0])
    if option["id"] in {"factory_finetuned", "pcb_adapter_v1"}:
        active_route = get_inference_routing()
        return {
            "selected_model_route": option["id"],
            "model_route_label": option["label"],
            "active_model": active_route["active_model"]["name"],
            "adapter_type": active_route["active_model"]["adapter_type"],
            "factory_id": active_route["factory_id"],
            "product_line_id": active_route["product_line_id"],
            "fallback_model": active_route["fallback_model_name"],
            "routing_status": active_route["status"],
        }
    if option["id"] == "nano_defects_eval":
        return {
            "selected_model_route": option["id"],
            "model_route_label": option["label"],
            "active_model": "NanoDefects Bottle QA — Evaluation Route",
            "adapter_type": "Evaluation Route",
            "factory_id": "nanodefects_factory",
            "product_line_id": "nano_bottle_line",
            "fallback_model": "VisionGuard Zero-Shot Base",
            "routing_status": "baseline_evaluated",
            "dataset": "NanoDefects v1",
            "adapter_training_status": "prototype_training_pending",
        }
    return {
        "selected_model_route": option["id"],
        "model_route_label": option["label"],
        "active_model": "VisionGuard Zero-Shot Base",
        "adapter_type": "None",
        "factory_id": "global",
        "product_line_id": "generic_visual_qa",
        "fallback_model": None,
        "routing_status": "active",
    }


def analyze_dataset(payload: dict) -> dict:
    ensure_adaptation_seed()
    defect_classes_raw = payload.get("defect_classes") or ",".join(DEEPPCB_CLASSES)
    defect_classes = [item.strip() for item in str(defect_classes_raw).replace("\n", ",").split(",") if item.strip()]
    product_type = payload.get("product_type") or "PCB / electronics"
    dataset_url = payload.get("dataset_url") or "DeepPCB demo dataset"
    has_existing_model = bool(payload.get("existing_model_link"))
    class_count = max(len(defect_classes), 1)
    selected_creation = str(payload.get("selected_creation_type") or "").lower()
    nano_context = (
        "nano" in selected_creation
        or "nanodefect" in dataset_url.lower()
        or "steel bottle" in product_type.lower()
        or "thermos" in product_type.lower()
    )
    sample_count = (
        50
        if nano_context
        else 1500 if "deeppcb" in dataset_url.lower() or "pcb" in product_type.lower() else max(420, class_count * 140)
    )
    missing_data = "None blocking" if sample_count >= 800 else "Add more defect examples before full adapter training"
    if nano_context:
        missing_data = "Need more clean/PASS examples before reliable PASS/FAIL adapter training"
        recommended_method = "Baseline evaluation + adapter readiness; LoRA prototype pending"
        expected_uplift = "prototype estimate after more labels"
        risk_level = "Medium"
    else:
        recommended_method = "LoRA adapter fine-tuning" if sample_count >= 800 else "Threshold tuning + targeted data collection"
        expected_uplift = "8-13 accuracy points" if recommended_method.startswith("LoRA") else "3-6 accuracy points"
        risk_level = "Low" if sample_count >= 1000 and class_count >= 4 else "Medium"
    required_images = 0 if sample_count >= 1000 else max(0, 800 - sample_count)

    return {
        "input_summary": {
            "factory_name": payload.get("factory_name") or "Precision Circuits Demo Plant",
            "line_id": payload.get("line_id") or "PCB-A1",
            "product_type": product_type,
            "dataset_url": dataset_url,
            "existing_model_link": payload.get("existing_model_link") or None,
            "camera_conditions": payload.get("camera_conditions") or "Fixed overhead camera, controlled lighting",
            "severity_rules": payload.get("severity_rules") or "Crack, broken trace, short, and missing material escalate to STOP_LINE.",
            "uses_existing_model": has_existing_model,
        },
        "readiness": {
            "dataset_readiness": "Strong / ready for adaptation" if sample_count >= 1000 else "Partial / collect more examples",
            "sample_count": sample_count,
            "good_defect_ratio": "Clean examples underrepresented; collect more PASS images" if nano_context else "Usable: 42% good / 58% defective",
            "label_quality": "Real factory pilot labels; review recommended before training" if nano_context else "Strong for DeepPCB; medium for customer-uploaded draft until reviewed",
            "defect_class_coverage": f"{class_count} classes covered",
            "class_imbalance": "High: pilot set is defect-heavy" if nano_context else "Moderate: mousebite and spur underrepresented",
            "missing_data": "Low" if sample_count >= 1000 else missing_data,
            "recommended_adaptation_path": recommended_method,
        },
        "estimate": {
            "recommended_method": recommended_method,
            "estimated_training_time": "Not recommended yet; collect more clean/PASS images" if nano_context else "38-55 minutes on AMD MI300X" if sample_count >= 800 else "12-20 minutes for threshold calibration",
            "estimated_gpu_cost": "No GPU training spend recommended yet" if nano_context else "$1.30-$1.85 at current demo GPU pricing" if sample_count >= 800 else "$0.40-$0.70",
            "expected_accuracy_uplift": expected_uplift,
            "risk_level": risk_level,
            "required_additional_images": required_images,
        },
        "training_stages": ADAPTATION_STAGES,
    }


def get_factory_profile() -> dict:
    ensure_adaptation_seed()
    conn = get_conn()
    try:
        cursor = conn.execute(
            """
            SELECT f.*, p.id AS product_line_id, p.name AS product_line_name,
                   p.product_type, p.description
            FROM factories f
            JOIN product_lines p ON p.factory_id = f.id
            WHERE f.id = ?
            """,
            ("pcb_demo_plant",),
        )
        row = _dict_row(cursor, cursor.fetchone())
    finally:
        conn.close()
    return {
        "id": row["id"],
        "name": row["name"],
        "industry": row["industry"],
        "location": row["location"],
        "product_line": row["product_line_name"],
        "product_line_id": row["product_line_id"],
        "product_type": row["product_type"],
        "target_defects": DEEPPCB_CLASSES,
        "inspection_mode": "Factory-specific visual QA routing",
        "current_deployment": "PCB Adapter v1",
    }


def get_datasets() -> list[dict]:
    ensure_adaptation_seed()
    conn = get_conn()
    try:
        cursor = conn.execute("SELECT * FROM adaptation_datasets ORDER BY created_at DESC")
        datasets = _rows(cursor)
    finally:
        conn.close()
    for dataset in datasets:
        dataset["defect_classes"] = json.loads(dataset.pop("defect_classes_json") or "[]")
    return datasets


def get_baseline_evaluation() -> dict:
    ensure_adaptation_seed()
    conn = get_conn()
    try:
        cursor = conn.execute("SELECT * FROM baseline_evaluations WHERE id = ?", ("deeppcb_zero_shot_eval",))
        row = _dict_row(cursor, cursor.fetchone())
    finally:
        conn.close()
    summary = json.loads(row.pop("summary_json") or "{}")
    return {
        "id": row["id"],
        "dataset_id": row["dataset_id"],
        "base_model": row["base_model"],
        "metrics": {
            "accuracy": row["accuracy"],
            "precision": row["precision_score"],
            "recall": row["recall"],
            "false_pass_rate": row["false_pass_rate"],
            "false_alert_rate": row["false_alert_rate"],
            "latency_ms": row["latency_ms"],
        },
        "weaknesses": summary.get("weaknesses", []),
        "adaptation_need": summary.get("adaptation_need", ""),
        "created_at": row["created_at"],
    }


def get_training_jobs() -> list[dict]:
    ensure_adaptation_seed()
    conn = get_conn()
    try:
        cursor = conn.execute("SELECT * FROM training_jobs ORDER BY created_at DESC")
        rows = _rows(cursor)
    finally:
        conn.close()
    for row in rows:
        row["metrics"] = json.loads(row.pop("metrics_json") or "{}")
    return rows


def get_model_registry() -> list[dict]:
    ensure_adaptation_seed()
    conn = get_conn()
    try:
        cursor = conn.execute("SELECT * FROM model_registry ORDER BY is_active DESC, created_at DESC")
        rows = _rows(cursor)
    finally:
        conn.close()
    for row in rows:
        row["is_active"] = bool(row["is_active"])
    return rows


def get_inference_routing() -> dict:
    ensure_adaptation_seed()
    conn = get_conn()
    try:
        cursor = conn.execute(
            """
            SELECT r.*, m.model_name, m.base_model, m.adapter_type, m.dataset_version,
                   m.validation_score, m.deployment_status
            FROM inference_routes r
            JOIN model_registry m ON m.id = r.active_model_registry_id
            WHERE r.id = ?
            """,
            ("route_pcb_line_a",),
        )
        row = _dict_row(cursor, cursor.fetchone())
    finally:
        conn.close()
    return {
        "factory_id": row["factory_id"],
        "product_line_id": row["product_line_id"],
        "product_type": "pcb_board",
        "route": "factory_adapter",
        "active_model": {
            "id": row["active_model_registry_id"],
            "name": row["model_name"],
            "base_model": row["base_model"],
            "adapter_type": row["adapter_type"],
            "dataset_version": row["dataset_version"],
            "validation_score": row["validation_score"],
            "deployment_status": row["deployment_status"],
        },
        "fallback_model_name": row["fallback_model_name"],
        "runtime": "AMD MI300X · ROCm · vLLM",
        "status": row["status"],
        "updated_at": row["updated_at"],
    }


def get_feedback_summary() -> dict:
    ensure_adaptation_seed()
    conn = get_conn()
    try:
        cursor = conn.execute("SELECT * FROM operator_feedback ORDER BY id DESC LIMIT 20")
        rows = _rows(cursor)
        counts = conn.execute(
            """
            SELECT
              COUNT(*) AS total,
              SUM(CASE WHEN status = 'queued' THEN 1 ELSE 0 END) AS queued,
              SUM(CASE WHEN status = 'included_next_training' THEN 1 ELSE 0 END) AS included
            FROM operator_feedback
            """
        ).fetchone()
    finally:
        conn.close()
    return {
        "total": int(counts[0] or 0),
        "queued": int(counts[1] or 0),
        "included_next_training": int(counts[2] or 0),
        "items": rows,
    }


def add_operator_feedback(payload: dict) -> dict:
    ensure_adaptation_seed()
    conn = get_conn()
    try:
        created_at = _now()
        cursor = conn.execute(
            """
            INSERT INTO operator_feedback (
              factory_id, product_line_id, image_ref, predicted_verdict,
              corrected_verdict, predicted_defect_type, corrected_defect_type,
              notes, status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.get("factory_id", "pcb_demo_plant"),
                payload.get("product_line_id", "pcb_line_a"),
                payload.get("image_ref", "operator_upload"),
                payload.get("predicted_verdict", "ALERT_OPERATOR"),
                payload.get("corrected_verdict", "ALERT_OPERATOR"),
                payload.get("predicted_defect_type", "unknown"),
                payload.get("corrected_defect_type", "unknown"),
                payload.get("notes", ""),
                payload.get("status", "queued"),
                created_at,
            ),
        )
        conn.commit()
        feedback_id = cursor.lastrowid
    finally:
        conn.close()
    return {"id": feedback_id, "status": "queued", "created_at": created_at}


def create_training_job() -> dict:
    ensure_adaptation_seed()
    conn = get_conn()
    try:
        version = f"PCB Adapter v{len(get_training_jobs()) + 1}"
        job_id = f"pcb_lora_job_{int(datetime.now(timezone.utc).timestamp())}"
        created_at = _now()
        conn.execute(
            """
            INSERT INTO training_jobs (
              id, dataset_id, base_model, training_method, status, epochs,
              learning_rate, output_model_version, metrics_json, created_at, completed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                "deeppcb_v1",
                "Qwen/Qwen2.5-VL-7B-Instruct",
                "LoRA adapter fine-tuning",
                "queued",
                6,
                0.0002,
                version,
                json.dumps({"note": "Queued for next AMD MI300X adapter training window."}),
                created_at,
                None,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return {"id": job_id, "status": "queued", "output_model_version": version}


def deploy_model(model_id: str) -> dict:
    ensure_adaptation_seed()
    conn = get_conn()
    try:
        model = conn.execute("SELECT id, model_name FROM model_registry WHERE id = ?", (model_id,)).fetchone()
        if not model:
            raise ValueError(f"Unknown model_registry id: {model_id}")
        route_id = "route_nano_bottle_line" if model_id == "nano_defects_eval_route" else "route_pcb_line_a"
        conn.execute(
            """
            UPDATE inference_routes
            SET active_model_registry_id = ?, status = 'deployed', updated_at = ?
            WHERE id = ?
            """,
            (model_id, _now(), route_id),
        )
        conn.execute(
            "UPDATE model_registry SET deployment_status = CASE WHEN id = ? THEN 'deployed' ELSE deployment_status END",
            (model_id,),
        )
        conn.commit()
    finally:
        conn.close()
    return {"model_id": model_id, "status": "deployed"}
