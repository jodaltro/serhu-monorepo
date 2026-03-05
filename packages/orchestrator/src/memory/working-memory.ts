import type { MemoryEntry } from './types.js';

/**
 * Working Memory — the short-term context buffer.
 *
 * Modeled after MemGPT's "main context" / RAM concept.
 * Holds the most recent memories in a FIFO buffer with a configurable limit.
 * When capacity is exceeded, the oldest entries are evicted and returned
 * so the MemoryManager can consolidate them into longer-term storage.
 */
export class WorkingMemory {
  private buffer: MemoryEntry[] = [];
  private readonly limit: number;

  constructor(limit: number = 50) {
    this.limit = limit;
  }

  /**
   * Add a new memory entry. Returns evicted entries if buffer overflows.
   */
  push(entry: MemoryEntry): MemoryEntry[] {
    this.buffer.push(entry);
    const evicted: MemoryEntry[] = [];
    while (this.buffer.length > this.limit) {
      evicted.push(this.buffer.shift()!);
    }
    return evicted;
  }

  /**
   * Get all entries currently in working memory.
   */
  getAll(): MemoryEntry[] {
    return [...this.buffer];
  }

  /**
   * Search working memory for entries containing the query string.
   */
  search(query: string): MemoryEntry[] {
    const lower = query.toLowerCase();
    return this.buffer.filter((e) => e.content.toLowerCase().includes(lower));
  }

  /**
   * Current number of entries in the buffer.
   */
  get size(): number {
    return this.buffer.length;
  }

  /**
   * Clear working memory, returning all evicted entries.
   */
  clear(): MemoryEntry[] {
    const evicted = [...this.buffer];
    this.buffer = [];
    return evicted;
  }
}
