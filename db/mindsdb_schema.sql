CREATE DATABASE visionguard_db
WITH
  engine = 'sqlite',
  parameters = {
    "db_file": "/tmp/visionguard.db"
  };

CREATE TABLE visionguard_db.defect_logs (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP,
  image_id        VARCHAR(128),
  product_type    VARCHAR(64),
  defect_detected BOOLEAN,
  defect_type     VARCHAR(64),
  defect_category VARCHAR(64),
  severity        VARCHAR(32),
  confidence      FLOAT,
  location        VARCHAR(32),
  region_horizontal VARCHAR(32),
  region_vertical   VARCHAR(32),
  action_taken    VARCHAR(64),
  line_id         VARCHAR(32),
  shift           VARCHAR(16),
  processing_ms   INTEGER,
  model_name      VARCHAR(128),
  visual_explanation TEXT,
  possible_causes    TEXT,
  recommended_fix    TEXT,
  prevention         TEXT,
  factory_owner_summary TEXT
);

CREATE VIEW visionguard_db.shift_summary AS
SELECT
  shift,
  line_id,
  COUNT(*) AS total_inspected,
  SUM(CASE WHEN defect_detected THEN 1 ELSE 0 END) AS defects_found,
  AVG(confidence) AS avg_confidence,
  AVG(processing_ms) AS avg_latency_ms,
  MAX(timestamp) AS last_updated
FROM visionguard_db.defect_logs
GROUP BY shift, line_id;

CREATE VIEW visionguard_db.defect_spike_summary AS
SELECT
  line_id,
  shift,
  defect_type,
  severity,
  COUNT(*) AS defect_count,
  AVG(confidence) AS avg_confidence,
  AVG(processing_ms) AS avg_latency_ms,
  MAX(timestamp) AS last_seen
FROM visionguard_db.defect_logs
WHERE defect_detected = true
GROUP BY line_id, shift, defect_type, severity;
