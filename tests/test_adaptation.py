from agents import adaptation


def test_adaptation_overview_seeded_from_deeppcb(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "adaptation.db"))

    overview = adaptation.get_adaptation_overview()

    assert overview["factory"]["id"] == "pcb_demo_plant"
    assert overview["dataset"]["name"] == "DeepPCB"
    assert overview["routing"]["active_model"]["name"] == "PCB Adapter v1"
    assert "open circuit" in overview["dataset"]["defect_classes"]


def test_model_registry_contains_deployed_pcb_adapter(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "adaptation.db"))

    models = adaptation.get_model_registry()
    deployed = [model for model in models if model["id"] == "pcb_adapter_v1"][0]

    assert deployed["adapter_type"] == "LoRA Adapter"
    assert deployed["deployment_status"] == "deployed"
    assert deployed["is_active"] is True


def test_adaptation_model_options_include_inspection_routes():
    options = adaptation.get_model_options()

    assert [option["id"] for option in options] == [
        "base_visionguard",
        "factory_finetuned",
        "pcb_adapter_v1",
        "nano_defects_eval",
    ]


def test_nanodefects_route_is_truthful_evaluation_route(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "adaptation.db"))

    models = adaptation.get_model_registry()
    nano_model = [model for model in models if model["id"] == "nano_defects_eval_route"][0]
    route = adaptation.resolve_model_route("nano_defects_eval")

    assert nano_model["adapter_type"] == "Evaluation Route"
    assert nano_model["deployment_status"] == "baseline_evaluated"
    assert nano_model["is_active"] is False
    assert route["routing_status"] == "baseline_evaluated"
    assert route["adapter_training_status"] == "prototype_training_pending"


def test_dataset_readiness_analysis_returns_estimate(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "adaptation.db"))

    report = adaptation.analyze_dataset(
        {
            "dataset_url": "https://github.com/tangsanli5201/DeepPCB",
            "product_type": "Printed circuit board",
            "defect_classes": "open circuit, short, mousebite, spur, pin hole, missing copper",
        }
    )

    assert report["readiness"]["sample_count"] >= 1000
    assert report["estimate"]["recommended_method"] == "LoRA adapter fine-tuning"
    assert report["estimate"]["risk_level"] == "Low"
    assert report["training_stages"][-1]["name"] == "Deployment"


def test_operator_feedback_is_persisted(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "adaptation.db"))

    created = adaptation.add_operator_feedback(
        {
            "image_ref": "deeppcb/regression_case.jpg",
            "predicted_verdict": "PASS",
            "corrected_verdict": "ALERT_OPERATOR",
            "predicted_defect_type": "none",
            "corrected_defect_type": "mousebite",
            "notes": "Missed PCB mousebite defect.",
        }
    )
    feedback = adaptation.get_feedback_summary()

    assert created["status"] == "queued"
    assert feedback["queued"] >= 1
    assert any(item["image_ref"] == "deeppcb/regression_case.jpg" for item in feedback["items"])
