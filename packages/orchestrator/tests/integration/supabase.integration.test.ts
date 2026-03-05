import { describe, it, expect, beforeAll } from 'vitest';
import { RelationalMemory } from '../../src/memory/relational-memory.js';
import { hasSupabaseCredentials, testConfig } from './test-config.js';

/**
 * Integration tests for RelationalMemory with a real Supabase instance.
 * Tests are skipped when SUPABASE_URL/SUPABASE_KEY env vars are not set
 * or when the Supabase instance is unreachable.
 */
describe.runIf(hasSupabaseCredentials())('RelationalMemory (Supabase integration)', () => {
  let relational: RelationalMemory;
  let reachable = false;

  beforeAll(async () => {
    relational = new RelationalMemory(testConfig.supabaseUrl, testConfig.supabaseKey);
    try {
      reachable = await relational.healthCheck();
    } catch {
      console.warn('Supabase unreachable — integration tests will be skipped');
    }
  });

  it('performs a health check against Supabase', async ({ skip }) => {
    if (!reachable) skip();
    expect(reachable).toBe(true);
  });

  it('inserts and retrieves a memory record', async ({ skip }) => {
    if (!reachable) skip();
    const record = await relational.insertMemory({
      ser_id: 'integration-test-ser',
      memory_type: 'semantic',
      content: 'The user enjoys learning about philosophy',
      metadata: { source: 'integration-test' },
    });

    expect(record.id).toBeDefined();
    expect(record.content).toBe('The user enjoys learning about philosophy');

    const memories = await relational.getMemories('integration-test-ser', 'semantic');
    expect(memories.length).toBeGreaterThanOrEqual(1);
    expect(memories.some((m) => m.content.includes('philosophy'))).toBe(true);
  });

  it('saves and loads personality state', async ({ skip }) => {
    if (!reachable) skip();
    const saved = await relational.savePersonality({
      ser_id: 'integration-test-ser',
      state: {
        hexaco: { creativity: 0.8, sincerity: 0.7 },
        cognitiveStage: 'preoperational',
        cognitiveAge: 75,
      },
    });

    expect(saved.ser_id).toBe('integration-test-ser');

    const loaded = await relational.loadPersonality('integration-test-ser');
    expect(loaded).not.toBeNull();
    expect((loaded!.state as Record<string, unknown>)['cognitiveStage']).toBe('preoperational');
  });
});
