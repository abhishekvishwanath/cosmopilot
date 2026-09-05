import { ConciergeLauncher } from "@/components/site/concierge-launcher";
import { SiteFooter } from "@/components/site/site-footer";
import { SiteHeader } from "@/components/site/site-header";
import { WhatsAppButton } from "@/components/site/whatsapp-button";
import { publicApiFetch } from "@/lib/api";
import type { PublicClinic } from "@/lib/types";

export default async function SiteLayout({ children }: { children: React.ReactNode }) {
  const clinic = await publicApiFetch<PublicClinic>("/clinic");

  return (
    <div className="flex flex-1 flex-col bg-ivory">
      <SiteHeader clinicName={clinic.name} />
      <main className="flex-1">{children}</main>
      <SiteFooter clinic={clinic} />
      {clinic.primary_phone && <WhatsAppButton phone={clinic.primary_phone} />}
      <ConciergeLauncher clinicName={clinic.name} />
    </div>
  );
}
