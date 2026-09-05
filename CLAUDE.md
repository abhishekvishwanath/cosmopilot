# CLAUDE.md — CosmoPilot
## AI Patient Acquisition & Appointment Automation Platform

> **Purpose:** This file is the single source of truth for Claude Code while building the CosmoPilot prototype. Read it completely before making architectural or implementation decisions.

---

# 1. PRODUCT IDENTITY

**Product:** CosmoPilot

**Category:** AI Patient Acquisition & Appointment Automation

**Initial vertical:** Premium cosmetic dental clinics

**Initial market:** Dubai / UAE

**Core outcome:**

> CosmoPilot helps premium cosmetic clinics get discovered through AI/search and convert that demand into booked consultations automatically.

### Core business promise

- Improve clinic visibility across AI/search discovery.
- Send qualified visitors to a premium treatment-focused landing page.
- Capture enquiries immediately.
- Respond to new enquiries within approximately 60 seconds.
- Use an AI Patient Concierge to call the lead when appropriate.
- If the call is unanswered, recover the lead through WhatsApp.
- Qualify the patient for appointment booking.
- Book or assist with booking.
- Store the lead/conversation/appointment in the CRM.
- Notify clinic staff.
- Send confirmations and reminders.
- Track the complete acquisition funnel.

### Critical positioning

Do NOT position CosmoPilot primarily as:

- An AI chatbot.
- A generic CRM.
- A GEO agency.
- A marketing dashboard.

Position it as:

> **An AI patient acquisition engine that turns AI/search discovery into booked cosmetic consultations.**

---

# 2. CURRENT PRODUCT SCOPE

The product begins **after the clinic is acquired/onboarded**.

Client acquisition and GEO execution are outside the prototype's core implementation unless explicitly requested.

### In scope

1. Premium clinic/treatment landing page.
2. Appointment enquiry form.
3. Lead capture.
4. CRM.
5. AI knowledge base.
6. AI Patient Concierge.
7. Outbound AI calling.
8. WhatsApp fallback.
9. Appointment workflow.
10. Clinic notifications.
11. Follow-up automation.
12. Appointment reminders.
13. Analytics.
14. Provider integrations.
15. Demo mode with mocked integrations.
16. Production-oriented security and reliability.

### Out of scope for initial prototype

- Cold calling clinics.
- Automated client acquisition.
- Full GEO automation.
- Guaranteeing AI rankings.
- Autonomous medical diagnosis.
- Autonomous medical advice.
- Complex hospital/EMR functionality.
- Full enterprise PMS integrations before the core prototype works.
- Building a custom payment processor.
- Building a custom calendar system for production.

---

# 3. IDEAL CUSTOMER PROFILE

### Primary ICP

Premium cosmetic dental clinics with:

- Multiple dentists/practitioners.
- Existing website.
- Strong reviews.
- Premium positioning.
- Existing marketing spend.
- Meaningful inbound enquiries.
- WhatsApp communication.
- Receptionist/sales staff.
- High-value treatment offerings.

### Priority treatments

- Veneers.
- Invisalign / clear aligners.
- Dental implants.
- Smile makeovers.
- Full-mouth rehabilitation.
- Cosmetic dentistry.
- Other premium elective cosmetic treatments.

### Avoid initially

- Very small practices with little lead volume.
- Clinics with poor digital presence.
- Clinics with almost no inbound enquiries.
- Low-ticket-only practices.
- Clinics unwilling to provide approved treatment information.
- Clinics expecting the AI to provide diagnosis or medical advice.

---

# 4. CORE USER JOURNEY

The primary user journey is:

```text
AI / Google / Social / Referral
              ↓
Treatment-specific landing page
              ↓
Visitor understands:
- Treatment
- Clinic
- Doctor
- Trust signals
- FAQs
- Booking options
              ↓
      ┌───────┼────────┐
      │       │        │
   Book Now WhatsApp  Enquiry
      │       │        │
      └───────┼────────┘
              ↓
         Lead Created
              ↓
       CRM + Attribution
              ↓
    Immediate confirmation
              ↓
     AI Concierge <60 sec
              ↓
      ┌───────┴───────┐
      │               │
   AI Call         WhatsApp
      │               │
      └───────┬───────┘
              ↓
       Qualification
              ↓
      Appointment intent
              ↓
      Availability lookup
              ↓
      ┌───────┴────────┐
      │                │
   Booked          Human escalation
      │                │
     CRM          Clinic staff
      │
 Confirmation
      │
 Reminder
      │
 Consultation
      │
 Treatment pipeline
```

---

# 5. PRODUCT PRINCIPLES

These principles are mandatory.

### 5.1 Build for revenue, not feature count

The primary success metric is:

> **Lead → qualified lead → booked appointment**

Not:

- Number of AI messages.
- Number of dashboard widgets.
- Number of integrations.
- Number of technical features.

