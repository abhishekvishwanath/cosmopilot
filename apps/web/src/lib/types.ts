// Mirrors apps/api/app/schemas/*.py. Kept by hand for now — codegen from
// the OpenAPI schema is a reasonable upgrade once this surface grows.

export interface Clinic {
  id: string;
  name: string;
  description: string | null;
  website: string | null;
  primary_phone: string | null;
  email: string | null;
  timezone: string;
  status: string;
  settings: Record<string, unknown>;
}

export interface Doctor {
  id: string;
  clinic_id: string;
  name: string;
  title: string | null;
  specialties: string[] | null;
  credentials: string | null;
  bio: string | null;
  photo_url: string | null;
  status: string;
}

export interface Treatment {
  id: string;
  clinic_id: string;
  name: string;
  category: string | null;
  description: string | null;
  approved_information: string | null;
  price_guidance: string | null;
  duration: string | null;
  booking_enabled: boolean;
  status: string;
}

export interface PublicLocation {
  id: string;
  address: string | null;
  city: string | null;
  country: string | null;
  phone: string | null;
  opening_hours: Record<string, string> | null;
  timezone: string | null;
}

export interface PublicClinic {
  id: string;
  name: string;
  description: string | null;
  website: string | null;
  primary_phone: string | null;
  email: string | null;
  timezone: string;
  locations: PublicLocation[];
}

export interface PublicDoctor {
  id: string;
  slug: string;
  name: string;
  title: string | null;
  specialties: string[] | null;
  credentials: string | null;
  bio: string | null;
  photo_url: string | null;
}

export interface TreatmentFaqItem {
  q: string;
  a: string;
}

export interface PublicTreatment {
  id: string;
  slug: string;
  name: string;
  category: string | null;
  description: string | null;
  approved_information: string | null;
  faq: TreatmentFaqItem[] | null;
  price_guidance: string | null;
  duration: string | null;
  booking_enabled: boolean;
}

export interface Conversation {
  id: string;
  clinic_id: string;
  lead_id: string;
  channel: string;
  status: string;
  summary: string | null;
  started_at: string | null;
  ended_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConciergeToolCall {
  name: string;
  arguments: Record<string, unknown>;
  result: Record<string, unknown>;
}

export interface ConciergeMessageResult {
  conversation_id: string;
  reply: string;
  lead_status: string;
  tool_calls: ConciergeToolCall[];
}

export interface KnowledgeDocument {
  id: string;
  clinic_id: string;
  type: string;
  title: string;
  embedding_status: string;
  created_at: string;
}

export interface KnowledgeSource {
  title: string | null;
  source_type: string;
  similarity: number;
  excerpt: string;
}

export interface KnowledgeAnswer {
  answer: string;
  grounded: boolean;
  generated: boolean;
  sources: KnowledgeSource[];
}

export interface PublicLeadCreate {
  name: string;
  phone: string;
  email?: string | null;
  treatment_id?: string | null;
  preferred_time?: string | null;
  contact_method?: "Call" | "WhatsApp" | "Email" | null;
  consent: boolean;
  source?: string | null;
  campaign?: string | null;
  landing_page?: string | null;
  anonymous_id?: string | null;
}

export interface PublicLeadResult {
  id: string;
  status: string;
}

export interface Lead {
  id: string;
  clinic_id: string;
  name: string;
  email: string | null;
  phone: string | null;
  whatsapp: string | null;
  treatment_id: string | null;
  source: string | null;
  landing_page: string | null;
  preferred_time: string | null;
  intent_score: number | null;
  consent: boolean;
  status: string;
  assigned_to: string | null;
  created_at: string;
  updated_at: string;
}

export interface LeadPage {
  items: Lead[];
  next_cursor: string | null;
}

export interface Appointment {
  id: string;
  clinic_id: string;
  lead_id: string;
  doctor_id: string | null;
  treatment_id: string | null;
  external_id: string | null;
  start: string | null;
  end: string | null;
  status: string;
  location: string | null;
}

export interface TimelineEvent {
  id: string;
  event_type: string;
  source: string | null;
  event_metadata: Record<string, unknown> | null;
  timestamp: string;
}

export interface DashboardStats {
  total_leads: number;
  leads_by_status: Record<string, number>;
  upcoming_appointments: number;
  appointments_by_status: Record<string, number>;
}

export const LEAD_STATUSES = [
  "NEW",
  "CONTACTING",
  "CONTACTED",
  "QUALIFIED",
  "APPOINTMENT_INTENT",
  "BOOKED",
  "CONFIRMED",
  "ATTENDED",
  "NO_ANSWER",
  "WHATSAPP_FOLLOWUP",
  "HUMAN_REQUIRED",
  "CANCELLED",
  "NO_SHOW",
  "LOST",
  "REACTIVATION",
] as const;
