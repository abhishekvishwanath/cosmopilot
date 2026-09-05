import { createBrowserClient } from "@supabase/ssr";

/**
 * Supabase client for use in Client Components. Reads the public
 * (browser-safe) project URL and anon key — never the service role key.
 */
export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}
