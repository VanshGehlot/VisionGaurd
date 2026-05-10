from PIL import Image

from model.qwen_client import inspect_pil_image
from utils.pass_verifier import verify_pass_result


def scanner_agent(image: Image.Image, inspection_profile: str | None = None) -> dict:
    """
    Run multimodal inspection against a product image.

    The primary execution path is Qwen2.5-VL served through vLLM on AMD MI300X.
    """
    first_pass = inspect_pil_image(image, inspection_profile=inspection_profile)
    result = verify_pass_result(first_pass, image, inspection_profile=inspection_profile)
    result["inspection_profile"] = inspection_profile or "generic"
    return result