### 5.2 Build the shortest valuable path first

The first complete vertical slice must be:

```text
Landing Page
→ Form
→ Lead
→ CRM
→ AI Call
→ Qualification
→ Appointment
→ CRM Update
→ WhatsApp fallback
```

### 5.3 Use deterministic logic for critical actions

The LLM should NOT control:

- Appointment confirmation.
- Payment confirmation.
- Database authorization.
- Clinic identity.
- Availability truth.
- Consent state.
- Security.
- Workflow state.

The LLM can reason and converse, but backend tools must execute critical actions.

### 5.4 Do not hallucinate

Never invent:

- Doctor credentials.
- Treatment information.
- Pricing.
- Appointment availability.
- Clinic policies.
- Reviews.
- Results/outcomes.
- Medical claims.

### 5.5 Human escalation is a first-class feature

Escalate when:

- Patient asks for a human.
- Patient asks a clinical question outside approved knowledge.
- AI is uncertain.
- Patient presents an urgent/emergency situation.
- Booking cannot be completed.
- Patient disputes information.
- Clinic-specific policy requires staff involvement.

### 5.6 Provider abstraction

External providers must be replaceable.

Use interfaces/adapters for:

- LLM.
- Voice.
- WhatsApp.
- Calendar.
- Payments.
- Email.

Do not tightly couple core business logic to one vendor.

---

# 6. RECOMMENDED TECH STACK

## Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui

## Backend

- Python
- FastAPI
- Pydantic

## Database

- Supabase
- PostgreSQL
- pgvector

## Authentication

- Supabase Auth

## AI

- Claude and/or OpenAI behind an abstraction layer.
- Tool calling.
- RAG.
- pgvector.
- LangGraph only when stateful agent orchestration is genuinely required.

Do NOT introduce LangGraph everywhere simply because it is available.

## Automation

- n8n

n8n is the orchestration layer for:

- Webhooks.
- Delays.
- Branching.
- Notifications.
- Follow-ups.
- Reminders.
- External workflow events.

Core application state belongs in FastAPI + PostgreSQL, not n8n.

## Voice

- Vapi

Vapi is the initial AI calling provider.

## WhatsApp

- Meta WhatsApp Cloud API preferred.

Keep a provider interface so Twilio can be added later if necessary.

## Email

- Resend

## Payments

- Stripe test mode initially, only if the prototype requires deposits/payment.

## Storage

- Supabase Storage

## Analytics

- Internal event tracking.
- PostHog optional.

## Hosting

- Vercel — Next.js.
- Railway — FastAPI.
- n8n Cloud — automation.
- Docker — local development/deployment consistency.

## Development

- GitHub.
- Docker / Docker Compose.
- Pytest.
- Playwright.
- ESLint.
- TypeScript checks.
- Production builds.

---

# 7. SYSTEM ARCHITECTURE

```text
                  AI / SEARCH
                      │
              NEXT.JS WEBSITE
                      │
        ┌─────────────┼──────────────┐
        │             │              │
      Form         WhatsApp        Chat
        │             │              │
        └─────────────┼──────────────┘
                      │
                  FASTAPI
                      │
          ┌───────────┼───────────┐
          │           │           │
      Supabase       AI          n8n
          │           │           │
         CRM      Concierge    Automation
                      │
              ┌───────┴───────┐
              │               │
            Vapi          WhatsApp
              │               │
              └───────┬───────┘
                      │
                APPOINTMENTS
                      │
                CLINIC STAFF
```

### Responsibility boundaries

**Next.js**

- Public website.
- Landing pages.
- Forms.
- AI chat UI.
- Admin dashboard.

**FastAPI**

- Business logic.
- Authentication/authorization checks.
- Lead processing.
- AI orchestration.
- Tool execution.
- Appointment logic.
- Provider adapters.
- Webhooks.
- API layer.

**Supabase/PostgreSQL**

- Persistent application state.
- CRM.
- Leads.
- Conversations.
- Appointments.
- Events.
- Clinic configuration.

**n8n**

- Workflow orchestration.
- Delays.
- Follow-ups.
- Notifications.
- Cross-system event automation.

**LLM**

- Natural language reasoning.
- Conversation.
- Intent detection.
- Approved information retrieval.
- Tool selection.

**Vapi**

- Phone call transport/conversation execution.

**Meta WhatsApp Cloud API**

- WhatsApp messaging.

---

# 8. DATA MODEL

Minimum schema:

## clinics

- id
- name
- description
- website
- primary_phone
- email
- timezone
- status
- settings
- created_at
- updated_at

## clinic_locations

- id
- clinic_id
- address
- city
- country
- phone
- opening_hours
- timezone

## doctors

- id
- clinic_id
- name
- title
- specialties
- credentials
- bio
- photo_url
- status

## treatments

