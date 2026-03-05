import { describe, it, expect } from 'vitest';
import { PersonalityManager } from '../../src/personality/personality-manager.js';
import { createTabulaRasa } from '../../src/personality/types.js';

describe('PersonalityManager', () => {
  it('creates a tabula rasa with neutral trait midpoints', () => {
    const state = createTabulaRasa();
    expect(state.cognitiveStage).toBe('sensorimotor');
    expect(state.cognitiveAge).toBe(0);

    // HEXACO traits start at 0.5
    expect(state.hexaco.sincerity).toBe(0.5);
    expect(state.hexaco.creativity).toBe(0.5);

    // Character starts at 0.0 (not yet developed)
    expect(state.character.empathy).toBe(0.0);

    // Values start at 0.0 (nothing valued yet)
    expect(state.values.stimulation).toBe(0.0);
  });

  it('increments cognitive age and transitions stages', () => {
    const manager = new PersonalityManager(createTabulaRasa());

    // Initial state
    expect(manager.getState().cognitiveStage).toBe('sensorimotor');

    // Move to preoperational (age >= 50)
    for (let i = 0; i < 50; i++) manager.incrementAge();
    expect(manager.getState().cognitiveStage).toBe('preoperational');
    expect(manager.getState().cognitiveAge).toBe(50);

    // Move to concrete operational (age >= 200)
    for (let i = 0; i < 150; i++) manager.incrementAge();
    expect(manager.getState().cognitiveStage).toBe('concrete_operational');

    // Move to formal operational (age >= 500)
    for (let i = 0; i < 300; i++) manager.incrementAge();
    expect(manager.getState().cognitiveStage).toBe('formal_operational');
  });

  it('applies personality updates and clamps to [0, 1]', () => {
    const manager = new PersonalityManager(createTabulaRasa());

    // Positive delta
    manager.applyUpdate({ creativity: 0.3 }, 'hexaco');
    expect(manager.getState().hexaco.creativity).toBeCloseTo(0.8);

    // Negative delta
    manager.applyUpdate({ creativity: -0.5 }, 'hexaco');
    expect(manager.getState().hexaco.creativity).toBeCloseTo(0.3);

    // Clamping at 1.0
    manager.applyUpdate({ creativity: 2.0 }, 'hexaco');
    expect(manager.getState().hexaco.creativity).toBe(1.0);

    // Clamping at 0.0
    manager.applyUpdate({ creativity: -5.0 }, 'hexaco');
    expect(manager.getState().hexaco.creativity).toBe(0.0);
  });

  it('applies character updates (starting from 0)', () => {
    const manager = new PersonalityManager(createTabulaRasa());

    manager.applyUpdate({ empathy: 0.2, compassion: 0.15 }, 'character');
    const state = manager.getState();
    expect(state.character.empathy).toBeCloseTo(0.2);
    expect(state.character.compassion).toBeCloseTo(0.15);
  });

  it('applies value updates', () => {
    const manager = new PersonalityManager(createTabulaRasa());

    manager.applyUpdate({ stimulation: 0.4, hedonism: 0.3 }, 'values');
    const state = manager.getState();
    expect(state.values.stimulation).toBeCloseTo(0.4);
    expect(state.values.hedonism).toBeCloseTo(0.3);
  });

  it('loads a full personality state', () => {
    const manager = new PersonalityManager(createTabulaRasa());
    const customState = createTabulaRasa();
    customState.cognitiveAge = 100;
    customState.cognitiveStage = 'preoperational';
    customState.hexaco.creativity = 0.9;

    manager.loadState(customState);
    const loaded = manager.getState();
    expect(loaded.cognitiveAge).toBe(100);
    expect(loaded.cognitiveStage).toBe('preoperational');
    expect(loaded.hexaco.creativity).toBe(0.9);
  });

  it('returns a deep copy of state (mutations do not leak)', () => {
    const manager = new PersonalityManager(createTabulaRasa());
    const state = manager.getState();
    state.hexaco.creativity = 1.0;

    // Internal state should be unaffected
    expect(manager.getState().hexaco.creativity).toBe(0.5);
  });
});
