import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

from app.core.config import settings


def _safe_ext(filename: Optional[str]) -> str:
    if not filename:
        return ""
    ext = Path(filename).suffix
    # Keep only safe characters in extension
    return "".join(c for c in ext if c.isalnum() or c == ".")[:10]


def save_upload_file(upload: UploadFile, subdir: str) -> dict:
    """Save an UploadFile under settings.UPLOAD_DIR/subdir and return metadata.

    Returns a dict with keys: file_path, file_size, file_type, source_filename.
    """
    content = upload.file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise ValueError(f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE} bytes")

    ext = _safe_ext(upload.filename)
    filename = f"{uuid.uuid4().hex}{ext}"
    upload_dir = Path(settings.UPLOAD_DIR) / subdir
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / filename

    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "file_path": str(Path(subdir) / filename),
        "file_size": len(content),
        "file_type": upload.content_type or "application/octet-stream",
        "source_filename": upload.filename or filename,
    }


def delete_file(relative_path: Optional[str]) -> bool:
    """Delete a file relative to settings.UPLOAD_DIR. Returns True if removed or not found."""
    if not relative_path:
        return True
    base = Path(settings.UPLOAD_DIR).resolve()
    target = (base / relative_path).resolve()
    # Security: refuse to delete outside the upload base directory
    if not str(target).startswith(str(base)):
        return False
    if not target.exists():
        return True
    try:
        target.unlink()
        return True
    except OSError:
        return False


def read_file_text(relative_path: str) -> str:
    base = Path(settings.UPLOAD_DIR).resolve()
    target = (base / relative_path).resolve()
    if not str(target).startswith(str(base)):
        raise ValueError("Invalid file path")
    with open(target, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()
