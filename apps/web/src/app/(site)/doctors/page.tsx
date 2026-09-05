import type { Metadata } from "next";

import { DoctorCard } from "@/components/site/doctor-card";
import { SectionHeading } from "@/components/site/section-heading";
import { publicApiFetch } from "@/lib/api";
import type { PublicDoctor } from "@/lib/types";

export const metadata: Metadata = {
  title: "Our Doctors",
  description: "Meet the specialist team at Cosmo Dental Dubai.",
};

export default async function DoctorsPage() {
  const doctors = await publicApiFetch<PublicDoctor[]>("/doctors");

  return (
    <div className="mx-auto max-w-6xl px-6 py-20">
      <SectionHeading
        eyebrow="Our specialists"
        title="Meet the team"
        description="Board-credentialed specialists across cosmetic, orthodontic, and implant dentistry."
      />
      <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {doctors.map((doctor) => (
          <DoctorCard key={doctor.id} doctor={doctor} />
        ))}
      </div>
    </div>
  );
}
