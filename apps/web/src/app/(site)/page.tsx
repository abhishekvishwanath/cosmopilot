import { AppointmentForm } from "@/components/site/appointment-form";
import { DoctorCard } from "@/components/site/doctor-card";
import { FaqAccordion } from "@/components/site/faq-accordion";
import { ReviewsSection } from "@/components/site/reviews-section";
import { SectionHeading } from "@/components/site/section-heading";
import { TreatmentCard } from "@/components/site/treatment-card";
import { TrustBadges } from "@/components/site/trust-badges";
import { WhatsAppButton } from "@/components/site/whatsapp-button";
import { publicApiFetch } from "@/lib/api";
import { CLINIC_FAQS, DEMO_REVIEWS } from "@/lib/site-content";
import type { PublicClinic, PublicDoctor, PublicTreatment } from "@/lib/types";

export default async function HomePage() {
  const [clinic, treatments, doctors] = await Promise.all([
    publicApiFetch<PublicClinic>("/clinic"),
    publicApiFetch<PublicTreatment[]>("/treatments"),
    publicApiFetch<PublicDoctor[]>("/doctors"),
  ]);
  const location = clinic.locations[0];

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden bg-charcoal text-ivory">
        <div className="pointer-events-none absolute -right-32 -top-32 h-96 w-96 rounded-full bg-gold/10 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-40 -left-20 h-96 w-96 rounded-full bg-emerald/30 blur-3xl" />
        <div className="relative mx-auto max-w-6xl px-6 py-24 sm:py-32">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-gold">
            Premium Cosmetic Dentistry — Dubai
          </p>
          <h1 className="mt-4 max-w-2xl font-serif text-4xl leading-tight sm:text-6xl">
            A smile you&apos;re proud of, and a booking process that respects your time.
          </h1>
          <p className="mt-6 max-w-xl text-ivory/70">
            Veneers, Invisalign, implants, and full smile makeovers at {clinic.name}. Enquire
            below and hear back in minutes — not days.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-4">
            <a
              href="#book"
              className="rounded-full bg-gold px-7 py-3 text-sm font-medium text-charcoal transition-colors hover:bg-gold-dark"
            >
              Book a Consultation
            </a>
            {clinic.primary_phone && (
              <WhatsAppButton phone={clinic.primary_phone} variant="inline" />
            )}
          </div>
        </div>
      </section>

      {/* Trust bar */}
      <section className="border-b border-ivory-soft bg-white">
        <div className="mx-auto max-w-6xl px-6 py-10">
          <TrustBadges />
        </div>
      </section>

      {/* Treatments */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <SectionHeading
          eyebrow="Treatments"
          title="Popular treatments at Cosmo Dental Dubai"
          description="Every treatment page includes approved pricing guidance, FAQs, and a direct path to booking."
        />
        <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {treatments.map((treatment) => (
            <TreatmentCard key={treatment.id} treatment={treatment} />
          ))}
        </div>
      </section>

      {/* Why this clinic */}
      <section className="bg-ivory-soft/60">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <SectionHeading
            eyebrow="Why Cosmo Dental Dubai"
            title="Specialist-led care, without the back-and-forth"
            description="A small team of specialists, transparent pricing guidance, and a follow-up process designed so no enquiry goes cold."
          />
          <div className="mt-10 grid gap-6 sm:grid-cols-3">
            {[
              {
                title: "Specialist-matched",
                body: "Every treatment is led by a specialist in that exact procedure — not a generalist.",
              },
              {
                title: "Fast follow-up",
                body: "New enquiries are contacted in minutes via call or WhatsApp, not days later.",
              },
              {
                title: "No surprise pricing",
                body: "Approved price guidance is shared upfront — full quotes confirmed at consultation.",
              },
            ].map((item) => (
              <div key={item.title} className="rounded-2xl bg-white p-6">
                <h3 className="font-serif text-lg text-charcoal">{item.title}</h3>
                <p className="mt-2 text-sm text-charcoal-soft">{item.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Doctors */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <SectionHeading
          eyebrow="Our specialists"
          title="Meet the team"
          description="Board-credentialed specialists across cosmetic, orthodontic, and implant dentistry."
        />
        <div className="mt-10 grid gap-6 sm:grid-cols-3">
          {doctors.map((doctor) => (
            <DoctorCard key={doctor.id} doctor={doctor} />
          ))}
        </div>
      </section>

      {/* Reviews */}
      <section id="reviews" className="bg-ivory-soft/60 scroll-mt-20">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <SectionHeading eyebrow="Patient stories" title="What patients say" />
          <div className="mt-10">
            <ReviewsSection reviews={DEMO_REVIEWS} />
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="mx-auto max-w-6xl scroll-mt-20 px-6 py-20">
        <SectionHeading eyebrow="FAQs" title="Good to know before you book" />
        <div className="mt-10 max-w-2xl">
          <FaqAccordion items={CLINIC_FAQS} />
        </div>
      </section>

      {/* Location */}
      <section id="location" className="bg-emerald-soft scroll-mt-20">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <SectionHeading eyebrow="Visit us" title="Location & opening hours" />
          {location && (
            <div className="mt-8 grid gap-8 sm:grid-cols-2">
              <div>
                <p className="text-charcoal">{location.address}</p>
                <p className="text-charcoal-soft">
                  {location.city}, {location.country}
                </p>
                {location.phone && <p className="mt-2 text-charcoal-soft">{location.phone}</p>}
              </div>
              {location.opening_hours && (
                <dl className="space-y-1 text-sm">
                  {Object.entries(location.opening_hours).map(([day, hours]) => (
                    <div key={day} className="flex justify-between border-b border-charcoal/10 py-1">
                      <dt className="capitalize text-charcoal-soft">{day.replace("-", " – ")}</dt>
                      <dd className="text-charcoal">{hours}</dd>
                    </div>
                  ))}
                </dl>
              )}
            </div>
          )}
        </div>
      </section>

      {/* Book */}
      <section id="book" className="mx-auto max-w-2xl scroll-mt-20 px-6 py-20">
        <SectionHeading
          align="center"
          eyebrow="Get started"
          title="Request a consultation"
          description="Tell us a little about what you're looking for — we'll follow up almost immediately."
        />
        <div className="mt-10">
          <AppointmentForm
            treatments={treatments.map((t) => ({ id: t.id, name: t.name }))}
          />
        </div>
      </section>
    </div>
  );
}
