"""
One-time Vapi provisioning for Phase 10 (CLAUDE.md §7/§10/§32). Vapi is
call transport only — the model, tool schemas, and system prompt come
straight from app/agents/tools.py and app/agents/prompts.py, the exact
same sources the text Concierge uses, so this script never hand-duplicates
the assistant's brain as a second, drifting copy.

Usage (from apps/api, with the venv active):
    python scripts/create_vapi_assistant.py --webhook-url https://your-tunnel.example.com/api/v1/webhooks/vapi

`--webhook-url` must be publicly reachable — Vapi can't call `localhost`,
so local development needs a tunnel (e.g. `ngrok http 8000`) pointed at
the FastAPI dev server, same as n8n's local-development story.

Safe to re-run: if VAPI_ASSISTANT_ID is already set in .env, this updates
that assistant in place instead of creating a duplicate.
"""

import argparse
import asyncio
import os
import sys
from typing import Any

import httpx

sys.path.insert(0, os.getcwd())

from app.agents.prompts import (  # noqa: E402
    VOICE_CONCIERGE_FIRST_MESSAGE,
    VOICE_CONCIERGE_SYSTEM_PROMPT,
)
from app.agents.tools import TOOL_SCHEMAS  # noqa: E402
from app.core.config import get_settings  # noqa: E402

VAPI_API_URL = "https://api.vapi.ai"


def _build_tools(webhook_url: str, webhook_secret: str) -> list[dict[str, Any]]:
    # Reuses TOOL_SCHEMAS' `function` dict verbatim (name/description/
    # parameters already match Vapi's expected OpenAIFunction shape) so
    # there's exactly one place the AI Concierge's tool set is defined.
    return [
        {
            "type": "function",
            "function": schema["function"],
            "server": {"url": webhook_url, "secret": webhook_secret},
            "async": False,
        }
        for schema in TOOL_SCHEMAS
    ]


async def _ensure_groq_credential(client: httpx.AsyncClient, groq_api_key: str) -> None:
    response = await client.get("/credential")
    response.raise_for_status()
    if any(c.get("provider") == "groq" for c in response.json()):
        return
    response = await client.post(
        "/credential",
        json={"provider": "groq", "apiKey": groq_api_key, "name": "CosmoPilot Groq"},
    )
    response.raise_for_status()
    print("Created Groq credential on this Vapi account.")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--webhook-url",
        required=True,
        help="Public URL for POST /api/v1/webhooks/vapi (e.g. an ngrok tunnel + path)",
    )
    args = parser.parse_args()

    settings = get_settings()
    missing = [
        name
        for name, value in [
            ("VAPI_API_KEY", settings.vapi_api_key),
            ("GROQ_API_KEY", settings.groq_api_key),
            ("VAPI_WEBHOOK_SECRET", settings.vapi_webhook_secret),
            ("VAPI_PHONE_NUMBER_ID", settings.vapi_phone_number_id),
        ]
        if not value
    ]
    if missing:
        raise SystemExit(f"Missing required .env settings: {', '.join(missing)}")

    headers = {"Authorization": f"Bearer {settings.vapi_api_key}"}
    async with httpx.AsyncClient(base_url=VAPI_API_URL, headers=headers, timeout=30.0) as client:
        await _ensure_groq_credential(client, settings.groq_api_key)  # type: ignore[arg-type]

        payload: dict[str, Any] = {
            "name": "CosmoPilot AI Concierge",
            "voice": {"provider": "vapi", "voiceId": "Elliot"},
            "model": {
                "provider": "groq",
                "model": settings.groq_model,
                "temperature": 0.3,
                "tools": _build_tools(args.webhook_url, settings.vapi_webhook_secret),  # type: ignore[arg-type]
                "messages": [{"role": "system", "content": VOICE_CONCIERGE_SYSTEM_PROMPT}],
            },
            "firstMessage": VOICE_CONCIERGE_FIRST_MESSAGE,
            "firstMessageMode": "assistant-speaks-first",
            "analysisPlan": {"summaryPlan": {"enabled": True}},
            "server": {"url": args.webhook_url, "secret": settings.vapi_webhook_secret},
        }

        if settings.vapi_assistant_id:
            response = await client.patch(f"/assistant/{settings.vapi_assistant_id}", json=payload)
            response.raise_for_status()
            assistant_id = settings.vapi_assistant_id
            print(f"Updated existing assistant {assistant_id}.")
        else:
            response = await client.post("/assistant", json=payload)
            response.raise_for_status()
            assistant_id = response.json()["id"]
            print(
                f"Created assistant {assistant_id} — "
                "add this to apps/api/.env as VAPI_ASSISTANT_ID."
            )

        response = await client.patch(
            f"/phone-number/{settings.vapi_phone_number_id}",
            json={"assistantId": assistant_id},
        )
        response.raise_for_status()
        print(f"Attached assistant {assistant_id} to phone number {settings.vapi_phone_number_id}.")


if __name__ == "__main__":
    asyncio.run(main())
