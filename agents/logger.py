import uuid

from config import get_settings
from db.sqlite_client import insert_defect_log


def logger_agent(
    scan_result: dict,
    product_type: str = "bottle",
    line_id: str | None = None,
    shift: str | None = None,
) -> dict:
    """
    Enrich a scan result with operational context and persist it locally.

    MindsDB can query the same SQLite database for analytics and reporting.
    """
    event = {
        **scan_result,
        "image_id": f"{product_type}_{uuid.uuid4().hex[:10]}",
        "product_type": product_type,
        "line_id": line_id or get_settings().default_line_id,
        "shift": shift or get_settings().default_shift,
    }

    insert_defect_log(event)
    return event
