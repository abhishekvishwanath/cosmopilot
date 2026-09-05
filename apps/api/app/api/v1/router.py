from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    appointments,
    auth,
    clinics,
    conversations,
    doctors,
    health,
    knowledge,
    leads,
    public,
    treatments,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(public.router)
api_router.include_router(clinics.router)
api_router.include_router(doctors.router)
api_router.include_router(treatments.router)
api_router.include_router(leads.router)
api_router.include_router(appointments.router)
api_router.include_router(conversations.router)
api_router.include_router(analytics.router)
api_router.include_router(knowledge.router)

# integrations, webhooks (see docs/API_CONVENTIONS.md) are added starting
# Phase 6+, once the underlying features exist.
