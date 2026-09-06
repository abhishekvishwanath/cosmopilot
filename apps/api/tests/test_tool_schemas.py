from app.agents.tools import TOOL_HANDLERS, TOOL_SCHEMAS


def test_every_schema_has_a_matching_handler() -> None:
    schema_names = {s["function"]["name"] for s in TOOL_SCHEMAS}
    assert schema_names == set(TOOL_HANDLERS.keys())


def test_every_schema_is_well_formed() -> None:
    for schema in TOOL_SCHEMAS:
        assert schema["type"] == "function"
        fn = schema["function"]
        assert isinstance(fn["name"], str) and fn["name"]
        assert isinstance(fn["description"], str) and fn["description"]
        params = fn["parameters"]
        assert params["type"] == "object"
        assert isinstance(params["properties"], dict)
        assert isinstance(params["required"], list)
        # every "required" field must actually be declared as a property
        assert set(params["required"]) <= set(params["properties"].keys())


def test_required_tools_from_claude_md_are_present() -> None:
    required = {
        "get_clinic_details",
        "get_treatment_details",
        "search_clinic_knowledge",
        "get_doctor_details",
        "get_approved_price_guidance",
        "get_booking_policies",
        "check_appointment_availability",
        "create_lead",
        "create_appointment_intent",
        "book_appointment",
        "reschedule_appointment",
        "cancel_appointment",
        "get_appointment_status",
        "escalate_to_human",
    }
    assert required <= set(TOOL_HANDLERS.keys())
