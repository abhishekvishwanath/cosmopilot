import Link from "next/link";

import type { PublicClinic } from "@/lib/types";

export function SiteFooter({ clinic }: { clinic: PublicClinic }) {
  const location = clinic.locations[0];

  return (
    <footer className="border-t border-ivory-soft bg-emerald text-ivory">
      <div className="mx-auto grid max-w-6xl gap-10 px-6 py-14 sm:grid-cols-3">
        <div>
          <p className="font-serif text-lg">{clinic.name}</p>
          {clinic.description && (
            <p className="mt-3 text-sm text-ivory/70">{clinic.description}</p>
          )}
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ivory/60">
            Explore
          </p>
          <ul className="mt-3 space-y-2 text-sm text-ivory/80">
            <li>
              <Link href="/treatments" className="hover:text-ivory">
                Treatments
              </Link>
            </li>
            <li>
              <Link href="/doctors" className="hover:text-ivory">
                Doctors
              </Link>
            </li>
            <li>
              <Link href="/#faq" className="hover:text-ivory">
                FAQs
              </Link>
            </li>
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ivory/60">
            Contact
          </p>
          <ul className="mt-3 space-y-2 text-sm text-ivory/80">
            {clinic.primary_phone && <li>{clinic.primary_phone}</li>}
            {clinic.email && <li>{clinic.email}</li>}
            {location && (
              <li>
                {location.address}, {location.city}
              </li>
            )}
          </ul>
        </div>
      </div>
      <div className="border-t border-ivory/10">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-6 py-5 text-xs text-ivory/50 sm:flex-row sm:items-center sm:justify-between">
          <p>
            Demo prototype — {clinic.name} is a fictional clinic. Content is illustrative, not
            real clinical or pricing information.
          </p>
          <Link href="/login" className="hover:text-ivory/80">
            Clinic staff login
          </Link>
        </div>
      </div>
    </footer>
  );
}
