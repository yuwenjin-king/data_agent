import re
from typing import List


def chunk_text(
    text: str, splitter_type: str = "token", chunk_size: int = 500, overlap: int = 0
) -> List[str]:
    """Split text into chunks. This is a stub implementation for P2.

    - ``token``: split on whitespace, then group roughly ``chunk_size`` tokens.
    - ``character``: split by raw character count.
    """
    if not text:
        return []

    if splitter_type == "character":
        step = max(chunk_size - overlap, 1)
        return [text[i : i + chunk_size] for i in range(0, len(text), step)]

    # Default token splitter
    tokens = re.split(r"(\s+)", text)
    # tokens now alternates between words and whitespace; keep chunks of ~chunk_size words
    chunks = []
    current = []
    current_len = 0
    for token in tokens:
        if token.strip():
            current_len += 1
        current.append(token)
        if current_len >= chunk_size:
            chunks.append("".join(current).strip())
            current = []
            current_len = 0
    if current:
        chunks.append("".join(current).strip())
    return chunks or [text]
