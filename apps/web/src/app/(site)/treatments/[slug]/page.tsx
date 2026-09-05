import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { AppointmentForm } from "@/components/site/appointment-form";
import { DoctorCard } from "@/components/site/doctor-card";
import { FaqAccordion } from "@/components/site/faq-accordion";
import { ReviewsSection } from "@/components/site/reviews-section";
import { SectionHeading } from "@/components/site/section-heading";
import { TrustBadges } from "@/components/site/trust-badges";
import { WhatsAppButton } from "@/components/site/whatsapp-button";
import { ApiError, publicApiFetch } from "@/lib/api";
import { getProcessSteps, getReviewsForTreatment } from "@/lib/site-content";
import type { PublicDoctor, PublicTreatment } from "@/lib/types";

async function getTreatment(slug: string): Promise<PublicTreatment> {
  try {
    return await publicApiFetch<PublicTreatment>(`/treatments/${slug}`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  }
}

function findMatchedDoctor(
  treatment: PublicTreatment,
  doctors: PublicDoctor[]
): PublicDoctor | undefined {
  const target = treatment.name.toLowerCase();
  return (
    doctors.find((doctor) =>
      doctor.specialties?.some(
        (specialty) =>
          target.includes(specialty.toLowerCase()) || specialty.toLowerCase().includes(target)
      )
    ) ?? doctors[0]
  );
}

export async function generateMetadata(
  props: PageProps<"/treatments/[slug]">
): Promise<Metadata> {
  const { slug } = await props.params;
  const treatment = await getTreatment(slug);
  return {
    title: `${treatment.name} in Dubai`,
    description: treatment.description ?? undefined,
  };
}

export default async function TreatmentPage(props: PageProps<"/treatments/[slug]">) {
  const { slug } = await props.params;
  const [treatment, doctors, allTreatments, clinic] = await Promise.all([
    getTreatment(slug),
    publicApiFetch<PublicDoctor[]>("/doctors"),
    publicApiFetch<PublicTreatment[]>("/treatments"),
    publicApiFetch<{ primary_phone: string | null }>("/clinic"),
  ]);
  const doctor = findMatchedDoctor(treatment, doctors);
  const processSteps = getProcessSteps(treatment.category);
  const reviews = getReviewsForTreatment(treatment.name);

  return (
    <div>
      {/* Overview */}
      <section className="bg-charcoal text-ivory">
        <div className="mx-auto max-w-6xl px-6 py-20">
          {treatment.category && (
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-gold">
              {treatment.category}
            </p>
          )}
          <h1 className="mt-4 max-w-2xl font-serif text-4xl leading-tight sm:text-5xl">
            {treatment.name} in Dubai
          </h1>
          {treatment.description && (
            <p className="mt-5 max-w-xl text-ivory/70">{treatment.description}</p>
          )}
          <div className="mt-8 flex flex-wrap items-center gap-6 text-sm text-ivory/80">
            {treatment.duration && <span>Duration: {treatment.duration}</span>}
            {treatment.price_guidance && <span>{treatment.price_guidance}</span>}
          </div>
          <div className="mt-8 flex flex-wrap gap-4">
            <a
              href="#book"
              className="rounded-full bg-gold px-7 py-3 text-sm font-medium text-charcoal transition-colors hover:bg-gold-dark"
            >
              Book a Consultation
            </a>
            {clinic.primary_phone && (
              <WhatsAppButton
                phone={clinic.primary_phone}
                treatmentName={treatment.name}
                variant="inline"
              />
            )}
          </div>
        </div>
      </section>

      {/* Approved information */}
      {treatment.approved_information && (
        <section className="mx-auto max-w-3xl px-6 py-16">
          <SectionHeading eyebrow="What to know" title="About this treatment" />
          <p className="mt-4 text-charcoal-soft">{treatment.approved_information}</p>
        </section>
      )}

      {/* Trust */}
      <section className="border-y border-ivory-soft bg-white">
        <div className="mx-auto max-w-6xl px-6 py-10">
          <TrustBadges />
        </div>
      </section>

      {/* Doctor */}
      {doctor && (
        <section className="mx-auto max-w-6xl px-6 py-16">
          <SectionHeading eyebrow="Your specialist" title="Who you'll see" />
          <div className="mt-8 max-w-sm">
            <DoctorCard doctor={doctor} />
          </div>
        </section>
      )}

      {/* Process */}
      <section className="bg-ivory-soft/60">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <SectionHeading eyebrow="How it works" title="Treatment process" />
          <ol className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {processSteps.map((step, index) => (
              <li key={step} className="rounded-2xl bg-white p-6">
                <span className="font-serif text-2xl text-gold-dark">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <p className="mt-3 text-sm text-charcoal-soft">{step}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Reviews */}
      <section className="mx-auto max-w-6xl px-6 py-16">
        <SectionHeading eyebrow="Patient stories" title="What patients say" />
        <div className="mt-8">
          <ReviewsSection reviews={reviews} />
        </div>
      </section>

      {/* FAQ */}
      {treatment.faq && treatment.faq.length > 0 && (
        <section className="bg-ivory-soft/60">
          <div className="mx-auto max-w-6xl px-6 py-16">
            <SectionHeading eyebrow="FAQs" title={`Questions about ${treatment.name}`} />
            <div className="mt-8 max-w-2xl">
              <FaqAccordion items={treatment.faq} />
            </div>
          </div>
        </section>
      )}

      {/* Book */}
      <section id="book" className="mx-auto max-w-2xl scroll-mt-20 px-6 py-20">
        <SectionHeading
          align="center"
          eyebrow="Get started"
          title={`Book your ${treatment.name} consultation`}
        />
        <div className="mt-10">
          <AppointmentForm
            treatments={allTreatments.map((t) => ({ id: t.id, name: t.name }))}
            defaultTreatmentId={treatment.id}
          />
        </div>
      </section>
    </div>
  );
}
