import type { Metadata } from "next";

import { SectionHeading } from "@/components/site/section-heading";
import { TreatmentCard } from "@/components/site/treatment-card";
import { publicApiFetch } from "@/lib/api";
import type { PublicTreatment } from "@/lib/types";

export const metadata: Metadata = {
  title: "Treatments",
  description: "Cosmetic, orthodontic, and restorative dental treatments in Dubai.",
};

export default async function TreatmentsPage() {
  const treatments = await publicApiFetch<PublicTreatment[]>("/treatments");

  return (
    <div className="mx-auto max-w-6xl px-6 py-20">
      <SectionHeading
        eyebrow="Treatments"
        title="All treatments"
        description="Every treatment page includes approved information, pricing guidance, and FAQs — reviewed by the clinic, not invented by AI."
      />
      <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {treatments.map((treatment) => (
          <TreatmentCard key={treatment.id} treatment={treatment} />
        ))}
      </div>
    </div>
  );
}
