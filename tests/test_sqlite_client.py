import importlib


def test_sqlite_insert_and_fetch(tmp_path, monkeypatch):
    db_path = tmp_path / "visionguard-test.db"
    monkeypatch.setenv("SQLITE_DB_PATH", str(db_path))

    import db.sqlite_client as sqlite_client

    sqlite_client = importlib.reload(sqlite_client)

    sqlite_client.insert_defect_log(
        {
            "image_id": "test_001",
            "product_type": "bottle",
            "defect_detected": True,
            "defect_type": "crack",
            "defect_category": "structural crack",
            "severity": "critical",
            "confidence": 0.94,
            "location": "upper-left bottle neck",
            "region": {"horizontal": "left", "vertical": "upper"},
            "action": "STOP_LINE",
            "line_id": "LINE-T1",
            "shift": "night",
            "processing_ms": 220,
            "model_name": "Qwen/Qwen2.5-VL-7B-Instruct",
            "visual_explanation": "Visible crack.",
            "possible_causes": ["thermal stress"],
            "recommended_fix": ["remove item"],
            "prevention": ["calibrate cooling"],
            "factory_owner_summary": "Critical crack summary.",
        }
    )

    columns, rows = sqlite_client.get_logs(limit=5)
    assert "image_id" in columns
    assert "defect_category" in columns
    assert "region_horizontal" in columns
    assert len(rows) == 1
    assert rows[0][2] == "test_001"