- id
- clinic_id
- name
- category
- description
- approved_information
- faq
- price_guidance
- duration
- booking_enabled
- status

## leads

- id
- clinic_id
- name
- email
- phone
- whatsapp
- treatment_id
- source
- landing_page
- preferred_time
- intent_score
- consent
- status
- assigned_to
- created_at
- updated_at

## visitor_sessions

- id
- clinic_id
- treatment_id
- source
- campaign
- landing_page
- anonymous_id
- created_at

## conversations

- id
- clinic_id
- lead_id
- channel
- external_id
- status
- summary
- started_at
- ended_at

## messages

- id
- conversation_id
- direction
- sender_type
- content
- tool_name
- metadata
- external_id
- timestamp

## appointments

- id
- clinic_id
- lead_id
- doctor_id
- treatment_id
- external_id
- start
- end
- status
- location
- created_at
- updated_at

## appointment_events

- id
- appointment_id
- event_type
- metadata
- timestamp

## consents

- id
- lead_id
- channel
- consent_type
- granted
- timestamp
- source

## payments

- id
- clinic_id
- lead_id
- appointment_id
- provider
- external_id
- amount
- currency
- status
- payment_link
- timestamps

## documents

- id
- clinic_id
- type
- title
- storage_path
- extracted_text
- embedding_status

## integrations

- id
- clinic_id
- type
- provider
- status
- configuration_metadata
- health_check

## events

- id
- clinic_id
- lead_id
- appointment_id
- source
- event_type
- metadata
- timestamp

---

# 9. LEAD STATES

Use an explicit state machine.

Suggested states:

```text
NEW
 ↓
CONTACTING
 ↓
CONTACTED
 ↓
QUALIFIED
 ↓
APPOINTMENT_INTENT
 ↓
BOOKED
 ↓
CONFIRMED
 ↓
ATTENDED
```

Alternative terminal/recovery states:

```text
NO_ANSWER
WHATSAPP_FOLLOWUP
HUMAN_REQUIRED
CANCELLED
NO_SHOW
LOST
REACTIVATION
```

Do not rely on free-form AI text to determine workflow state.

---

# 10. AI PATIENT CONCIERGE

The concierge is a **patient acquisition and booking assistant**, NOT an AI dentist.

## Responsibilities

- Introduce itself clearly as the clinic's AI concierge/assistant where appropriate.
- Confirm why the patient enquired.
- Identify treatment interest.
- Answer approved clinic/treatment questions.
- Explain booking process.
- Collect minimum necessary information.
- Ask preferred appointment time.
- Check availability through tools.
- Assist with appointment booking.
- Escalate to clinic staff.
- Create structured conversation summary.
- Update CRM through tools.

## Do NOT

- Diagnose.
- Prescribe.
- Give individualized medical advice.
- Determine clinical suitability.
- Guarantee treatment outcomes.
- Invent treatment prices.
- Invent appointment slots.
- Invent doctor credentials.
- Handle emergencies as a medical triage system.

## Example conversation structure

```text
Introduction
↓
Confirm enquiry
↓
Identify treatment
↓
Understand basic booking intent
↓
Answer approved questions
↓
Ask preferred appointment time
↓
Check availability
↓
Offer available slots
↓
Book or escalate
↓
Confirm next step
```

Keep conversations concise.

Do not ask unnecessary medical questions.

---

# 11. AI KNOWLEDGE ARCHITECTURE

Use clinic-specific RAG.

Knowledge sources:

- Clinic information.
- Doctor profiles.
- Treatment descriptions.
- Approved FAQs.
- Approved pricing guidance.
- Opening hours.
- Locations.
- Booking policies.
- Clinic-provided documents.

Pipeline:

```text
Clinic content
 ↓
Document processing
 ↓
Chunking
 ↓
Embeddings
 ↓
pgvector
 ↓
Semantic retrieval
 ↓
LLM context
 ↓
Answer
```

Every answer must remain within the clinic's approved knowledge.

For dynamic information use tools instead of RAG:

- Availability → appointment tool.
- Current appointment → appointment tool.
- Payment status → payment tool.
- CRM status → CRM/database tool.

---

# 12. AI TOOLS

Implement typed tools/functions.

Required tools:

- `get_clinic_details`
- `get_treatment_details`
- `search_clinic_knowledge`
- `get_doctor_details`
- `get_approved_price_guidance`
- `get_booking_policies`
- `check_appointment_availability`
- `create_lead`
- `create_appointment_intent`
- `book_appointment`
- `reschedule_appointment`
- `cancel_appointment`
- `get_appointment_status`
- `escalate_to_human`

Optional:

- `create_payment_link`
- `send_booking_link`
- `notify_clinic_staff`

Every tool must:

- Validate input.
- Validate clinic scope.
- Return structured output.
- Log execution.
- Fail safely.
- Never allow the LLM to bypass authorization.

