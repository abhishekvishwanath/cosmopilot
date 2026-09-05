DEFAULT_MAX_CHARS = 800
DEFAULT_OVERLAP = 100


def chunk_text(
    text: str, max_chars: int = DEFAULT_MAX_CHARS, overlap: int = DEFAULT_OVERLAP
) -> list[str]:
    """
    Splits text into chunks on paragraph boundaries where possible,
    falling back to a hard character split (with overlap) only for a
    single paragraph longer than max_chars. Tuned for short clinic-
    knowledge passages (FAQs, policy text), not long-document RAG —
    overlap between adjacent paragraph-grouped chunks isn't needed at
    this scale.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        candidate = f"{current}\n\n{para}".strip() if current else para
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
        if len(para) <= max_chars:
            current = para
        else:
            step = max_chars - overlap
            for i in range(0, len(para), step):
                chunks.append(para[i : i + max_chars])
            current = ""

    if current:
        chunks.append(current)
    return chunks
