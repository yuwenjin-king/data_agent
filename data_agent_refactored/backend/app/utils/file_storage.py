import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

from app.core.config import settings

# Stream uploads in 1 MiB chunks so the size limit aborts early (DoS guard).
_READ_CHUNK = 1024 * 1024


def safe_ext(filename: Optional[str]) -> str:
    """Return a lowercased, sanitized extension (alphanumeric only), e.g. '.txt'."""
    if not filename:
        return ""
    ext = Path(filename).suffix
    return "".join(c for c in ext if c.isalnum() or c == ".")[:10].lower()


def read_with_size_limit(upload: UploadFile) -> bytes:
    """Read the upload in chunks, aborting if it exceeds MAX_UPLOAD_SIZE."""
    size = 0
    chunks: list[bytes] = []
    while True:
        chunk = upload.file.read(_READ_CHUNK)
        if not chunk:
            break
        size += len(chunk)
        if size > settings.MAX_UPLOAD_SIZE:
            raise ValueError(f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE} bytes")
        chunks.append(chunk)
    return b"".join(chunks)


def _is_within_base(base: Path, target: Path) -> bool:
    """True only if target is base itself or nested under it (robust traversal guard)."""
    try:
        target.relative_to(base)
        return True
    except ValueError:
        return False


def save_upload_file(
    upload: UploadFile,
    subdir: str,
    *,
    allowed_extensions: Optional[set[str]] = None,
) -> dict:
    """Save an UploadFile under settings.UPLOAD_DIR/subdir and return metadata.

    Validates the extension against an allowlist and enforces the size limit
    while streaming. The stored filename is a random UUID, so user-controlled
    names never reach the filesystem path.

    Returns a dict with keys: file_path, file_size, file_type, source_filename.
    """
    ext = safe_ext(upload.filename)
    allow = (
        allowed_extensions
        if allowed_extensions is not None
        else {e.lower() for e in settings.ALLOWED_UPLOAD_EXTENSIONS}
    )
    if allow and ext not in allow:
        raise ValueError(f"File type '{ext or '(none)'}' is not allowed. Allowed: {sorted(allow)}")

    content = read_with_size_limit(upload)

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
    # Refuse paths that escape the upload base directory.
    if not _is_within_base(base, target):
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
    if not _is_within_base(base, target):
        raise ValueError("Invalid file path")
    with open(target, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()