---

# 13. LEAD CAPTURE FLOW

When a visitor submits an enquiry:

```text
Form submit
 ↓
Frontend validation
 ↓
FastAPI
 ↓
Validate input
 ↓
Check consent
 ↓
Create lead
 ↓
Create visitor/session attribution
 ↓
CRM event
 ↓
Clinic notification/event
 ↓
Trigger n8n
 ↓
AI concierge workflow
```

Minimum useful lead fields:

- Name.
- Phone.
- Email if needed.
- Treatment interest.
- Preferred appointment time.
- Communication preference.
- Consent.
- Source.
- Landing page.

Do not collect unnecessary sensitive information.

---

# 14. 60-SECOND AI RESPONSE

The commercial promise is:

> **New enquiries receive an automated response within approximately 60 seconds.**

Preferred flow:

```text
Lead submitted
 ↓
Lead persisted
 ↓
n8n receives event
 ↓
Check lead status
 ↓
Trigger AI call
 ↓
AI concierge contacts lead
```

Do not guarantee exactly 60 seconds under all provider/network conditions.

Use wording such as:

- "within approximately 60 seconds"
- "near-instant response"
- "rapid automated follow-up"

Implement retries and failure handling.

---

# 15. AI CALL WORKFLOW

```text
New lead
 ↓
Validate lead + consent
 ↓
Check if already booked/contacted
 ↓
Trigger Vapi
 ↓
Pass:
- clinic
- treatment
- lead name
- enquiry context
- approved knowledge context
 ↓
AI call
 ↓
Conversation
 ↓
Tool calls
 ↓
Appointment or escalation
 ↓
Call summary
 ↓
FastAPI
 ↓
CRM
```

The AI must never independently mark an appointment as booked without a successful backend booking response.

---

# 16. MISSED CALL / WHATSAPP FALLBACK

If the AI call is unanswered:

```text
Call attempted
 ↓
NO_ANSWER
 ↓
Wait configurable period
 ↓
WhatsApp follow-up
 ↓
Patient replies
 ↓
AI WhatsApp concierge
 ↓
Qualification
 ↓
Appointment
```

Rules:

- Respect communication consent.
- Respect opt-outs.
- Do not spam.
- Stop follow-ups after booking.
- Stop follow-ups when human handoff is requested.
- Make retry timing configurable.
- Log every message.

Example state:

```text
NO_ANSWER
→ WHATSAPP_PENDING
→ WHATSAPP_CONTACTED
→ RESPONDED
→ BOOKED / HUMAN_REQUIRED / LOST
```

---

# 17. N8N WORKFLOWS

## Workflow A — New Lead

```text
Webhook
 ↓
Validate
 ↓
Check duplicate/idempotency
 ↓
Persist event
 ↓
Check lead status
 ↓
Trigger AI call
 ↓
Log result
```

## Workflow B — AI Call Unanswered

```text
Call result webhook
 ↓
Check status
 ↓
If NO_ANSWER
 ↓
Wait
 ↓
Check booking status
 ↓
If not booked
 ↓
Send WhatsApp
 ↓
Update CRM
```

## Workflow C — WhatsApp Incoming

```text
Meta webhook
 ↓
Identify clinic/lead
 ↓
Persist message
 ↓
Call FastAPI AI endpoint
 ↓
Retrieve context
 ↓
Tool calls
 ↓
Generate response
 ↓
Send WhatsApp
 ↓
Persist message
```

## Workflow D — Appointment Booked

```text
Appointment webhook
 ↓
Verify
 ↓
Idempotency check
 ↓
Update appointment
 ↓
Update CRM
 ↓
Cancel active follow-ups
 ↓
Notify clinic
 ↓
Send confirmation
```

## Workflow E — Reminder

```text
Scheduled trigger
 ↓
Find upcoming appointments
 ↓
Check status
 ↓
Send reminder
 ↓
Log message
```

## Workflow F — No Show

```text
No-show event
 ↓
Update CRM
 ↓
Wait configurable time
 ↓
Send rescheduling message
 ↓
Track response
 ↓
Escalate if necessary
```

## Workflow G — Payment

```text
Payment webhook
 ↓
Verify signature
 ↓
Idempotency check
 ↓
Update payment
 ↓
Update appointment/lead
 ↓
Confirmation
```

---

# 18. APPOINTMENT ARCHITECTURE

Use a provider abstraction.

```text
AppointmentService
        │
CalendarProvider interface
        │
 ┌──────────────┬───────────────┐
 │              │               │
MockCalendar  Google/etc.   Clinic PMS
```

For prototype:

- Use `MockCalendarProvider`.
- Seed realistic slots.
- Support availability.
- Support booking.
- Support rescheduling.
- Support cancellation.

Production integrations come later.

### Source of truth

The appointment provider is the source of truth for:

