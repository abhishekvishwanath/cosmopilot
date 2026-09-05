from fastapi import APIRouter

from app.api.v1 import auth, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)

# Further resource routers (clinics, doctors, treatments, leads,
# conversations, messages, appointments, analytics, knowledge, integrations,
# webhooks — see docs/API_CONVENTIONS.md) are added starting Phase 2, once
# the underlying tables/services exist.
