function toWhatsAppHref(phone: string, message: string): string {
  const digitsOnly = phone.replace(/[^\d]/g, "");
  return `https://wa.me/${digitsOnly}?text=${encodeURIComponent(message)}`;
}

export function WhatsAppButton({
  phone,
  treatmentName,
  variant = "floating",
}: {
  phone: string;
  treatmentName?: string;
  variant?: "floating" | "inline";
}) {
  const message = treatmentName
    ? `Hi, I'd like to know more about ${treatmentName}.`
    : "Hi, I'd like to book a consultation.";
  const href = toWhatsAppHref(phone, message);

  if (variant === "inline") {
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center justify-center gap-2 rounded-full border border-emerald px-6 py-3 text-sm font-medium text-emerald transition-colors hover:bg-emerald hover:text-ivory"
      >
        WhatsApp us
      </a>
    );
  }

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      aria-label="Chat with us on WhatsApp"
      className="fixed bottom-6 right-6 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-emerald text-ivory shadow-lg transition-transform hover:scale-105"
    >
      <svg viewBox="0 0 24 24" fill="currentColor" className="h-7 w-7">
        <path d="M12.04 2c-5.52 0-10 4.48-10 10 0 1.76.46 3.46 1.35 4.96L2 22l5.2-1.36a9.96 9.96 0 0 0 4.84 1.24h.01c5.52 0 10-4.48 10-10s-4.49-9.88-10.01-9.88Zm0 18.15h-.01a8.2 8.2 0 0 1-4.18-1.14l-.3-.18-3.09.81.82-3.01-.2-.31a8.15 8.15 0 0 1-1.26-4.32c0-4.51 3.67-8.18 8.19-8.18 4.51 0 8.18 3.67 8.18 8.19 0 4.51-3.68 8.14-8.15 8.14Zm4.48-6.13c-.25-.12-1.45-.72-1.67-.8-.22-.08-.39-.12-.55.12-.16.25-.63.8-.78.96-.14.16-.29.18-.53.06-.25-.12-1.04-.38-1.98-1.22-.73-.65-1.23-1.46-1.37-1.7-.14-.25-.02-.38.11-.5.11-.11.25-.29.37-.43.12-.14.16-.25.25-.41.08-.16.04-.31-.02-.43-.06-.12-.55-1.32-.75-1.81-.2-.48-.4-.41-.55-.42h-.47c-.16 0-.43.06-.65.31-.22.25-.86.84-.86 2.04 0 1.2.88 2.36 1 2.53.12.16 1.73 2.64 4.2 3.7.59.25 1.05.4 1.41.52.59.19 1.13.16 1.56.1.48-.07 1.45-.59 1.65-1.16.2-.57.2-1.06.14-1.16-.06-.11-.22-.17-.47-.29Z" />
      </svg>
    </a>
  );
}