- Availability.
- Booking.
- Appointment status.

The LLM is never the source of truth.

---

# 19. CRM

The CRM must be simple and useful.

## Dashboard

Display:

- New leads.
- Qualified leads.
- Calls.
- Answer rate.
- WhatsApp follow-ups.
- Appointments.
- Upcoming appointments.
- No-shows.
- Conversion rate.

## Lead record

Show:

- Name.
- Contact.
- Treatment.
- Source.
- Landing page.
- Status.
- AI call status.
- WhatsApp status.
- Appointment.
- Conversation summary.
- Assigned staff.
- Timeline.

## Timeline

Example:

```text
09:32 Lead submitted
09:32 CRM created
09:33 AI call started
09:34 Patient answered
09:37 Appointment requested
09:38 Appointment booked
09:38 Clinic notified
09:38 Confirmation sent
```

---

# 20. PREMIUM WEBSITE REQUIREMENTS

The website must look like a premium medical/cosmetic brand.

Do NOT create a generic SaaS-looking clinic website.

## Required sections

- Hero.
- Treatment positioning.
- Treatment benefits/information.
- Doctor credentials.
- Clinic credentials.
- Reviews.
- Before/after section only when supplied and legally/compliantly permitted.
- FAQs.
- Location.
- Contact.
- Booking CTA.
- WhatsApp CTA.
- AI concierge entry point.

## Treatment landing page

Example:

```text
Veneers in Dubai
 ↓
Treatment overview
 ↓
Why choose clinic
 ↓
Doctor
 ↓
Reviews
 ↓
Treatment process
 ↓
FAQ
 ↓
Trust signals
 ↓
Book consultation
 ↓
WhatsApp
```

The landing page must be designed for conversion, not just aesthetics.

---

# 21. GEO CONTEXT

GEO is a service layer around the product, not the core automation engine.

Potential discovery sources:

- ChatGPT.
- Gemini.
- Perplexity.
- Google AI/search.
- Social/referral traffic.

The product should preserve:

- Source.
- Campaign.
- Landing page.
- Treatment.
- Visitor session.

Do NOT implement fake AI-ranking claims.

Do NOT guarantee:

- "#1 on ChatGPT"
- "#1 on Gemini"
- Fixed AI rankings.

The product measures and improves the conversion of AI/search traffic.

---

# 22. ANALYTICS FUNNEL

Track:

```text
Discovery
 ↓
Landing Page Visit
 ↓
Enquiry
 ↓
Lead
 ↓
AI Contact Attempt
 ↓
Contacted
 ↓
Qualified
 ↓
Appointment Intent
 ↓
Appointment Booked
 ↓
Appointment Confirmed
 ↓
Attended
 ↓
Treatment
```

Important metrics:

- Visitors.
- Leads.
- Lead conversion rate.
- AI call attempts.
- Call answer rate.
- WhatsApp recovery rate.
- Qualified lead rate.
- Appointment booking rate.
- Attendance rate.
- No-show rate.
- Treatment conversion if data is available.
- Estimated attributed revenue.

---

# 23. SECURITY & PRIVACY

This is healthcare-adjacent software. Treat patient data as sensitive.

Mandatory:

- No secrets in source code.
- `.env` for credentials.
- `.env.example` with placeholders.
- Authenticated admin routes.
- Clinic-scoped authorization.
- Input validation.
- Rate limiting.
- Webhook verification.
- Idempotency.
- Audit logs.
- Secure storage.
- HTTPS in production.
- Minimal data collection.
- Consent tracking.
- Opt-out handling.
- Data deletion/export architecture.
- No card data storage.
- No unnecessary medical information in CRM.
- Avoid storing raw sensitive conversation content when a structured summary is sufficient.

Do not claim legal/compliance certification automatically.

Production deployment must be reviewed against applicable UAE/local healthcare, privacy, advertising and messaging requirements.

---

# 24. WEBHOOK RULES

Every webhook must support:

- Signature verification where provider supports it.
- Request validation.
- Authentication.
- Idempotency.
- Duplicate detection.
- Logging.
- Safe retries.
- Error responses.
- Provider event ID storage.

Example:

```text
Webhook
 ↓
Verify signature
 ↓
Extract provider event ID
 ↓
Check processed_events
 ↓
If already processed → return success
 ↓
Otherwise process
 ↓
Persist event
 ↓
Execute action
 ↓
Mark processed
```

Never process payment or appointment events twice.

---

# 25. ERROR HANDLING

Every external integration can fail.

Handle:

- API timeout.
- API unavailable.
- Invalid credentials.
- Rate limit.
- Invalid webhook.
- Duplicate webhook.
- AI failure.
- Voice failure.
- WhatsApp failure.
- Calendar failure.
- Database failure.

User-facing behavior should be graceful.

Example:

