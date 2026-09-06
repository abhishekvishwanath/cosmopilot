from app.agents.concierge import _requests_human


def test_requests_human_true_for_direct_ask() -> None:
    assert _requests_human("Can I just speak to a real person please?") is True


def test_requests_human_true_case_insensitive() -> None:
    assert _requests_human("I want to TALK TO A HUMAN now") is True


def test_requests_human_false_for_unrelated_message() -> None:
    assert _requests_human("How much do veneers cost?") is False


def test_requests_human_false_for_pain_without_explicit_human_ask() -> None:
    # Deliberately narrow — pain/medical keyword matching is left to the
    # LLM's escalate_to_human tool call, not this deterministic backstop,
    # since broad keyword matching there would be fragile.
    assert _requests_human("I have a lot of tooth pain right now") is False
