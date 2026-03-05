import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import type { RelationalRecord, PersonalityRecord } from './types.js';

/**
 * Relational Memory — structured persistent storage backed by Supabase.
 *
 * Stores structured memory records (episodic, semantic, causal, entity)
 * and the personality state snapshots for each Ser.
 */
export class RelationalMemory {
  private client: SupabaseClient;

  constructor(url: string, key: string) {
    this.client = createClient(url, key);
  }

  // ── Memory Records ──────────────────────────────────────────

  /**
   * Insert a memory record into the memories table.
   */
  async insertMemory(record: RelationalRecord): Promise<RelationalRecord> {
    const { data, error } = await this.client
      .from('memories')
      .insert(record)
      .select()
      .single();
    if (error) throw new Error(`Supabase insertMemory: ${error.message}`);
    return data as RelationalRecord;
  }

  /**
   * Retrieve memories for a Ser, optionally filtered by type.
   */
  async getMemories(
    serId: string,
    type?: RelationalRecord['memory_type'],
    limit: number = 50,
  ): Promise<RelationalRecord[]> {
    let query = this.client
      .from('memories')
      .select('*')
      .eq('ser_id', serId)
      .order('created_at', { ascending: false })
      .limit(limit);

    if (type) {
      query = query.eq('memory_type', type);
    }

    const { data, error } = await query;
    if (error) throw new Error(`Supabase getMemories: ${error.message}`);
    return (data ?? []) as RelationalRecord[];
  }

  // ── Personality State ───────────────────────────────────────

  /**
   * Upsert the personality state for a Ser.
   */
  async savePersonality(record: PersonalityRecord): Promise<PersonalityRecord> {
    const { data, error } = await this.client
      .from('personality_states')
      .upsert(record, { onConflict: 'ser_id' })
      .select()
      .single();
    if (error) throw new Error(`Supabase savePersonality: ${error.message}`);
    return data as PersonalityRecord;
  }

  /**
   * Load the personality state for a Ser.
   */
  async loadPersonality(serId: string): Promise<PersonalityRecord | null> {
    const { data, error } = await this.client
      .from('personality_states')
      .select('*')
      .eq('ser_id', serId)
      .maybeSingle();
    if (error) throw new Error(`Supabase loadPersonality: ${error.message}`);
    return data as PersonalityRecord | null;
  }

  /**
   * Health check — verifies the connection to Supabase.
   */
  async healthCheck(): Promise<boolean> {
    // A simple query to verify connectivity
    const { error } = await this.client.from('memories').select('id').limit(1);
    // Table might not exist yet, but if we get a connection error it's different
    return !error || error.code === '42P01'; // 42P01 = table does not exist
  }
}
