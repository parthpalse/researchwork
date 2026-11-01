import { createClient, SupabaseClient } from '@supabase/supabase-js';

// Login settings come from the backend (/api/config), so the same build works in
// every environment. The publishable key is public by design.
let client: SupabaseClient | null = null;

export async function getSupabase(): Promise<SupabaseClient> {
  if (client) return client;
  const response = await fetch('/api/config');
  if (!response.ok) throw new Error('Could not reach the server.');
  const config = await response.json();
  if (!config.supabase_url || !config.supabase_publishable_key) {
    throw new Error('Login is not configured on the server yet.');
  }
  client = createClient(config.supabase_url, config.supabase_publishable_key);
  return client;
}

export async function authHeaders(): Promise<Record<string, string>> {
  if (!client) return {};
  const { data } = await client.auth.getSession();
  const token = data.session?.access_token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// fetch() for our API with the signed-in user's token attached
export async function apiFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const headers = { ...(init.headers as Record<string, string> | undefined), ...(await authHeaders()) };
  return fetch(input, { ...init, headers });
}
