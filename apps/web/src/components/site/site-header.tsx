import Link from "next/link";

export function SiteHeader({ clinicName }: { clinicName: string }) {
  return (
    <header className="sticky top-0 z-30 border-b border-ivory-soft bg-ivory/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="font-serif text-lg text-charcoal">
          {clinicName}
        </Link>
        <nav className="hidden items-center gap-6 text-sm text-charcoal-soft sm:flex">
          <Link href="/treatments" className="hover:text-charcoal">
            Treatments
          </Link>
          <Link href="/doctors" className="hover:text-charcoal">
            Doctors
          </Link>
          <Link href="/#reviews" className="hover:text-charcoal">
            Reviews
          </Link>
          <Link href="/#faq" className="hover:text-charcoal">
            FAQs
          </Link>
          <Link href="/#location" className="hover:text-charcoal">
            Location
          </Link>
        </nav>
        <Link
          href="/#book"
          className="rounded-full bg-charcoal px-5 py-2 text-sm font-medium text-ivory transition-colors hover:bg-emerald"
        >
          Book Consultation
        </Link>
      </div>
    </header>
  );
}
