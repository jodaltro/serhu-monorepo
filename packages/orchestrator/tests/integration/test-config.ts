import { config } from 'dotenv';
import { resolve } from 'path';

// Load .env from repository root
config({ path: resolve(import.meta.dirname, '../../../../.env') });

/**
 * Test configuration loaded from environment variables.
 * Integration tests are skipped when credentials are not available.
 */
export const testConfig = {
  qdrantUrl: process.env.QDRANT_URL ?? '',
  qdrantApiKey: process.env.QDRANT_API_KEY ?? '',
  supabaseUrl: process.env.SUPABASE_URL ?? '',
  supabaseKey: process.env.SUPABASE_KEY ?? '',
};

export function hasQdrantCredentials(): boolean {
  return Boolean(testConfig.qdrantUrl && testConfig.qdrantApiKey);
}

export function hasSupabaseCredentials(): boolean {
  return Boolean(testConfig.supabaseUrl && testConfig.supabaseKey);
}

export function hasAllCredentials(): boolean {
  return hasQdrantCredentials() && hasSupabaseCredentials();
}
