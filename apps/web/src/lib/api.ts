const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string
  ) {
    super(message);
  }
}

/**
 * Calls apps/api with the caller's Supabase access token. apps/web never
 * talks to Postgres directly (see docs/ARCHITECTURE.md) — every CRM read
 * or write goes through this.
 */
export async function apiFetch<T>(
  path: string,
  token: string,
  init?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_URL}/api/v1${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      ...init?.headers,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const error = body?.error;
    throw new ApiError(
      response.status,
      error?.code ?? "unknown_error",
      error?.message ?? `Request to ${path} failed with ${response.status}.`
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

/**
 * POSTs to apps/api's unauthenticated /public/* routes (e.g. the enquiry
 * form). Never cached — publicApiFetch's `revalidate` is a GET-only concern.
 */
export async function publicApiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_URL}/api/v1/public${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  const responseBody = await response.json().catch(() => null);
  if (!response.ok) {
    const error = responseBody?.error;
    throw new ApiError(
      response.status,
      error?.code ?? "unknown_error",
      error?.message ?? `Request to ${path} failed with ${response.status}.`
    );
  }
  return responseBody as T;
}

/**
 * Calls apps/api's unauthenticated /public/* routes — what the marketing
 * site (apps/web/src/app/(site)) renders for anonymous visitors. Never use
 * this for anything CRM/clinic-staff scoped; use apiFetch for that.
 */
export async function publicApiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}/api/v1/public${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
    next: { revalidate: 60 },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const error = body?.error;
    throw new ApiError(
      response.status,
      error?.code ?? "unknown_error",
      error?.message ?? `Request to ${path} failed with ${response.status}.`
    );
  }

  return response.json() as Promise<T>;
}
