"use client";

import { usePathname } from "next/navigation";
import { useState } from "react";

import { ApiError, publicApiPost } from "@/lib/api";
import { getAttribution, getOrCreateAnonymousId, setStoredLeadId } from "@/lib/tracking";
import type { PublicLeadCreate, PublicLeadResult } from "@/lib/types";

const CONTACT_METHODS = ["Call", "WhatsApp", "Email"] as const;

export interface TreatmentOption {
  id: string;
  name: string;
}

interface FormState {
  name: string;
  phone: string;
  email: string;
  treatmentId: string;
  preferredTime: string;
  contactMethod: (typeof CONTACT_METHODS)[number];
  consent: boolean;
}

const EMPTY_FORM: FormState = {
  name: "",
  phone: "",
  email: "",
  treatmentId: "",
  preferredTime: "",
  contactMethod: "WhatsApp",
  consent: false,
};

export function AppointmentForm({
  treatments,
  defaultTreatmentId,
}: {
  treatments: TreatmentOption[];
  defaultTreatmentId?: string;
}) {
  const pathname = usePathname();
  const [form, setForm] = useState<FormState>({
    ...EMPTY_FORM,
    treatmentId: defaultTreatmentId ?? "",
  });
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [result, setResult] = useState<PublicLeadResult | null>(null);

  function validate(): boolean {
    const next: Partial<Record<keyof FormState, string>> = {};
    if (form.name.trim().length < 2) next.name = "Please enter your full name.";
    if (form.phone.trim().length < 7) next.phone = "Please enter a valid phone number.";
    if (!form.consent) next.consent = "Consent is required so we can contact you.";
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSubmitError(null);
    if (!validate()) return;

    setSubmitting(true);
    const attribution = getAttribution();
    const payload: PublicLeadCreate = {
      name: form.name.trim(),
      phone: form.phone.trim(),
      email: form.email.trim() || null,
      treatment_id: form.treatmentId || null,
      preferred_time: form.preferredTime.trim() || null,
      contact_method: form.contactMethod,
      consent: form.consent,
      source: attribution.source ?? "website",
      campaign: attribution.campaign,
      landing_page: pathname,
      anonymous_id: getOrCreateAnonymousId(),
    };

    try {
      const created = await publicApiPost<PublicLeadResult>("/leads", payload);
      setStoredLeadId(created.id);
      setResult(created);
    } catch (error) {
      setSubmitError(
        error instanceof ApiError
          ? error.message
          : "Something went wrong sending your enquiry. Please try WhatsApp instead."
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (result) {
    return (
      <div className="rounded-2xl border border-gold bg-gold-soft/40 p-8 text-center">
        <h3 className="font-serif text-2xl text-charcoal">Thank you, {form.name.split(" ")[0]}.</h3>
        <p className="mt-2 text-sm text-charcoal-soft">
          We&apos;ve got your enquiry. Our AI concierge — bottom right — can answer questions
          right now, and our team will follow up shortly too.
        </p>
        <button
          type="button"
          onClick={() => {
            setForm({ ...EMPTY_FORM, treatmentId: defaultTreatmentId ?? "" });
            setResult(null);
          }}
          className="mt-5 text-sm font-medium text-gold-dark hover:underline"
        >
          Submit another enquiry
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      <div>
        <label htmlFor="name" className="text-sm font-medium text-charcoal">
          Full name
        </label>
        <input
          id="name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          className="mt-1 w-full rounded-lg border border-ivory-soft bg-white px-4 py-2.5 text-charcoal focus:border-gold focus:outline-none"
          placeholder="Jane Doe"
        />
        {errors.name && <p className="mt-1 text-xs text-red-600">{errors.name}</p>}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="phone" className="text-sm font-medium text-charcoal">
            Phone / WhatsApp number
          </label>
          <input
            id="phone"
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
            className="mt-1 w-full rounded-lg border border-ivory-soft bg-white px-4 py-2.5 text-charcoal focus:border-gold focus:outline-none"
            placeholder="+971 5X XXX XXXX"
          />
          {errors.phone && <p className="mt-1 text-xs text-red-600">{errors.phone}</p>}
        </div>
        <div>
          <label htmlFor="email" className="text-sm font-medium text-charcoal">
            Email <span className="text-charcoal-soft">(optional)</span>
          </label>
          <input
            id="email"
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="mt-1 w-full rounded-lg border border-ivory-soft bg-white px-4 py-2.5 text-charcoal focus:border-gold focus:outline-none"
            placeholder="jane@example.com"
          />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="treatment" className="text-sm font-medium text-charcoal">
            Treatment interest
          </label>
          <select
            id="treatment"
            value={form.treatmentId}
            onChange={(e) => setForm({ ...form, treatmentId: e.target.value })}
            className="mt-1 w-full rounded-lg border border-ivory-soft bg-white px-4 py-2.5 text-charcoal focus:border-gold focus:outline-none"
          >
            <option value="">Not sure yet</option>
            {treatments.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="preferredTime" className="text-sm font-medium text-charcoal">
            Preferred time
          </label>
          <input
            id="preferredTime"
            value={form.preferredTime}
            onChange={(e) => setForm({ ...form, preferredTime: e.target.value })}
            className="mt-1 w-full rounded-lg border border-ivory-soft bg-white px-4 py-2.5 text-charcoal focus:border-gold focus:outline-none"
            placeholder="e.g. weekday mornings"
          />
        </div>
      </div>

      <fieldset>
        <legend className="text-sm font-medium text-charcoal">Preferred contact method</legend>
        <div className="mt-2 flex gap-4">
          {CONTACT_METHODS.map((method) => (
            <label key={method} className="flex items-center gap-2 text-sm text-charcoal-soft">
              <input
                type="radio"
                name="contactMethod"
                checked={form.contactMethod === method}
                onChange={() => setForm({ ...form, contactMethod: method })}
                className="accent-gold"
              />
              {method}
            </label>
          ))}
        </div>
      </fieldset>

      <div>
        <label className="flex items-start gap-2 text-sm text-charcoal-soft">
          <input
            type="checkbox"
            checked={form.consent}
            onChange={(e) => setForm({ ...form, consent: e.target.checked })}
            className="mt-0.5 accent-gold"
          />
          <span>
            I agree to be contacted by Cosmo Dental Dubai by phone, WhatsApp, or email about my
            enquiry.
          </span>
        </label>
        {errors.consent && <p className="mt-1 text-xs text-red-600">{errors.consent}</p>}
      </div>

      {submitError && (
        <p className="rounded-lg bg-red-50 px-4 py-2.5 text-sm text-red-700">{submitError}</p>
      )}

      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-full bg-charcoal px-6 py-3 text-sm font-medium text-ivory transition-colors hover:bg-emerald disabled:cursor-not-allowed disabled:opacity-60"
      >
        {submitting ? "Sending..." : "Request a consultation"}
      </button>
    </form>
  );
}
