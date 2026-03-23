"""
Watermark Module - Evidence Shield
Applies QC watermark with item code, timestamp, and GPS to inspection photos
"""
from pathlib import Path
from datetime import datetime


def apply_watermark(
    src_path: str,
    dest_path: str,
    item_code: str,
    timestamp: str,
    gps_text: str,
    opacity: float = 0.75,
) -> str:
    """
    Apply a professional watermark to an inspection photo.
    Falls back gracefully if Pillow is not installed.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        _apply_with_pillow(src_path, dest_path, item_code, timestamp, gps_text, opacity)
    except ImportError:
        # Fallback: just copy the image
        import shutil
        shutil.copy2(src_path, dest_path)
    return dest_path


def _apply_with_pillow(src_path, dest_path, item_code, timestamp, gps_text, opacity):
    from PIL import Image, ImageDraw, ImageFont
    import math

    img = Image.open(src_path).convert("RGBA")
    w, h = img.size

    # Create overlay
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)

    # Try to load a font, fall back to default
    font_large  = _get_font(20)
    font_medium = _get_font(15)
    font_small  = _get_font(12)

    # ── Dark banner at bottom ─────────────────────────────────────────
    banner_h = 90
    banner_y = h - banner_h
    draw.rectangle([0, banner_y, w, h], fill=(10, 15, 25, 200))

    # ── Neon blue top border on banner ──────────────────────────────
    draw.rectangle([0, banner_y, w, banner_y + 3], fill=(0, 212, 255, 255))

    # ── Text content ─────────────────────────────────────────────────
    padding = 14
    line_h  = 22

    # Company / App label
    draw.text((padding, banner_y + 8), "SWCC QC | مراقبة الجودة",
              font=font_small, fill=(0, 212, 255, 220))

    # Item code (large, prominent)
    draw.text((padding, banner_y + 26), f"⬡ {item_code}",
              font=font_large, fill=(255, 255, 255, 255))

    # Timestamp
    draw.text((padding, banner_y + 52), f"🕐 {timestamp}",
              font=font_medium, fill=(200, 210, 230, 220))

    # GPS
    draw.text((padding, banner_y + 70), f"📍 {gps_text}",
              font=font_small, fill=(160, 180, 200, 200))

    # ── Diagonal watermark text (center of image) ────────────────────
    wm_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    wm_draw  = ImageDraw.Draw(wm_layer)
    wm_font  = _get_font(max(14, w // 25))
    wm_text  = f"SWCC QC | {item_code}"
    bbox     = wm_draw.textbbox((0, 0), wm_text, font=wm_font)
    tw, th   = bbox[2] - bbox[0], bbox[3] - bbox[1]

    # Tiled diagonal watermark
    step_x = int(tw * 1.8)
    step_y = int(th * 3.5)
    for xi in range(-step_x, w + step_x, step_x):
        for yi in range(-step_y, h + step_y, step_y):
            wm_draw.text((xi, yi), wm_text, font=wm_font,
                         fill=(0, 212, 255, 28))

    # Rotate diagonal
    import math
    wm_rotated = wm_layer.rotate(25, expand=False)

    # Composite
    composited = Image.alpha_composite(img, overlay)
    composited = Image.alpha_composite(composited, wm_rotated)
    final      = composited.convert("RGB")
    final.save(dest_path, "JPEG", quality=92)


def _get_font(size: int):
    """Try to get a font; returns default if not available."""
    try:
        from PIL import ImageFont
        # Try common system fonts
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:/Windows/Fonts/calibrib.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]
        for path in candidates:
            if Path(path).exists():
                return ImageFont.truetype(path, size)
        return ImageFont.load_default()
    except Exception:
        from PIL import ImageFont
        return ImageFont.load_default()


def get_gps_location() -> tuple[float | None, float | None]:
    """
    Attempt to get GPS coordinates.
    On Android (via Flet), this requires permission.
    Returns (lat, lon) or (None, None).
    """
    try:
        import geocoder
        g = geocoder.ip("me")
        if g.ok:
            return g.latlng[0], g.latlng[1]
    except ImportError:
        pass
    return None, None


def format_gps(lat, lon) -> str:
    if lat and lon:
        return f"{lat:.5f}°N, {lon:.5f}°E"
    return "GPS: غير متاح"
