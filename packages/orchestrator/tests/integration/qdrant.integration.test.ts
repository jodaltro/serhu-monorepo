import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { ArchivalMemory } from '../../src/memory/archival-memory.js';
import { hasQdrantCredentials, testConfig } from './test-config.js';

const COLLECTION = `serhu_test_${Date.now()}`;

/**
 * Integration tests for ArchivalMemory with a real Qdrant instance.
 * Tests are skipped when QDRANT_URL/QDRANT_API_KEY env vars are not set
 * or when the Qdrant instance is unreachable.
 */
describe.runIf(hasQdrantCredentials())('ArchivalMemory (Qdrant integration)', () => {
  let archival: ArchivalMemory;
  let reachable = false;

  beforeAll(async () => {
    archival = new ArchivalMemory(
      testConfig.qdrantUrl,
      testConfig.qdrantApiKey,
      COLLECTION,
      4, // small vector size for testing
    );
    try {
      await archival.ensureCollection();
      reachable = true;
    } catch (err) {
      console.warn('Qdrant unreachable — integration tests will be skipped:', (err as Error).message);
    }
  });

  afterAll(async () => {
    if (reachable) {
      await archival.deleteCollection();
    }
  });

  it('creates and verifies collection', async ({ skip }) => {
    if (!reachable) skip();
    const info = await archival.getInfo();
    expect(info.pointsCount).toBe(0);
  });

  it('stores and retrieves a vector', async ({ skip }) => {
    if (!reachable) skip();
    const vector = [0.1, 0.2, 0.3, 0.4];
    await archival.store('mem-1', vector, {
      content: 'The user loves music',
      type: 'semantic',
      ser_id: 'test-ser',
    });

    await new Promise((r) => setTimeout(r, 500));

    const info = await archival.getInfo();
    expect(info.pointsCount).toBe(1);
  });

  it('performs semantic search with similarity scoring', async ({ skip }) => {
    if (!reachable) skip();
    await archival.store('mem-2', [0.9, 0.8, 0.7, 0.6], {
      content: 'The user is a software engineer',
      type: 'semantic',
      ser_id: 'test-ser',
    });

    await new Promise((r) => setTimeout(r, 500));

    const results = await archival.search([0.1, 0.2, 0.3, 0.4], 5);
    expect(results.length).toBeGreaterThanOrEqual(1);
    expect(results[0].score).toBeGreaterThan(0);
    expect(results[0].payload).toBeDefined();
  });

  it('deletes a vector', async ({ skip }) => {
    if (!reachable) skip();
    await archival.delete('mem-1');
    await new Promise((r) => setTimeout(r, 500));

    const info = await archival.getInfo();
    expect(info.pointsCount).toBe(1); // only mem-2 remains
  });
});
