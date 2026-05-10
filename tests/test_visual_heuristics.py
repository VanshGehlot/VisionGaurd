from pathlib import Path

from PIL import Image, ImageDraw

from utils.visual_heuristics import detect_dark_speckles


def test_good_mvtec_bottle_does_not_trigger_speckle_review():
    image = Image.open(Path("examples") / "bottle_good_0.jpg")
    result = detect_dark_speckles(image)
    assert result.flagged is False


def test_obvious_dark_speckles_trigger_localized_bbox():
    image = Image.new("RGB", (420, 420), "white")
    draw = ImageDraw.Draw(image)
    for y in range(150, 270, 12):
        for x in range(150, 270, 12):
            draw.ellipse((x, y, x + 4, y + 4), fill=(12, 12, 12))

    result = detect_dark_speckles(image)

    assert result.flagged is True
    assert result.bbox is not None
    x1, y1, x2, y2 = result.bbox
    assert 120 <= x1 <= 180
    assert 120 <= y1 <= 180
    assert 240 <= x2 <= 300
    assert 240 <= y2 <= 300
