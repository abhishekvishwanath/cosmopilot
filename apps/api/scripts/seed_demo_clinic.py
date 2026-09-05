"""
Seeds the fictional demo clinic (CLAUDE.md §35 — "Cosmo Dental Dubai") and
optionally grants a real Supabase Auth user staff access to it, so the CRM
dashboard has something real to show.

Idempotent: safe to re-run — looks up existing rows by name/email before
inserting, so it won't create duplicates.

Usage (from apps/api, with the venv active):
    python scripts/seed_demo_clinic.py
    python scripts/seed_demo_clinic.py --grant-access you@example.com
"""

import argparse
import asyncio
import os
import sys
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, os.getcwd())

from app.core.config import get_settings  # noqa: E402
from app.db.session import get_sessionmaker  # noqa: E402
from app.models.catalog import Doctor, Treatment  # noqa: E402
from app.models.clinic import Clinic, ClinicLocation, ClinicStaff  # noqa: E402
from app.models.lead import Lead  # noqa: E402
from app.repositories import appointments as appointments_repo  # noqa: E402
from app.repositories import events as events_repo  # noqa: E402

CLINIC_NAME = "Cosmo Dental Dubai"

DOCTORS: list[dict[str, Any]] = [
    {
        "name": "Dr. Layla Haddad",
        "title": "Lead Cosmetic Dentist",
        "specialties": ["Veneers", "Smile Makeovers"],
        "credentials": "DDS, Fictional Academy of Cosmetic Dentistry (demo data)",
        "bio": "Fictional demo profile — 12 years of cosmetic dentistry experience.",
    },
    {
        "name": "Dr. Omar Al Farsi",
        "title": "Orthodontist",
        "specialties": ["Invisalign", "Clear Aligners"],
        "credentials": "DMD, Fictional Board of Orthodontics (demo data)",
        "bio": "Fictional demo profile — Invisalign Diamond provider (illustrative).",
    },
    {
        "name": "Dr. Sara Khan",
        "title": "Implantologist",
        "specialties": ["Dental Implants", "Full-Mouth Rehabilitation"],
        "credentials": "BDS, MSc Implantology (demo data)",
        "bio": "Fictional demo profile — specializes in full-arch implant cases.",
    },
]

TREATMENTS: list[dict[str, Any]] = [
    {
        "name": "Porcelain Veneers",
        "category": "Cosmetic",
        "description": "Custom porcelain veneers to redesign smile shape, shade, and alignment.",
        "approved_information": (
            "Demo/approved copy: veneers are thin porcelain shells bonded to the front "
            "of teeth. Typically 2 visits. Results are illustrative demo content, not a "
            "real clinic's claims."
        ),
        "faq": [
            {
                "q": "How long do veneers last?",
                "a": "Demo answer: typically 10-15 years with proper care.",
            },
            {
                "q": "Is the procedure painful?",
                "a": "Demo answer: minimal discomfort, local anesthesia used for prep.",
            },
            {
                "q": "How many teeth can be treated?",
                "a": "Demo answer: from a single tooth up to a full smile makeover.",
            },
        ],
        "price_guidance": "Demo guidance: starting from AED 2,500 per tooth (illustrative only).",
        "duration": "2 visits, ~2-3 weeks",
    },
    {
        "name": "Invisalign Clear Aligners",
        "category": "Orthodontics",
        "description": "Clear aligner therapy for teeth straightening without metal braces.",
        "approved_information": "Demo/approved copy: treatment length varies by case complexity.",
        "faq": [
            {"q": "Is it painful?", "a": "Demo answer: mild pressure for the first few days."},
            {
                "q": "How often are check-ins needed?",
                "a": "Demo answer: roughly every 6-8 weeks during treatment.",
            },
            {
                "q": "Can I eat and drink normally?",
                "a": "Demo answer: remove aligners for meals; water is fine while wearing them.",
            },
        ],
        "price_guidance": "Demo guidance: starting from AED 9,000 (illustrative only).",
        "duration": "6-18 months",
    },
    {
        "name": "Dental Implants",
        "category": "Restorative",
        "description": "Titanium implant + crown to replace a missing tooth.",
        "approved_information": "Demo/approved copy: includes consultation, placement, and crown.",
        "faq": [
            {"q": "Is the procedure safe?", "a": "Demo answer: routine, under local anesthesia."},
            {
                "q": "How long is recovery?",
                "a": "Demo answer: initial healing ~1-2 weeks, full integration 3-6 months.",
            },
            {
                "q": "Do implants look natural?",
                "a": "Demo answer: crowns are shade-matched to surrounding teeth.",
            },
        ],
        "price_guidance": "Demo guidance: starting from AED 4,500 per implant (illustrative only).",
        "duration": "3-6 months (including healing)",
    },
    {
        "name": "Smile Makeover",
        "category": "Cosmetic",
        "description": "Combination treatment plan tailored to full smile aesthetics.",
        "approved_information": "Demo/approved copy: plan combines veneers, whitening, contouring.",
        "faq": [
            {"q": "How many visits?", "a": "Demo answer: varies by combination chosen."},
            {
                "q": "Is a consultation required first?",
                "a": "Demo answer: yes, plans are built around your goals and current smile.",
            },
        ],
        "price_guidance": "Demo guidance: custom quote after consultation (illustrative only).",
        "duration": "Varies by plan",
    },
    {
        "name": "Teeth Whitening",
        "category": "Cosmetic",
        "description": "In-clinic professional whitening treatment.",
        "approved_information": "Demo/approved copy: single-session in-clinic whitening.",
        "faq": [
            {"q": "How long do results last?", "a": "Demo answer: typically 6-12 months."},
            {
                "q": "Is whitening safe for enamel?",
                "a": "Demo answer: performed under supervision at a controlled concentration.",
            },
        ],
        "price_guidance": "Demo guidance: starting from AED 800 (illustrative only).",
        "duration": "1 visit, ~60-90 minutes",
    },
]

