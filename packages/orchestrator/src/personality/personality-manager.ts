import type { CognitiveStage, PersonalityState } from './types.js';

/**
 * Manages the personality state of a Ser, handling updates
 * and cognitive stage transitions based on interaction history.
 */
export class PersonalityManager {
  private state: PersonalityState;

  constructor(initialState: PersonalityState) {
    this.state = structuredClone(initialState);
  }

  getState(): PersonalityState {
    return structuredClone(this.state);
  }

  /**
   * Increments cognitive age and checks for stage transitions.
   */
  incrementAge(): void {
    this.state.cognitiveAge += 1;
    this.state.cognitiveStage = this.computeStage(this.state.cognitiveAge);
  }

  /**
   * Applies a partial personality update, clamping values to [0, 1].
   */
  applyUpdate(update: Partial<Record<string, number>>, domain: 'hexaco' | 'temperament' | 'character' | 'values'): void {
    const target = this.state[domain] as unknown as Record<string, number>;
    for (const [key, delta] of Object.entries(update)) {
      if (key in target && typeof delta === 'number') {
        target[key] = Math.max(0, Math.min(1, target[key] + delta));
      }
    }
  }

  /**
   * Replaces the full personality state (e.g. when loading from DB).
   */
  loadState(state: PersonalityState): void {
    this.state = structuredClone(state);
  }

  /**
   * Maps interaction count to Piaget cognitive stage.
   */
  private computeStage(age: number): CognitiveStage {
    if (age < 50) return 'sensorimotor';
    if (age < 200) return 'preoperational';
    if (age < 500) return 'concrete_operational';
    return 'formal_operational';
  }
}
