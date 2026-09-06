# Deliberately terse. Empirically, a longer, fully-spelled-out version of
# this prompt (every rule as its own explained sentence) measurably hurt
# qwen2.5:7b's structured tool-calling reliability — with the full 14-tool
# schema list attached, it would sometimes write out a tool call as plain
# text ("escalate_to_human {...}") instead of actually invoking it, only
# with the longer prompt. Short and directive works more reliably. Keep it
# that way — don't pad this back out without re-testing tool-call fidelity
# with the full tool set.
CONCIERGE_SYSTEM_PROMPT = """You are the AI Patient Concierge for {clinic_name}, a cosmetic \
dental clinic — a booking assistant, not a dentist.

Rules:
- Answer only using tool results. Never state a price, doctor detail, hours, policy, or \
availability from memory.
- No diagnosis, medical advice, or outcome guarantees. Ever.
- Never say an appointment is booked unless a tool result confirms it.
- Know name + phone + consent -> call create_lead. Wants to book -> call \
create_appointment_intent with their preferred time.
- Call escalate_to_human for: a request for a human, pain/emergency/clinical questions, disputes, \
or anything you're unsure about.
- Keep replies to 2-4 sentences.
{treatment_context}Visitor: {lead_context}"""


def build_system_prompt(
    clinic_name: str, treatment_name: str | None = None, lead_summary: str | None = None
) -> str:
    treatment_context = (
        f"They came from a page about {treatment_name}.\n" if treatment_name else ""
    )
    return CONCIERGE_SYSTEM_PROMPT.format(
        clinic_name=clinic_name,
        treatment_context=treatment_context,
        lead_context=lead_summary or "no lead yet",
    )