```text
Calendar unavailable
 ↓
Do not invent slots
 ↓
Tell patient:
"We're having trouble checking live availability.
I'll have the clinic confirm your preferred time."
 ↓
Create HUMAN_REQUIRED task
```

Never fabricate a successful action.

---

# 26. MOCK / DEMO MODE

The prototype MUST work without all production credentials.

Implement interfaces:

```text
MockLLMProvider
MockVoiceProvider
MockWhatsAppProvider
MockCalendarProvider
MockPaymentProvider
```

Seed:

- One demo clinic.
- 3–5 doctors.
- 5–8 treatments.
- Reviews.
- FAQs.
- Approved treatment information.
- Appointment slots.
- Demo leads.
- Demo conversations.

The complete demo should work:

```text
Visitor
 ↓
Treatment page
 ↓
Form
 ↓
CRM
 ↓
Mock AI call
 ↓
Qualification
 ↓
Mock appointment
 ↓
CRM update
 ↓
Mock WhatsApp fallback
```

Clearly label mocked integrations in the UI.

---

# 27. PROVIDER ABSTRACTIONS

Create interfaces such as:

```text
LLMProvider
VoiceProvider
WhatsAppProvider
CalendarProvider
PaymentProvider
EmailProvider
```

Example conceptual structure:

```text
providers/
    llm/
    voice/
    whatsapp/
    calendar/
    payments/
    email/
```

Then:

```text
providers/voice/vapi.py
providers/voice/mock.py
```

Core application code should depend on the interface, not directly on Vapi.

---

# 28. API DESIGN

Use REST APIs initially.

Suggested groups:

```text
/api/v1/auth
/api/v1/clinics
/api/v1/doctors
/api/v1/treatments
/api/v1/leads
/api/v1/conversations
/api/v1/messages
/api/v1/appointments
/api/v1/analytics
/api/v1/knowledge
/api/v1/integrations
/api/v1/webhooks
```

Public endpoints must be minimal and rate-limited.

Never expose sensitive clinic/patient data through public endpoints.

---

# 29. RECOMMENDED PROJECT STRUCTURE

Use a clean monorepo unless there is a strong reason not to.

```text
cosmopilot/
├── apps/
│   ├── web/
│   └── api/
├── workflows/
│   └── n8n/
├── packages/
│   ├── types/
│   └── config/
├── docs/
├── tests/
├── scripts/
├── docker/
├── .env.example
├── docker-compose.yml
├── README.md
└── CLAUDE.md
```

Backend conceptual structure:

```text
api/
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── providers/
│   ├── agents/
│   ├── workflows/
│   ├── repositories/
│   └── utils/
└── tests/
```

Keep business logic out of route handlers.

---

# 30. TESTING STRATEGY

## Unit tests

Test:

- Lead creation.
- State transitions.
- Appointment logic.
- Consent.
- Provider adapters.
- Tool validation.
- Idempotency.
- Authorization.

## Integration tests

Test:

- Form → API → database.
- API → n8n webhook.
- AI → tool calls.
- Appointment booking.
- WhatsApp webhook.
- Vapi webhook.
- Payment webhook.

## E2E

Use Playwright.

Test:

```text
Landing page
→ enquiry
→ lead
→ AI workflow
→ appointment
→ CRM
```

Also test:

```text
Lead
→ unanswered call
→ WhatsApp
→ response
→ appointment
```

---

# 31. PHASE-WISE BUILD PLAN

Claude must build sequentially.

Do NOT attempt the entire project in one uncontrolled generation.

---

## PHASE 0 — Discovery & Architecture

Tasks:

- Inspect repository.
- Inspect existing files.
- Confirm runtime.
- Establish architecture.
- Create project structure.
- Create `.env.example`.
- Create README.
- Define provider interfaces.
- Define database plan.
- Define API conventions.

Deliverables:

- Architecture.
- Project structure.
- Setup instructions.
- Environment variable list.

Then:

**STOP and request review.**

---

## PHASE 1 — Foundation

Build:

- Next.js.
- FastAPI.
- Supabase connection.
- Docker.
- Environment configuration.
- Logging.
- Health checks.
- Authentication foundation.
- Basic API/frontend connection.
- CI-ready lint/type/test commands.

Then:

**Run tests → review → STOP.**

---

## PHASE 2 — Database + CRM

Build:

- Migrations.
- Tables.
- Relationships.
- Seed data.
- Clinic CRUD.
- Doctors.
- Treatments.
- Leads.
- Appointments.
- Conversations.
- Events.
- Basic CRM dashboard.

Then:

**Run tests → review → STOP.**

---

## PHASE 3 — Premium Website

Build:

- Homepage.
- Treatment pages.
- Doctor pages.
- Reviews.
- FAQs.
- Trust sections.
- Appointment form.
- WhatsApp CTA.
- AI concierge UI shell.
- Responsive/mobile design.

