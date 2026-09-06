from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    appointments,
    auth,
    clinics,
    concierge,
    conversations,
    doctors,
    health,
    knowledge,
    leads,
    public,
    treatments,
    vapi,
    webhooks,
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
api_router.include_router(concierge.router)
api_router.include_router(webhooks.router)
api_router.include_router(vapi.router)

# integrations (see docs/API_CONVENTIONS.md) are added once a real
# provider integration (Meta WhatsApp, Stripe) needs its own inbound
# webhook — n8n's are covered by webhooks.router above, Vapi's by
# vapi.router.
