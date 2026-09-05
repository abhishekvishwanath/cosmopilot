import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { AvatarInitials } from "@/components/site/avatar-initials";
import { SectionHeading } from "@/components/site/section-heading";
import { TreatmentCard } from "@/components/site/treatment-card";
import { ApiError, publicApiFetch } from "@/lib/api";
import type { PublicDoctor, PublicTreatment } from "@/lib/types";

async function getDoctor(slug: string): Promise<PublicDoctor> {
  try {
    return await publicApiFetch<PublicDoctor>(`/doctors/${slug}`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  }
}

function findRelatedTreatments(
  doctor: PublicDoctor,
  treatments: PublicTreatment[]
): PublicTreatment[] {
  if (!doctor.specialties || doctor.specialties.length === 0) return [];
  return treatments.filter((treatment) =>
    doctor.specialties?.some((specialty) => {
      const name = treatment.name.toLowerCase();
      const s = specialty.toLowerCase();
      return name.includes(s) || s.includes(name);
    })
  );
}

export async function generateMetadata(props: PageProps<"/doctors/[slug]">): Promise<Metadata> {
  const { slug } = await props.params;
  const doctor = await getDoctor(slug);
  return {
    title: doctor.name,
    description: doctor.bio ?? doctor.title ?? undefined,
  };
}

export default async function DoctorPage(props: PageProps<"/doctors/[slug]">) {
  const { slug } = await props.params;
  const [doctor, treatments] = await Promise.all([
    getDoctor(slug),
    publicApiFetch<PublicTreatment[]>("/treatments"),
  ]);
  const relatedTreatments = findRelatedTreatments(doctor, treatments);

  return (
    <div>
      <section className="bg-charcoal text-ivory">
        <div className="mx-auto flex max-w-6xl flex-col items-start gap-6 px-6 py-20 sm:flex-row sm:items-center">
          <AvatarInitials name={doctor.name} size={96} />
          <div>
            <h1 className="font-serif text-4xl">{doctor.name}</h1>
            {doctor.title && <p className="mt-1 text-gold">{doctor.title}</p>}
            {doctor.specialties && doctor.specialties.length > 0 && (
              <p className="mt-3 text-sm text-ivory/70">{doctor.specialties.join(" · ")}</p>
            )}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-3xl px-6 py-16">
        {doctor.credentials && (
          <p className="text-sm font-medium text-gold-dark">{doctor.credentials}</p>
        )}
        {doctor.bio && <p className="mt-3 text-charcoal-soft">{doctor.bio}</p>}
      </section>

      {relatedTreatments.length > 0 && (
        <section className="bg-ivory-soft/60">
          <div className="mx-auto max-w-6xl px-6 py-16">
            <SectionHeading eyebrow="Treats" title={`Treatments with ${doctor.name}`} />
            <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {relatedTreatments.map((treatment) => (
                <TreatmentCard key={treatment.id} treatment={treatment} />
              ))}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
