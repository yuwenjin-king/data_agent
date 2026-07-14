"""Security tests for file uploads: extension allowlist, streaming size cap,
path-traversal containment, and excel import validation."""

import io

import pytest
from fastapi import UploadFile

from app.services.knowledge_service import semantic_model_crud
from app.utils.file_storage import delete_file, read_file_text, save_upload_file


def _upload(name: str, data: bytes) -> UploadFile:
    return UploadFile(filename=name, file=io.BytesIO(data))


def test_save_upload_rejects_disallowed_extension(tmp_path, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.UPLOAD_DIR", str(tmp_path))
    with pytest.raises(ValueError, match="not allowed"):
        save_upload_file(_upload("evil.exe", b"MZ"), "docs")


def test_save_upload_rejects_path_traversal_filename(tmp_path, monkeypatch):
    # Even a malicious filename is neutralized: stored name is a UUID.
    monkeypatch.setattr("app.core.config.settings.UPLOAD_DIR", str(tmp_path))
    meta = save_upload_file(_upload("../../etc/passwd.txt", b"x"), "docs")
    assert ".." not in meta["file_path"]
    assert meta["file_path"].endswith(".txt")


def test_save_upload_accepts_allowed_extension(tmp_path, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.UPLOAD_DIR", str(tmp_path))
    meta = save_upload_file(_upload("notes.md", b"# hi"), "docs")
    assert meta["file_size"] == 4
    assert meta["file_path"].endswith(".md")
    assert meta["source_filename"] == "notes.md"


def test_save_upload_streaming_size_cap_aborts_early(tmp_path, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr("app.core.config.settings.MAX_UPLOAD_SIZE", 10)
    with pytest.raises(ValueError, match="exceeds maximum size"):
        save_upload_file(_upload("big.txt", b"x" * 1024), "docs")


def test_delete_file_refuses_path_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))
    # Absolute escape and relative parent escape must both be refused.
    assert delete_file("/etc/passwd") is False
    assert delete_file("../secret") is False


def test_read_file_text_refuses_path_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))
    with pytest.raises(ValueError):
        read_file_text("../secret.txt")
    with pytest.raises(ValueError):
        read_file_text("/etc/passwd")


def test_delete_file_and_read_roundtrip_within_base(tmp_path, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))
    meta = save_upload_file(_upload("ok.txt", b"hello"), "docs")
    assert read_file_text(meta["file_path"]) == "hello"
    assert delete_file(meta["file_path"]) is True


def test_import_excel_rejects_non_xlsx(tmp_path, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.UPLOAD_DIR", str(tmp_path))
    with pytest.raises(ValueError, match="xlsx"):
        semantic_model_crud.import_excel(
            db=None, agent_id=1, upload_file=_upload("data.csv", b"a,b\n1,2")
        )
