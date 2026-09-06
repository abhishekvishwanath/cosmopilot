from app.agents.concierge import (
    ToolCallTrace,
    _claims_booking_confirmed,
    _confirmed_by_tool_evidence,
    _looks_like_an_unexecuted_tool_call,
    _requests_human,
    _summarize_terminal_success,
)


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


def test_claims_booking_confirmed_detects_common_phrasings() -> None:
    assert _claims_booking_confirmed("Your appointment has been booked for 9am.") is True
    assert _claims_booking_confirmed("You're booked in for Monday!") is True


def test_claims_booking_confirmed_detects_bare_word() -> None:
    # Observed live: qwen2.5:7b once replied with nothing but this single
    # word after skipping book_appointment entirely — the exact fabrication
    # this guard exists to catch, so the check must not require a full
    # sentence.
    assert _claims_booking_confirmed("booked") is True
    assert _claims_booking_confirmed("Confirmed!") is True


def test_claims_booking_confirmed_false_for_unrelated_reply() -> None:
    assert _claims_booking_confirmed("Veneers typically take 2-3 visits.") is False


def test_confirmed_by_tool_evidence_true_when_book_appointment_succeeded() -> None:
    trace = [ToolCallTrace(name="book_appointment", arguments={}, result={"booked": True})]
    assert _confirmed_by_tool_evidence(trace) is True


def test_confirmed_by_tool_evidence_true_when_status_lookup_shows_booked() -> None:
    trace = [
        ToolCallTrace(
            name="get_appointment_status",
            arguments={},
            result={"appointments": [{"status": "confirmed"}]},
        )
    ]
    assert _confirmed_by_tool_evidence(trace) is True


def test_confirmed_by_tool_evidence_false_for_intent_only() -> None:
    """
    This is the exact bug the guard exists to catch — a model that calls
    create_appointment_intent (which only records intent, never books) and
    then tells the patient a fixed time is "booked" anyway.
    """
    trace = [
        ToolCallTrace(
            name="create_appointment_intent", arguments={}, result={"status": "APPOINTMENT_INTENT"}
        )
    ]
    assert _confirmed_by_tool_evidence(trace) is False


def test_confirmed_by_tool_evidence_false_for_no_tool_calls() -> None:
    assert _confirmed_by_tool_evidence([]) is False


def test_looks_like_an_unexecuted_tool_call_detects_fake_calls() -> None:
    assert _looks_like_an_unexecuted_tool_call('book_appointment("abc123")') is True
    assert _looks_like_an_unexecuted_tool_call("get_appointment_status()") is True
    assert _looks_like_an_unexecuted_tool_call('escalate_to_human({"reason": "pain"})') is True


def test_looks_like_an_unexecuted_tool_call_false_for_normal_replies() -> None:
    assert _looks_like_an_unexecuted_tool_call("Sure, I can help with that!") is False
    assert _looks_like_an_unexecuted_tool_call("Call us at (04) 000-0000 for more info.") is False


def test_summarize_terminal_success_confirms_a_real_booking() -> None:
    """
    This is the exact bug the helper exists to catch — observed live: a
    booking succeeded but the turn ran out of MAX_TOOL_ITERATIONS before
    the model could also produce a text reply, so the generic "looping in
    the clinic team" fallback fired and downgraded a real success into an
    escalation. Confirming from the tool's own result instead avoids that.
    """
    trace = [
        ToolCallTrace(
            name="book_appointment",
            arguments={"slot_token": "abc"},
            result={
                "booked": True,
                "start": "2026-09-07T09:00:00+04:00",
                "doctor_name": "Dr. Layla Haddad",
            },
        )
    ]
    summary = _summarize_terminal_success(trace)
    assert summary is not None
    assert "2026-09-07T09:00:00+04:00" in summary
    assert "Dr. Layla Haddad" in summary


def test_summarize_terminal_success_only_considers_the_last_call() -> None:
    trace = [
        ToolCallTrace(name="book_appointment", arguments={}, result={"booked": True, "start": "x"}),
        ToolCallTrace(
            name="create_appointment_intent", arguments={}, result={"status": "APPOINTMENT_INTENT"}
        ),
    ]
    assert _summarize_terminal_success(trace) is None


def test_summarize_terminal_success_none_when_nothing_succeeded() -> None:
    trace = [
        ToolCallTrace(
            name="create_appointment_intent", arguments={}, result={"status": "APPOINTMENT_INTENT"}
        )
    ]
    assert _summarize_terminal_success(trace) is None
    assert _summarize_terminal_success([]) is None
