import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { MemoryManager } from '../../src/memory/memory-manager.js';
import { PersonalityManager, createTabulaRasa } from '../../src/personality/index.js';
import type { MemoryEntry } from '../../src/memory/types.js';
import { hasAllCredentials, testConfig } from './test-config.js';

const COLLECTION = `serhu_flow_test_${Date.now()}`;
const SER_ID = `flow-test-ser-${Date.now()}`;

/**
 * Full orchestration flow integration test.
 * Tests the complete memory pipeline: working → archival + relational,
 * combined with personality evolution.
 */
describe.runIf(hasAllCredentials())('Orchestrator full flow (integration)', () => {
  let manager: MemoryManager;
  let personality: PersonalityManager;
  let reachable = false;

  beforeAll(async () => {
    manager = new MemoryManager(SER_ID, {
      workingMemoryLimit: 3, // small limit to trigger evictions
      qdrantUrl: testConfig.qdrantUrl,
      qdrantApiKey: testConfig.qdrantApiKey,
      qdrantCollectionName: COLLECTION,
      supabaseUrl: testConfig.supabaseUrl,
      supabaseKey: testConfig.supabaseKey,
    });
    try {
      await manager.initialize();
      reachable = true;
    } catch (err) {
      console.warn('External services unreachable — integration tests will be skipped:', (err as Error).message);
    }
    personality = new PersonalityManager(createTabulaRasa());
  });

  afterAll(async () => {
    if (reachable) {
      await manager.archival.deleteCollection();
    }
  });

  it('processes memories through the full pipeline (working → archival + relational)', async ({ skip }) => {
    if (!reachable) skip();
    const entries: MemoryEntry[] = [
      { id: 'f1', content: 'User said: I love stargazing', timestamp: new Date().toISOString(), type: 'episodic' },
      { id: 'f2', content: 'User feels peaceful at night', timestamp: new Date().toISOString(), type: 'semantic' },
      { id: 'f3', content: 'Stargazing makes user happy because it reminds them of childhood', timestamp: new Date().toISOString(), type: 'causal' },
    ];

    // Process first 3 entries — no eviction (limit is 3)
    for (const entry of entries) {
      const result = await manager.processMemory(entry);
      expect(result.evicted).toHaveLength(0);
    }
    expect(manager.working.size).toBe(3);

    // Process a 4th entry — triggers eviction of the first
    const fourthEntry: MemoryEntry = {
      id: 'f4',
      content: 'User identifies as an INFP personality type',
      timestamp: new Date().toISOString(),
      type: 'entity',
    };
    const result = await manager.processMemory(fourthEntry);
    expect(result.evicted).toHaveLength(1);
    expect(result.evicted[0].content).toContain('stargazing');
  });

  it('searches across working memory', async ({ skip }) => {
    if (!reachable) skip();
    const { workingResults } = await manager.recall('night');
    expect(workingResults.length).toBeGreaterThanOrEqual(1);
    expect(workingResults[0].content).toContain('night');
  });

  it('stores vectors in archival memory and searches them', async ({ skip }) => {
    if (!reachable) skip();
    const vector = [0.5, 0.3, 0.8, 0.1];
    await manager.archival.store('vec-1', vector, {
      content: 'User loves astronomy',
      type: 'semantic',
      ser_id: SER_ID,
    });
    await new Promise((r) => setTimeout(r, 500));

    const { archivalResults } = await manager.recall('astronomy', [0.5, 0.3, 0.8, 0.1], 3);
    expect(archivalResults.length).toBeGreaterThanOrEqual(1);
    expect(archivalResults[0].score).toBeGreaterThan(0);
  });

  it('evolves personality through interaction', ({ skip }) => {
    if (!reachable) skip();
    personality.applyUpdate({ creativity: 0.1, inquisitiveness: 0.05 }, 'hexaco');
    personality.applyUpdate({ empathy: 0.15, compassion: 0.1 }, 'character');
    personality.applyUpdate({ stimulation: 0.2, universalismNature: 0.15 }, 'values');

    personality.incrementAge();

    const state = personality.getState();
    expect(state.hexaco.creativity).toBeCloseTo(0.6);
    expect(state.character.empathy).toBeCloseTo(0.15);
    expect(state.values.stimulation).toBeCloseTo(0.2);
    expect(state.cognitiveAge).toBe(1);
    expect(state.cognitiveStage).toBe('sensorimotor');
  });

  it('flushes working memory to long-term storage', async ({ skip }) => {
    if (!reachable) skip();
    const count = await manager.flush();
    expect(count).toBe(3); // remaining entries in working memory
    expect(manager.working.size).toBe(0);
  });
});
