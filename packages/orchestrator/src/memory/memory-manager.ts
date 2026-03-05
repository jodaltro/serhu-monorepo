import { WorkingMemory } from './working-memory.js';
import { ArchivalMemory } from './archival-memory.js';
import { RelationalMemory } from './relational-memory.js';
import type { MemoryConfig, MemoryEntry } from './types.js';

/**
 * MemoryManager — the MemGPT-like orchestration layer for memory.
 *
 * Acts as an operating system for the Ser's memory:
 * - Working Memory (RAM): immediate context buffer
 * - Archival Memory (Disk/Qdrant): long-term semantic search via vectors
 * - Relational Memory (Supabase): structured persistent records & personality
 *
 * When working memory overflows, evicted entries are automatically consolidated
 * into both archival (vector) and relational (structured) storage.
 */
export class MemoryManager {
  readonly working: WorkingMemory;
  readonly archival: ArchivalMemory;
  readonly relational: RelationalMemory;

  private serId: string;

  constructor(serId: string, config: MemoryConfig) {
    this.serId = serId;
    this.working = new WorkingMemory(config.workingMemoryLimit);
    this.archival = new ArchivalMemory(
      config.qdrantUrl,
      config.qdrantApiKey,
      config.qdrantCollectionName,
    );
    this.relational = new RelationalMemory(config.supabaseUrl, config.supabaseKey);
  }

  /**
   * Initialize the memory system (ensure vector collection exists).
   */
  async initialize(): Promise<void> {
    await this.archival.ensureCollection();
  }

  /**
   * Process a new memory entry through the memory pipeline:
   * 1. Add to working memory
   * 2. If evicted entries exist, consolidate them to long-term storage
   */
  async processMemory(
    entry: MemoryEntry,
    embedding?: number[],
  ): Promise<{ evicted: MemoryEntry[] }> {
    const evicted = this.working.push(entry);

    // Consolidate evicted entries to long-term storage
    for (const evictedEntry of evicted) {
      await this.consolidate(evictedEntry, embedding);
    }

    return { evicted };
  }

  /**
   * Search across all memory tiers.
   * 1. First search working memory (fast, exact match)
   * 2. Then search archival memory (semantic similarity via vectors)
   */
  async recall(
    query: string,
    queryVector?: number[],
    topK: number = 5,
  ): Promise<{
    workingResults: MemoryEntry[];
    archivalResults: Array<{ id: string | number; score: number; payload: Record<string, unknown> | null | undefined }>;
  }> {
    const workingResults = this.working.search(query);

    let archivalResults: Array<{ id: string | number; score: number; payload: Record<string, unknown> | null | undefined }> = [];
    if (queryVector) {
      archivalResults = await this.archival.search(queryVector, topK);
    }

    return { workingResults, archivalResults };
  }

  /**
   * Force-flush all working memory entries to long-term storage.
   */
  async flush(): Promise<number> {
    const entries = this.working.clear();
    for (const entry of entries) {
      await this.consolidate(entry);
    }
    return entries.length;
  }

  /**
   * Consolidate a single memory entry into relational storage.
   * If an embedding is provided, also store in archival (vector) memory.
   */
  private async consolidate(
    entry: MemoryEntry,
    embedding?: number[],
  ): Promise<void> {
    // Always save to relational storage
    await this.relational.insertMemory({
      ser_id: this.serId,
      memory_type: entry.type,
      content: entry.content,
      metadata: entry.metadata ?? {},
    });

    // If embedding provided, also save to archival/vector storage
    if (embedding) {
      await this.archival.store(entry.id, embedding, {
        content: entry.content,
        type: entry.type,
        timestamp: entry.timestamp,
        ser_id: this.serId,
      });
    }
  }
}
