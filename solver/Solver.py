"""
SYSC3010 - Pi Cubed | Group L3-G6 | Author: Luke Grundy

Public interface between the solver and the rest of the Pi Cubed system.

Cube state format: 54-character string of face letters U R F D L B, read
left-to-right top-to-bottom per face in order U R F D L B. Solved state:
    "UUUUUUUUURRRRRRRRFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"

Public API:
    load_state(state_string)
        Load a scanned cube state from a 54-character string.
        Validates length, characters, and per-face counts.
        Raises ValueError on malformed input.

    select_algorithm(name)
        Select the solving algorithm by name (default: CFOP).
        Raises ValueError for unsupported names.

    solve()
        Run the selected algorithm on the loaded state.
        Returns a space-separated move string, e.g. "R U R' F".
        Returns "" if the cube is already solved.
        Raises CubeNotSolvableError if the state is physically impossible (detected at the end of the solving process).

    scramble(length=25)
        Reset to solved, apply a random length-move scramble,
        and return the scramble as a move string. The string
        can be forwarded to the motor pi.

    get_state_string()
        Return the current cube state as a 54-character string.

    is_solved()
        Return True if the current cube state is solved.
"""

import random
from Algorithm_Selector import AlgorithmSelector
from Cube_State import Cube


VALID_FACES = set("URFDLB")
SCRAMBLE_MOVES = ["R","R'","R2","U","U'","U2","F","F'","F2","L","L'","L2","B","B'","B2",]


class CubeNotSolvableError(Exception):
    """Raised when the solver cannot find a valid solution.

    Indicates the scanned cube state is physically impossible to solve.
    """


class Solver:

    def __init__(self):
        self._cube = Cube()
        self._algorithm = None
        self._alg_name = "CFOP"

    def load_state(self, state_string):
        """Load the cube from a 54-character face-letter string (U R F D L B).

        Raises ValueError if the string length, characters, or face counts are wrong.
        """
        if len(state_string) != 54:  # check length
            raise ValueError(
                f"State string must be exactly 54 characters, got {len(state_string)}."
            )

        invalid = set(state_string) - VALID_FACES  # check for invalid characters
        if invalid:
            raise ValueError(
                f"Invalid characters: {sorted(invalid)}. Only U R F D L B are allowed."
            )

        wrong = {
            f: state_string.count(f) for f in VALID_FACES if state_string.count(f) != 9
        }  # check for correct face counts
        if wrong:
            raise ValueError(
                f"Each face letter must appear exactly 9 times. Incorrect counts: {wrong}"
            )

        self._cube.set_cube_state(list(state_string))
        self._algorithm = None

    def select_algorithm(self, name):
        """Select the solving algorithm by name.

        Raises ValueError for unknown names.
        """
        name = name.upper()
        if name not in AlgorithmSelector.ALGORITHMS:
            raise ValueError(
                f"Unknown algorithm '{name}'. Supported: {', '.join(sorted(AlgorithmSelector.ALGORITHMS))}."
            )
        self._alg_name = name
        self._algorithm = None

    def solve(self):
        """Run the selected algorithm and return the solution as a move string.

        Returns an empty string if already solved. Raises CubeNotSolvableError
        if the cube state is physically impossible (solution not found).
        """
        if self._cube.is_solved():
            return ""

        selector = AlgorithmSelector(self._cube.state[:], self._alg_name)
        self._algorithm = selector.get_algorithm()
        moves = self._algorithm.solve()

        result = Cube()
        result.set_cube_state(self._cube.state[:])
        result.apply_sequence(moves)
        if not result.is_solved():
            raise CubeNotSolvableError(
                "Could not fully solve the cube — scanned state may be physically impossible. "
                f"Partial solution: {' '.join(moves) if moves else '(none)'}"
            )

        return " ".join(moves)

    def scramble(self, length=25):
        """Reset to solved, apply a random scramble, and return the scramble move string.

        No two consecutive moves share the same face. The returned string can be
        passed to the motor pi to physically reproduce the scramble.
        """
        self._cube = Cube()
        self._algorithm = None

        moves, last_face = [], None
        for _ in range(length):
            move = random.choice(SCRAMBLE_MOVES)
            while move[0] == last_face:
                move = random.choice(SCRAMBLE_MOVES)
            moves.append(move)
            last_face = move[0]

        self._cube.apply_sequence(moves)
        return " ".join(moves)

    def get_state_string(self):
        """Return the current cube state as a 54-character string."""
        return self._cube.cube_to_string()

    def is_solved(self):
        """Return True if the current cube state is solved."""
        return self._cube.is_solved()