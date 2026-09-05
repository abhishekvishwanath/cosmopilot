from app.services.knowledge import MIN_SIMILARITY, _join_sentences, has_sufficient_knowledge


def test_has_sufficient_knowledge_true_above_threshold() -> None:
    assert has_sufficient_knowledge(MIN_SIMILARITY + 0.1) is True


def test_has_sufficient_knowledge_true_at_exact_threshold() -> None:
    assert has_sufficient_knowledge(MIN_SIMILARITY) is True


def test_has_sufficient_knowledge_false_below_threshold() -> None:
    assert has_sufficient_knowledge(MIN_SIMILARITY - 0.01) is False


def test_has_sufficient_knowledge_false_when_no_results() -> None:
    assert has_sufficient_knowledge(None) is False


def test_join_sentences_does_not_double_periods() -> None:
    result = _join_sentences(["This ends in a period.", "So does this."])
    assert ".." not in result
    assert result == "This ends in a period. So does this."


def test_join_sentences_adds_missing_periods() -> None:
    assert _join_sentences(["No period here"]) == "No period here."


def test_join_sentences_skips_blank_parts() -> None:
    assert _join_sentences(["First.", "", "  ", "Second."]) == "First. Second."
