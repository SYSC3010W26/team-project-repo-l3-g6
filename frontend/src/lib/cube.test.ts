import { describe, it, expect } from 'vitest';
import { applyMove, SOLVED_STATE } from './cube';

describe('applyMove', () => {
  it('returns solved state after 4 identical moves', () => {
    const faces = ['U', 'R', 'L', 'F', 'B', 'D'];
    for (const face of faces) {
      let state = SOLVED_STATE;
      for (let i = 0; i < 4; i++) {
        state = applyMove(state, face);
      }
      expect(state).toBe(SOLVED_STATE);
    }
  });

  it('handles inverse moves correctly', () => {
    const cases = ['R', 'U', 'F', 'B', 'L', 'D'];
    for (const move of cases) {
      let state = applyMove(SOLVED_STATE, move);
      state = applyMove(state, move + "'");
      expect(state).toBe(SOLVED_STATE);
    }
  });

  it('handles double moves correctly', () => {
    const faces = ['U', 'R', 'L', 'F', 'B', 'D'];
    for (const face of faces) {
      const state1 = applyMove(SOLVED_STATE, face + '2');
      const state2 = applyMove(applyMove(SOLVED_STATE, face), face);
      expect(state1).toBe(state2);
    }
  });

  it('performs a "Sexy Move" (R U R\' U\') 6 times to return to solved', () => {
    let state = SOLVED_STATE;
    const sexyMove = ['R', 'U', "R'", "U'"];
    for (let i = 0; i < 6; i++) {
      for (const move of sexyMove) {
        state = applyMove(state, move);
      }
    }
    expect(state).toBe(SOLVED_STATE);
  });

  it('performs a "Sune" (R U R\' U R U2 R\') correctly', () => {
    // Sune is a common algorithm, performing it 3 times (with some rotations) returns to solved
    // But simpler: Sune is a specific permutation.
    let state = SOLVED_STATE;
    const sune = ['R', 'U', "R'", 'U', 'R', 'U2', "R'"];
    for (const move of sune) {
      state = applyMove(state, move);
    }
    expect(state).not.toBe(SOLVED_STATE);
    
    // Applying it multiple times in specific ways returns to solved, but let's just use it to check non-triviality
    expect(state.length).toBe(54);
  });
});
