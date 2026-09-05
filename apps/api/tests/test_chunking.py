from app.utils.chunking import chunk_text


def test_chunk_text_empty_returns_nothing() -> None:
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_chunk_text_short_text_is_single_chunk() -> None:
    assert chunk_text("Veneers last 10-15 years.", max_chars=800) == ["Veneers last 10-15 years."]


def test_chunk_text_groups_paragraphs_under_the_limit() -> None:
    text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
    chunks = chunk_text(text, max_chars=100)
    assert chunks == [text]


def test_chunk_text_splits_when_paragraphs_exceed_limit() -> None:
    para_a = "A" * 40
    para_b = "B" * 40
    text = f"{para_a}\n\n{para_b}"
    chunks = chunk_text(text, max_chars=50)
    assert chunks == [para_a, para_b]


def test_chunk_text_hard_splits_a_single_long_paragraph() -> None:
    long_para = "X" * 250
    chunks = chunk_text(long_para, max_chars=100, overlap=20)
    assert len(chunks) > 1
    assert all(len(c) <= 100 for c in chunks)
    # Overlap means consecutive hard-split chunks share a tail/head region.
    assert chunks[0][-20:] == chunks[1][:20]