DEMO_LEADS: list[dict[str, Any]] = [
    {
        "name": "Fatima Al Mazrouei",
        "email": "fatima.demo@example.com",
        "phone": "+971501234567",
        "treatment_name": "Porcelain Veneers",
        "source": "google_ads",
        "status": "NEW",
    },
    {
        "name": "James Whitfield",
        "email": "james.demo@example.com",
        "phone": "+971502345678",
        "treatment_name": "Invisalign Clear Aligners",
        "source": "instagram",
        "status": "CONTACTED",
    },
    {
        "name": "Noura Al Suwaidi",
        "email": "noura.demo@example.com",
        "phone": "+971503456789",
        "treatment_name": "Smile Makeover",
        "source": "chatgpt",
        "status": "QUALIFIED",
    },
    {
        "name": "Michael Chen",
        "email": "michael.demo@example.com",
        "phone": "+971504567890",
        "treatment_name": "Dental Implants",
        "source": "referral",
        "status": "BOOKED",
    },
    {
        "name": "Aisha Rahman",
        "email": "aisha.demo@example.com",
        "phone": "+971505678901",
        "treatment_name": "Teeth Whitening",
        "source": "google_search",
        "status": "LOST",
    },
]


async def get_or_create_clinic(session: AsyncSession) -> Clinic:
    result = await session.execute(select(Clinic).where(Clinic.name == CLINIC_NAME))
    clinic = result.scalars().first()
    if clinic:
        return clinic

    clinic = Clinic(
        name=CLINIC_NAME,
        description=(
            "Fictional demo clinic (CLAUDE.md §35) — premium cosmetic dentistry in "
            "Dubai. All content on this record is illustrative demo data, not a real "
            "clinic's information."
        ),
        website="https://cosmodentaldubai.example",
        primary_phone="+97140000000",
        email="hello@cosmodentaldubai.example",
        timezone="Asia/Dubai",
        status="active",
    )
    session.add(clinic)
    await session.flush()

    session.add(
        ClinicLocation(
            clinic_id=clinic.id,
            address="Demo Address, Sheikh Zayed Road",
            city="Dubai",
            country="United Arab Emirates",
            phone="+97140000000",
            timezone="Asia/Dubai",
            opening_hours={
                "mon-fri": "09:00-19:00",
                "sat": "10:00-16:00",
                "sun": "closed",
            },
        )
    )
    return clinic


async def get_or_create_doctors(
    session: AsyncSession, clinic_id: uuid.UUID
) -> dict[str, Doctor]:
    result = await session.execute(select(Doctor).where(Doctor.clinic_id == clinic_id))
    existing = {d.name: d for d in result.scalars().all()}

    for doc_data in DOCTORS:
        doctor = existing.get(doc_data["name"])
        if doctor is None:
            doctor = Doctor(clinic_id=clinic_id, status="active", **doc_data)
            session.add(doctor)
            existing[doc_data["name"]] = doctor
        else:
            for field, value in doc_data.items():
                setattr(doctor, field, value)
    await session.flush()
    return existing


async def get_or_create_treatments(
    session: AsyncSession, clinic_id: uuid.UUID
) -> dict[str, Treatment]:
    result = await session.execute(select(Treatment).where(Treatment.clinic_id == clinic_id))
    existing = {t.name: t for t in result.scalars().all()}

    for t_data in TREATMENTS:
        treatment = existing.get(t_data["name"])
        if treatment is None:
            treatment = Treatment(
                clinic_id=clinic_id, status="active", booking_enabled=True, **t_data
            )
            session.add(treatment)
            existing[t_data["name"]] = treatment
        else:
            for field, value in t_data.items():
                setattr(treatment, field, value)
    await session.flush()
    return existing


