import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";

/**
 * Server Component / Route Handler helper: returns the current session's
 * access token (for calling apps/api) and user, redirecting to /login if
 * there isn't one. proxy.ts already gates /admin/**, this is defense in
 * depth for any Server Component that reads the session directly.
 */
export async function requireSession() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) {
    redirect("/login");
  }

  return { accessToken: session.access_token, user: session.user };
}
