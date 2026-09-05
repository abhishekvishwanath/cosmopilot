import Link from "next/link";

import type { PublicDoctor } from "@/lib/types";

import { AvatarInitials } from "./avatar-initials";

export function DoctorCard({ doctor }: { doctor: PublicDoctor }) {
  return (
    <Link
      href={`/doctors/${doctor.slug}`}
      className="flex flex-col items-center rounded-2xl border border-ivory-soft bg-white p-6 text-center transition-colors hover:border-gold"
    >
      <AvatarInitials name={doctor.name} size={72} />
      <h3 className="mt-4 font-serif text-lg text-charcoal">{doctor.name}</h3>
      {doctor.title && <p className="text-sm text-gold-dark">{doctor.title}</p>}
      {doctor.specialties && doctor.specialties.length > 0 && (
        <p className="mt-2 text-xs text-charcoal-soft">{doctor.specialties.join(" · ")}</p>
      )}
    </Link>
  );
}