async def seed_leads_and_appointment(
    session: AsyncSession,
    clinic_id: uuid.UUID,
    treatments: dict[str, Treatment],
    doctors: dict[str, Doctor],
) -> None:
    result = await session.execute(select(Lead).where(Lead.clinic_id == clinic_id))
    existing_emails = {lead.email for lead in result.scalars().all()}

    created: dict[str, Lead] = {}
    for lead_data in DEMO_LEADS:
        if lead_data["email"] in existing_emails:
            continue
        treatment = treatments.get(lead_data["treatment_name"])
        slug = (treatment.name if treatment else "general").lower().replace(" ", "-")
        lead = Lead(
            clinic_id=clinic_id,
            name=lead_data["name"],
            email=lead_data["email"],
            phone=lead_data["phone"],
            treatment_id=treatment.id if treatment else None,
            source=lead_data["source"],
            landing_page=f"/treatments/{slug}",
            consent=True,
            status=lead_data["status"],
        )
        session.add(lead)
        await session.flush()
        await events_repo.create_event(
            session,
            clinic_id=clinic_id,
            event_type="lead_created",
            source=lead_data["source"],
            lead_id=lead.id,
        )
        created[lead_data["name"]] = lead

    booked_lead = created.get("Michael Chen")
    doctor = doctors.get("Dr. Sara Khan")
    treatment = treatments.get("Dental Implants")
    if booked_lead and doctor and treatment:
        appointment = await appointments_repo.create_appointment(
            session,
            clinic_id,
            {
                "lead_id": booked_lead.id,
                "doctor_id": doctor.id,
                "treatment_id": treatment.id,
                "start": datetime.now(UTC) + timedelta(days=3, hours=2),
                "end": datetime.now(UTC) + timedelta(days=3, hours=3),
                "status": "booked",
                "location": "Cosmo Dental Dubai — Sheikh Zayed Road",
            },
        )
        await appointments_repo.add_appointment_event(
            session, appointment.id, "appointment_created"
        )

    await session.flush()


async def _find_or_create_supabase_user(email: str) -> uuid.UUID:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set to grant clinic access."
        )

    headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
    }
    base = settings.supabase_url.rstrip("/")

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Look for an existing user first (list + client-side match — small
        # dev project, no need for a heavier search mechanism).
        response = await client.get(
            f"{base}/auth/v1/admin/users", headers=headers, params={"per_page": 200}
        )
        response.raise_for_status()
        for user in response.json().get("users", []):
            if user.get("email", "").lower() == email.lower():
                return uuid.UUID(user["id"])

        # Not found — create a confirmed user with no password. They sign in
        # via magic link (see apps/web /login), nothing to type or store.
        response = await client.post(
            f"{base}/auth/v1/admin/users",
            headers=headers,
            json={"email": email, "email_confirm": True},
        )
        response.raise_for_status()
        return uuid.UUID(response.json()["id"])


async def grant_clinic_access(
    session: AsyncSession, clinic_id: uuid.UUID, email: str, role: str = "owner"
) -> None:
    user_id = await _find_or_create_supabase_user(email)

    result = await session.execute(
        select(ClinicStaff).where(
            ClinicStaff.clinic_id == clinic_id, ClinicStaff.user_id == user_id
        )
    )
    if result.scalars().first():
        print(f"{email} already has {role} access to this clinic.")
        return

    session.add(ClinicStaff(clinic_id=clinic_id, user_id=user_id, role=role))
    await session.flush()
    print(f"Granted {email} '{role}' access to {CLINIC_NAME} (user_id={user_id}).")


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--grant-access",
        metavar="EMAIL",
        help="Create/find a Supabase Auth user for this email and add them as clinic staff.",
    )
    args = parser.parse_args()

    session_factory = get_sessionmaker()
    async with session_factory() as session:
        clinic = await get_or_create_clinic(session)
        doctors = await get_or_create_doctors(session, clinic.id)
        treatments = await get_or_create_treatments(session, clinic.id)
        await seed_leads_and_appointment(session, clinic.id, treatments, doctors)

        if args.grant_access:
            await grant_clinic_access(session, clinic.id, args.grant_access)

        await session.commit()

    print(f"Seeded '{CLINIC_NAME}' — {len(doctors)} doctors, {len(treatments)} treatments.")


if __name__ == "__main__":
    asyncio.run(main())