Then:

**Run E2E smoke tests → review → STOP.**

---

## PHASE 4 — Lead Capture

Build:

- Form validation.
- Lead API.
- Consent.
- Attribution.
- Visitor session.
- CRM creation.
- Event tracking.
- Clinic notification.

Then:

**Test form → CRM → review → STOP.**

---

## PHASE 5 — AI Knowledge Base

Build:

- Document ingestion.
- Chunking.
- Embeddings.
- pgvector.
- Retrieval.
- Clinic context.
- Treatment context.
- Approved answer system.
- AI guardrails.

Then:

**Test hallucination boundaries → review → STOP.**

---

## PHASE 6 — AI Concierge

Build:

- AI provider abstraction.
- System prompt.
- Tool calling.
- Clinic context.
- Treatment context.
- Qualification flow.
- Human escalation.
- Conversation persistence.
- Structured summary.

Initially use a mock voice provider if Vapi credentials are unavailable.

Then:

**Run conversation tests → review → STOP.**

---

## PHASE 7 — Appointment Engine

Build:

- Calendar provider interface.
- MockCalendarProvider.
- Availability.
- Slot selection.
- Booking.
- Reschedule.
- Cancellation.
- Appointment status.
- CRM synchronization.

Then:

**Run booking E2E → review → STOP.**

---

## PHASE 8 — n8n Automation

Build:

### Workflow A

New lead → AI contact.

### Workflow B

Unanswered call → WhatsApp fallback.

### Workflow C

Appointment booked → stop follow-ups + notify clinic.

### Workflow D

Appointment reminder.

### Workflow E

No-show recovery.

Add:

- Error handling.
- Retries.
- Idempotency.
- Logging.

Then:

**Run complete automation test → review → STOP.**

---

## PHASE 9 — Meta WhatsApp

Only request credentials at this stage.

Need:

- Meta app.
- WhatsApp Business configuration.
- Phone number.
- Access token.
- Webhook configuration.

Build:

- Incoming webhook.
- Outgoing messages.
- Templates where required.
- Lead matching.
- AI conversation.
- Logging.
- Opt-out.

Then:

**Run WhatsApp E2E → review → STOP.**

---

## PHASE 10 — Vapi

Only request credentials at this stage.

Build:

- Vapi adapter.
- Assistant configuration.
- Outbound call.
- Lead context.
- Tool calls.
- Call events.
- Transcript/summary.
- Outcome handling.
- CRM update.

Then:

**Run live/test call → review → STOP.**

---

## PHASE 11 — Analytics

Build:

- Funnel events.
- Source attribution.
- Lead analytics.
- Call analytics.
- WhatsApp recovery.
- Appointment conversion.
- Dashboard.

Then:

**Review metrics → STOP.**

---

## PHASE 12 — Production Hardening

Build:

- Authorization.
- Clinic isolation.
- Rate limiting.
- Webhook verification.
- Idempotency.
- Audit logging.
- Error monitoring.
- Retry strategy.
- Secrets management.
- Privacy controls.
- Data retention/deletion architecture.

Then:

**Security review → STOP.**

---

## PHASE 13 — Full Demo E2E

Run:

```text
Visitor
 ↓
Treatment page
 ↓
Enquiry
 ↓
CRM
 ↓
AI call
 ↓
Qualification
 ↓
Appointment
 ↓
CRM
 ↓
Clinic notification
 ↓
Confirmation
 ↓
Reminder
```

Also:

```text
Visitor
 ↓
Enquiry
 ↓
AI call unanswered
 ↓
WhatsApp
 ↓
Conversation
 ↓
Appointment
```

Fix all critical failures.

---

# 32. CREDENTIAL / ACCOUNT PROTOCOL

Never ask for all credentials at the beginning.

Ask only when the relevant phase starts.

### Supabase

Needed around Phase 1.

Request:

- Project URL.
- Anon/public key.
- Server-side key only when genuinely required.

### AI provider

Needed around Phase 5/6.

Request:

- API key.

### Meta WhatsApp

Needed Phase 9.

Request only required credentials/configuration.

### Vapi

Needed Phase 10.

Request:

- API key.
- Required assistant configuration.

### Stripe

Only if payment functionality is included.

Use test mode first.

### Calendar/PMS

Only after identifying the clinic's actual scheduling platform.

Do not invent an integration.

For every credential request, tell the user:

1. Why it is needed.
2. Exact provider.
3. Exact credential/configuration required.
4. Whether test/live mode is needed.
5. Where to place it.
6. How to verify it works.

Never put secrets in source files.

---

# 33. CLAUDE CODE WORKING RULES

### Before coding

- Read this entire CLAUDE.md.
- Inspect the repository.
- Inspect existing code.
- Identify what already exists.
- Do not overwrite working code unnecessarily.
- State your understanding of the current phase.

