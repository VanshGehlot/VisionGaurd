import importlib


def test_report_generation_with_sample_logs(tmp_path, monkeypatch):
    db_path = tmp_path / "reporter-test.db"
    monkeypatch.setenv("SQLITE_DB_PATH", str(db_path))

    import db.sqlite_client as sqlite_client
    import agents.reporter as reporter

    sqlite_client = importlib.reload(sqlite_client)
    reporter = importlib.reload(reporter)

    sqlite_client.insert_defect_log(
        {
            "image_id": "good_001",
            "product_type": "bottle",
            "defect_detected": False,
            "defect_type": "none",
            "defect_category": "none",
            "severity": "ok",
            "confidence": 0.98,
            "location": "none",
            "region": {"horizontal": "none", "vertical": "none"},
            "action": "PASS",
            "line_id": "LINE-A1",
            "shift": "morning",
            "processing_ms": 180,
            "model_name": "Qwen/Qwen2.5-VL-7B-Instruct",
            "visual_explanation": "No visible defect.",
            "possible_causes": [],
            "recommended_fix": [],
            "prevention": ["maintain current process controls"],
            "factory_owner_summary": "No defect detected.",
        }
    )
    sqlite_client.insert_defect_log(
        {
            "image_id": "bad_001",
            "product_type": "bottle",
            "defect_detected": True,
            "defect_type": "contamination",
            "defect_category": "contamination mark",
            "severity": "warning",
            "confidence": 0.88,
            "location": "multiple",
            "region": {"horizontal": "center", "vertical": "middle"},
            "action": "ALERT_OPERATOR",
            "line_id": "LINE-A1",
            "shift": "morning",
            "processing_ms": 240,
            "model_name": "Qwen/Qwen2.5-VL-7B-Instruct",
            "visual_explanation": "Foreign material visible.",
            "possible_causes": ["cleaning residue", "airborne contamination"],
            "recommended_fix": ["inspect nearby items"],
            "prevention": ["improve cleaning verification"],
            "factory_owner_summary": "Contamination summary.",
        }
    )

    report = reporter.reporter_agent()
    assert "VisionGuard inspected 2 product images this shift" in report
    assert '"contamination"' in report
    assert '"contamination mark"' in report
    assert '"warning"' in report
    assert "cleaning residue" in report
