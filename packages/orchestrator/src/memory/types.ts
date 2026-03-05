/**
 * Represents a memory entry across all memory tiers.
 */
export interface MemoryEntry {
  id: string;
  content: string;
  timestamp: string;
  type: 'episodic' | 'semantic' | 'causal' | 'entity';
  metadata?: Record<string, unknown>;
}

/**
 * Configuration for the memory system.
 */
export interface MemoryConfig {
  workingMemoryLimit: number;  // max entries in working memory buffer
  qdrantUrl: string;
  qdrantApiKey: string;
  qdrantCollectionName: string;
  supabaseUrl: string;
  supabaseKey: string;
}

/**
 * Record stored in Supabase for structured relational memory.
 */
export interface RelationalRecord {
  id?: string;
  ser_id: string;
  memory_type: MemoryEntry['type'];
  content: string;
  metadata: Record<string, unknown>;
  created_at?: string;
}

/**
 * The personality snapshot stored in Supabase.
 */
export interface PersonalityRecord {
  id?: string;
  ser_id: string;
  state: Record<string, unknown>;
  updated_at?: string;
}
