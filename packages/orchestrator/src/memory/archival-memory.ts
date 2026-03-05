import { QdrantClient } from '@qdrant/js-client-rest';

/**
 * Archival Memory — long-term semantic storage backed by Qdrant.
 *
 * Modeled after MemGPT's "archival memory" / Disk concept.
 * Stores vector embeddings of memory entries for semantic retrieval.
 */
export class ArchivalMemory {
  private client: QdrantClient;
  private collectionName: string;
  private vectorSize: number;

  constructor(url: string, apiKey: string, collectionName: string, vectorSize: number = 384) {
    this.client = new QdrantClient({ url, apiKey });
    this.collectionName = collectionName;
    this.vectorSize = vectorSize;
  }

  /**
   * Ensure the collection exists in Qdrant. Creates it if missing.
   */
  async ensureCollection(): Promise<void> {
    const collections = await this.client.getCollections();
    const exists = collections.collections.some((c) => c.name === this.collectionName);
    if (!exists) {
      await this.client.createCollection(this.collectionName, {
        vectors: { size: this.vectorSize, distance: 'Cosine' },
      });
    }
  }

  /**
   * Store a memory vector with its associated payload.
   */
  async store(
    id: string,
    vector: number[],
    payload: Record<string, unknown>,
  ): Promise<void> {
    await this.client.upsert(this.collectionName, {
      points: [{ id, vector, payload }],
    });
  }

  /**
   * Retrieve the top-k most similar memories for a given query vector.
   */
  async search(queryVector: number[], topK: number = 5): Promise<Array<{
    id: string | number;
    score: number;
    payload: Record<string, unknown> | null | undefined;
  }>> {
    const results = await this.client.query(this.collectionName, {
      query: queryVector,
      limit: topK,
      with_payload: true,
    });
    return results.points.map((p) => ({
      id: p.id,
      score: p.score,
      payload: p.payload,
    }));
  }

  /**
   * Delete a memory entry by its ID.
   */
  async delete(id: string): Promise<void> {
    await this.client.delete(this.collectionName, {
      points: [id],
    });
  }

  /**
   * Delete the entire collection (for cleanup / testing).
   */
  async deleteCollection(): Promise<void> {
    try {
      await this.client.deleteCollection(this.collectionName);
    } catch {
      // Collection may not exist
    }
  }

  /**
   * Get collection info (point count, etc.).
   */
  async getInfo(): Promise<{ pointsCount: number }> {
    const info = await this.client.getCollection(this.collectionName);
    return { pointsCount: info.points_count ?? 0 };
  }
}