### During coding

- Work phase-by-phase.
- Keep changes scoped.
- Prefer simple architecture.
- Avoid premature abstractions.
- Use provider interfaces where external services are involved.
- Write tests alongside features.
- Use typed schemas.
- Validate external inputs.
- Add structured logs for important workflows.
- Keep secrets out of Git.
- Do not fabricate API behavior.

### After each phase

Run:

- Tests.
- Lint.
- Type checks.
- Build.
- Relevant E2E tests.
- Database migration checks.

Then report:

1. What was built.
2. Files changed.
3. Tests run.
4. Test results.
5. Known issues.
6. Credentials needed for next phase.
7. Next phase.
8. Any architectural decisions.

Then:

> **STOP and wait for explicit user approval.**

Do not automatically continue into the next major phase.

---

# 34. WHEN TO ASK THE USER

Ask only when the decision materially affects implementation.

Examples:

- Which AI provider?
- Meta WhatsApp vs another provider.
- Vapi account availability.
- Actual clinic scheduling/PMS platform.
- Payment requirement.
- Production vs mock integration.
- Clinic-specific policies.
- Approved treatment content.
- Pricing information.
- Consent/communication rules.
- Branding/assets.

Do NOT interrupt for trivial implementation decisions.

Use sensible defaults for non-critical details.

---

# 35. DEMO CLINIC DEFAULT

If no real clinic exists yet, create a fictional demo clinic.

Example:

**Clinic:** Cosmo Dental Dubai

Treatments:

- Veneers.
- Invisalign.
- Dental implants.
- Smile makeover.
- Teeth whitening.

Create fictional:

- Doctors.
- Credentials.
- Reviews.
- FAQs.
- Opening hours.
- Locations.
- Appointment slots.

Clearly label demo data.

Never present fictional information as real.

---

# 36. DEMO SCRIPT

The final prototype should support this demonstration:

### Scenario 1 — Successful call

1. Open veneer landing page.
2. Submit appointment enquiry.
3. Lead appears in CRM.
4. Automation triggers.
5. AI concierge calls.
6. Patient asks:
   - Cost.
   - Treatment duration.
   - Doctor.
   - Appointment timing.
7. AI answers using approved knowledge.
8. AI checks available slots.
9. Patient chooses slot.
10. Appointment is booked.
11. CRM updates.
12. Clinic receives notification.
13. Patient receives confirmation.

### Scenario 2 — Missed call

1. Submit enquiry.
2. AI attempts call.
3. Patient does not answer.
4. n8n detects `NO_ANSWER`.
5. WhatsApp follow-up is triggered.
6. Patient responds.
7. AI continues conversation.
8. Patient books.
9. CRM updates.
10. Follow-ups stop.

This is the minimum "wow" demo.

---

# 37. SUCCESS CRITERIA

The prototype is successful when:

- A visitor can discover a treatment landing page.
- Visitor can submit an enquiry.
- Lead appears in CRM.
- Attribution is preserved.
- AI concierge can contact the lead.
- AI understands clinic/treatment context.
- AI answers approved questions.
- AI does not hallucinate.
- AI can qualify the enquiry.
- Appointment availability can be checked.
- Appointment can be booked.
- CRM updates automatically.
- Clinic receives notification.
- Missed calls trigger WhatsApp fallback.
- Appointment stops unnecessary follow-ups.
- Reminders work.
- Complete flow is visible in the dashboard.
- Demo works without production credentials through mock providers.
- Real provider integrations can be enabled without rewriting the core architecture.

---

# 38. NON-NEGOTIABLE PRODUCT RULES

1. **Do not build a generic AI chatbot.**
2. **Do not build a generic CRM.**
3. **Do not build GEO ranking guarantees.**
4. **Do not let AI invent medical information.**
5. **Do not let AI determine clinical suitability.**
6. **Do not let AI directly control critical state without backend validation.**
7. **Do not fake external integrations.**
8. **Do not hard-code secrets.**
9. **Do not tightly couple the product to one provider.**
10. **Do not build all features before validating the core funnel.**
11. **Do not collect unnecessary patient information.**
12. **Do not continue to the next major build phase without user approval.**
13. **Always preserve a working demo state.**
14. **Prioritize lead-to-appointment conversion over technical complexity.**
15. **If uncertain, choose the simplest reliable implementation and explain the tradeoff.**

---

# 39. FINAL PRODUCT NORTH STAR

CosmoPilot should make the clinic owner feel:

> "A patient finds my clinic through AI/search, submits an enquiry, gets contacted almost immediately, gets their questions answered, gets helped toward an appointment, and my staff can see everything without manually chasing the lead."

Everything built should support this outcome.

If a feature does not materially improve:

**Discovery → Lead → Contact → Qualification → Appointment → Attendance**

it is lower priority and should not delay the core product.
