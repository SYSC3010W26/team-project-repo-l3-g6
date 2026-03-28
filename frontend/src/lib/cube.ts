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
  "U": [6, 3, 0, 7, 4, 1, 8, 5, 2, 45, 46, 47, 12, 13, 14, 15, 16, 17, 9, 10, 11, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 18, 19, 20, 39, 40, 41, 42, 43, 44, 36, 37, 38, 48, 49, 50, 51, 52, 53],
  "R": [0, 1, 20, 3, 4, 23, 6, 7, 26, 15, 12, 9, 16, 13, 10, 17, 14, 11, 18, 19, 29, 21, 22, 32, 24, 25, 35, 27, 28, 51, 30, 31, 48, 33, 34, 45, 36, 37, 38, 39, 40, 41, 42, 43, 44, 8, 46, 47, 5, 49, 50, 2, 52, 53],
  "F": [0, 1, 2, 3, 4, 5, 44, 41, 38, 6, 10, 11, 7, 13, 14, 8, 16, 17, 24, 21, 18, 25, 22, 19, 26, 23, 20, 15, 12, 9, 30, 31, 32, 33, 34, 35, 36, 37, 27, 39, 40, 28, 42, 43, 29, 45, 46, 47, 48, 49, 50, 51, 52, 53],
  "D": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 24, 25, 26, 18, 19, 20, 21, 22, 23, 42, 43, 44, 33, 30, 27, 34, 31, 28, 35, 32, 29, 36, 37, 38, 39, 40, 41, 51, 52, 53, 45, 46, 47, 48, 49, 50, 15, 16, 17],
  "L": [53, 1, 2, 50, 4, 5, 47, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 0, 19, 20, 3, 22, 23, 6, 25, 26, 18, 28, 29, 21, 31, 32, 24, 34, 35, 42, 39, 36, 43, 40, 37, 44, 41, 38, 45, 46, 33, 48, 49, 30, 51, 52, 27],
  "B": [11, 14, 17, 3, 4, 5, 6, 7, 8, 9, 10, 35, 12, 13, 34, 15, 16, 33, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 36, 39, 42, 2, 37, 38, 1, 40, 41, 0, 43, 44, 51, 48, 45, 52, 49, 46, 53, 50, 47]
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
