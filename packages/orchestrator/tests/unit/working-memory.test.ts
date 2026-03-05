import { describe, it, expect } from 'vitest';
import { WorkingMemory } from '../../src/memory/working-memory.js';
import type { MemoryEntry } from '../../src/memory/types.js';

function makeEntry(id: string, content: string): MemoryEntry {
  return {
    id,
    content,
    timestamp: new Date().toISOString(),
    type: 'semantic',
  };
}

describe('WorkingMemory', () => {
  it('stores and retrieves entries', () => {
    const wm = new WorkingMemory(10);
    const entry = makeEntry('1', 'Hello world');
    wm.push(entry);

    expect(wm.size).toBe(1);
    expect(wm.getAll()).toHaveLength(1);
    expect(wm.getAll()[0].content).toBe('Hello world');
  });

  it('evicts oldest entries when exceeding limit', () => {
    const wm = new WorkingMemory(3);

    wm.push(makeEntry('1', 'First'));
    wm.push(makeEntry('2', 'Second'));
    wm.push(makeEntry('3', 'Third'));

    // No eviction yet
    const evicted1 = wm.push(makeEntry('4', 'Fourth'));
    expect(evicted1).toHaveLength(1);
    expect(evicted1[0].content).toBe('First');
    expect(wm.size).toBe(3);

    // Another push evicts the second entry
    const evicted2 = wm.push(makeEntry('5', 'Fifth'));
    expect(evicted2).toHaveLength(1);
    expect(evicted2[0].content).toBe('Second');
  });

  it('searches entries by query string', () => {
    const wm = new WorkingMemory(10);
    wm.push(makeEntry('1', 'The user likes cats'));
    wm.push(makeEntry('2', 'The user works as a developer'));
    wm.push(makeEntry('3', 'Cats are independent animals'));

    const results = wm.search('cats');
    expect(results).toHaveLength(2);
    expect(results[0].content).toContain('cats');
  });

  it('search is case-insensitive', () => {
    const wm = new WorkingMemory(10);
    wm.push(makeEntry('1', 'HELLO WORLD'));

    expect(wm.search('hello')).toHaveLength(1);
    expect(wm.search('HELLO')).toHaveLength(1);
  });

  it('clear empties the buffer and returns all entries', () => {
    const wm = new WorkingMemory(10);
    wm.push(makeEntry('1', 'A'));
    wm.push(makeEntry('2', 'B'));

    const cleared = wm.clear();
    expect(cleared).toHaveLength(2);
    expect(wm.size).toBe(0);
    expect(wm.getAll()).toHaveLength(0);
  });
});
