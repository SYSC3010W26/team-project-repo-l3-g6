/**
 * Rubik's Cube state transition logic.
 * State string format: 54 characters, WCA order: U R F D L B.
 * Each face is a 3x3 grid (9 stickers), indexed 0-8.
 */

export const SOLVED_STATE = 'UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB';

/**
 * Precomputed move permutations for a 54-char state string.
 * Each array contains the source indices for the target indices after the move.
 * i.e. newState[i] = oldState[MOVE_MAP[move][i]]
 */
const MOVE_MAP: Record<string, number[]> = {
  "U": [2, 5, 8, 1, 4, 7, 0, 3, 6, 45, 46, 47, 12, 13, 14, 15, 16, 17, 9, 10, 11, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 18, 19, 20, 39, 40, 41, 42, 43, 44, 36, 37, 38, 48, 49, 50, 51, 52, 53],
  "D": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 24, 25, 26, 18, 19, 20, 21, 22, 23, 42, 43, 44, 29, 32, 35, 28, 31, 34, 27, 30, 33, 36, 37, 38, 39, 40, 41, 51, 52, 53, 45, 46, 47, 48, 49, 50, 15, 16, 17],
  "L": [47, 1, 2, 50, 4, 5, 53, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 6, 19, 20, 3, 22, 23, 0, 25, 26, 24, 28, 29, 21, 31, 32, 18, 34, 35, 42, 39, 36, 43, 40, 37, 44, 41, 38, 45, 46, 27, 48, 49, 30, 51, 52, 33],
  "R": [0, 1, 26, 3, 4, 23, 6, 7, 20, 15, 12, 9, 16, 13, 10, 17, 14, 11, 18, 19, 35, 21, 22, 32, 24, 25, 29, 27, 28, 45, 30, 31, 48, 33, 34, 51, 36, 37, 38, 39, 40, 41, 42, 43, 44, 2, 46, 47, 5, 49, 50, 8, 52, 53],
  "F": [44, 41, 38, 3, 4, 5, 6, 7, 8, 0, 10, 11, 1, 13, 14, 2, 16, 17, 24, 21, 18, 25, 22, 19, 26, 23, 20, 27, 28, 29, 30, 31, 32, 15, 12, 9, 36, 37, 33, 39, 40, 34, 42, 43, 35, 45, 46, 47, 48, 49, 50, 51, 52, 53],
  "B": [0, 1, 2, 3, 4, 5, 11, 14, 17, 9, 10, 29, 12, 13, 28, 15, 16, 27, 18, 19, 20, 21, 22, 23, 24, 25, 26, 36, 39, 42, 30, 31, 32, 33, 34, 35, 8, 37, 38, 7, 40, 41, 6, 43, 44, 51, 48, 45, 52, 49, 46, 53, 50, 47]
};

/**
 * Applies a single WCA move to a cube state.
 * @param stateString 54-char state string
 * @param move Single move (e.g. "U", "R'", "F2")
 * @returns Updated 54-char state string
 */
export function applyMove(stateString: string, move: string): string {
  if (stateString.length !== 54) return stateString;

  const face = move[0];
  const modifier = move.length > 1 ? move[1] : '';
  const perm = MOVE_MAP[face];
  
  if (!perm) return stateString;

  let state = stateString.split('');
  const times = modifier === "'" ? 3 : modifier === '2' ? 2 : 1;

  for (let t = 0; t < times; t++) {
    const nextState = new Array(54);
    for (let i = 0; i < 54; i++) {
      nextState[i] = state[perm[i]];
    }
    state = nextState;
  }

  return state.join('');
}

/**
 * Returns the inverse of a single WCA move.
 * @param move Single move (e.g. "U", "R'", "F2")
 * @returns Inverse move
 */
export function getInverseMove(move: string): string {
  if (!move) return '';
  if (move.endsWith("'")) return move.slice(0, -1);
  if (move.endsWith("2")) return move;
  return move + "'";
}
