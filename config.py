import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    vllm_url: str
    model_name: str
    mindsdb_url: str
    sqlite_db_path: str
    default_line_id: str
    default_shift: str
    visionguard_host: str
    visionguard_port: int
    demo_mode: bool


def get_settings() -> Settings:
    return Settings(
        vllm_url=os.getenv("VLLM_URL", "http://localhost:8000/v1/chat/completions"),
        model_name=os.getenv("MODEL_NAME", "Qwen/Qwen2.5-VL-7B-Instruct"),
        mindsdb_url=os.getenv("MINDSDB_URL", "http://127.0.0.1:47334"),
        sqlite_db_path=os.getenv("SQLITE_DB_PATH", "/tmp/visionguard.db"),
        default_line_id=os.getenv("DEFAULT_LINE_ID", "LINE-A1"),
        default_shift=os.getenv("DEFAULT_SHIFT", "morning"),
        visionguard_host=os.getenv("VISIONGUARD_HOST", "0.0.0.0"),
        visionguard_port=int(os.getenv("VISIONGUARD_PORT", "7860")),
        demo_mode=_as_bool(os.getenv("DEMO_MODE"), default=False),
    )

settings = get_settings()
