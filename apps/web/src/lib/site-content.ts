// Fictional demo content for Cosmo Dental Dubai (CLAUDE.md §35). Reviews
// aren't part of the CRM data model (§8) — there's no real review source
// yet, so these are static and clearly labeled in the UI, not pulled from
// a database as if they were genuine patient feedback.

export interface DemoReview {
  id: string;
  name: string;
  treatment: string;
  rating: 5 | 4;
  quote: string;
}

export const DEMO_REVIEWS: DemoReview[] = [
  {
    id: "r1",
    name: "H. Al Mansoori",
    treatment: "Porcelain Veneers",
    rating: 5,
    quote:
      "The whole process was explained clearly before I committed to anything. My smile looks natural, not \"done.\"",
  },
  {
    id: "r2",
    name: "R. Fernandes",
    treatment: "Invisalign Clear Aligners",
    rating: 5,
    quote:
      "Booked a consultation online and someone followed up almost immediately. Straightened my teeth in under a year.",
  },
  {
    id: "r3",
    name: "S. Okonkwo",
    treatment: "Dental Implants",
    rating: 5,
    quote:
      "Was nervous about implants but the team walked me through every step. Zero regrets, and the result feels permanent.",
  },
  {
    id: "r4",
    name: "A. Petrova",
    treatment: "Smile Makeover",
    rating: 4,
    quote:
      "Took a couple of extra visits to get the shade exactly right, but they didn't rush it and I'm glad they didn't.",
  },
];

export interface GeneralFaqItem {
  q: string;
  a: string;
}

export const CLINIC_FAQS: GeneralFaqItem[] = [
  {
    q: "Do I need a referral to book a consultation?",
    a: "No — you can book directly through this site, WhatsApp, or by phone. No referral needed for cosmetic consultations.",
  },
  {
    q: "How soon can I get an appointment?",
    a: "Most enquiries are followed up within minutes during clinic hours, and we'll offer the soonest suitable slot from live availability.",
  },
  {
    q: "Do you accept international patients?",
    a: "Yes — many patients travel to Dubai specifically for treatment. Ask about scheduling multiple visits around your trip.",
  },
  {
    q: "What happens if I need to reschedule?",
    a: "Just reply to your confirmation message or WhatsApp us — rescheduling is free with reasonable notice.",
  },
];

// Generic, non-clinical step outline per treatment category — deliberately
// process/logistics only (booking, visits, follow-up), never medical
// claims. Falls back to a sensible default for unlisted categories.
const PROCESS_STEPS_BY_CATEGORY: Record<string, string[]> = {
  Cosmetic: [
    "Consultation to discuss your goals and assess suitability",
    "Personalized treatment plan with clear pricing",
    "Treatment visit(s) at the clinic",
    "Follow-up check-in after treatment",
  ],
  Orthodontics: [
    "Consultation and digital scan of your teeth",
    "Custom treatment plan with expected timeline",
    "Regular check-ins as your teeth move",
    "Retention plan once treatment is complete",
  ],
  Restorative: [
    "Consultation and imaging to assess the site",
    "Personalized treatment plan with clear pricing",
    "Procedure visit(s) at the clinic",
    "Healing check-ins and final review",
  ],
};

const DEFAULT_PROCESS_STEPS = [
  "Consultation to understand your goals",
  "Personalized treatment plan with clear pricing",
  "Treatment visit(s) at the clinic",
  "Follow-up after treatment",
];

export function getProcessSteps(category: string | null): string[] {
  if (category && PROCESS_STEPS_BY_CATEGORY[category]) {
    return PROCESS_STEPS_BY_CATEGORY[category];
  }
  return DEFAULT_PROCESS_STEPS;
}

export function getReviewsForTreatment(treatmentName: string): DemoReview[] {
  const matched = DEMO_REVIEWS.filter((r) => r.treatment === treatmentName);
  return matched.length > 0 ? matched : DEMO_REVIEWS.slice(0, 3);
}
