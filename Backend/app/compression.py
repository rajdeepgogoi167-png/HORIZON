import gzip
import io
from pathlib import Path

from PIL import Image

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}


def compress_bytes(data: bytes, mime_type: str, quality: int = 40) -> tuple[bytes, str, str]:
    """Return compressed payload, stored extension hint, and encoding used."""
    if mime_type.lower() in IMAGE_TYPES or mime_type.lower().startswith("image/"):
        try:
            image = Image.open(io.BytesIO(data))
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            width, height = image.size
            max_side = 640 if max(width, height) > 640 else max(width, height)
            if max(width, height) > max_side:
                image.thumbnail((max_side, max_side))
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=quality, optimize=True)
            return buffer.getvalue(), ".jpg", "jpeg"
        except Exception:
            pass

    return gzip.compress(data, compresslevel=9), ".gz", "gzip"


def save_compressed(data: bytes, original_name: str, mime_type: str, quality: int) -> tuple[Path, int]:
    compressed, suffix, _encoding = compress_bytes(data, mime_type, quality)
    safe_name = Path(original_name).stem.replace(" ", "_")
    path = UPLOAD_DIR / f"{safe_name}{suffix}"
    index = 1
    while path.exists():
        path = UPLOAD_DIR / f"{safe_name}_{index}{suffix}"
        index += 1
    path.write_bytes(compressed)
    return path, len(compressed)


def jpeg_quality_for_bandwidth(bandwidth_kbps: float) -> int:
    if bandwidth_kbps < 48:
        return 25
    if bandwidth_kbps < 120:
        return 35
    if bandwidth_kbps < 250:
        return 45
    return 60
