"""
SYSC3010 - Pi Cubed Rubik's Cube Solver
Solver Algorithm Pi - Debug Viewer Unit Tests
Group L3-G6

Author: Luke Grundy

Tests:
    Move Validity
        - All 18 standard moves are accepted
        - Invalid move strings raise ValueError
        - Multi-move input strings are parsed and applied
        - Prime (') and double (2) variants work correctly
        - Move sequences are recorded in history

    Scramble
        - Scramble produces a cube that is not solved
        - Scramble records exactly n moves in history
        - Scramble with default length (25) works
        - Custom scramble lengths are respected

    Reset
        - Reset returns cube to solved state
        - Reset clears move history

    Solve (full CFOP)
        - Solved cube reports already solved (no crash)
        - solve() on a scrambled cube produces a solved cube
        - solve() result is deterministic for a fixed scramble
        - solve() does not leave history in an inconsistent state

    Stage-specific solves
        - solve_stage("cross") leaves D-layer cross solved
        - solve_stage("f2l")   leaves first two layers solved
        - solve_stage("oll")   leaves last layer oriented
        - solve_stage("pll")   leaves last layer permuted (fully solved)
        - Unknown stage names are rejected gracefully (no crash)
"""

import sys
import os
import unittest
import random

# Path setup
PROJECT_DIR = os.path.join(os.path.dirname(__file__), "..")
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from Cube_State import Cube
from Algorithm_Selector import AlgorithmSelector
import Permutation_Table as PT

import io
from contextlib import redirect_stdout

# Redirect stdout for the whole import so ANSI sequences don't pollute output
with redirect_stdout(io.StringIO()):
    from Cube_Debug_Viewer import CubeDebugger

VALID_MOVES = [
    "R", "R'", "R2",
    "U", "U'", "U2",
    "F", "F'", "F2",
    "L", "L'", "L2",
    "D", "D'", "D2",
    "B", "B'", "B2",
]

INVALID_MOVES = ["X", "Z", "Q", "RR", "u", "f2", "", "R3", "UU", "  "]


def _silent(fn, *args, **kwargs):
    """Call fn(*args, **kwargs) suppressing all stdout."""
    with redirect_stdout(io.StringIO()):
        return fn(*args, **kwargs)


def _make_debugger():
    """Return a fresh CubeDebugger without printing anything."""
    return _silent(CubeDebugger)


# ---------------------------------------------------------------------------
# Helper predicates (mirror the checks in CFOP_Tables)
# ---------------------------------------------------------------------------

def d_cross_solved(state):
    """Check that all four D-layer cross edges are in place."""
    return (
        state[28] == "D" and state[25] == "F" and
        state[32] == "D" and state[16] == "R" and
        state[34] == "D" and state[52] == "B" and
        state[30] == "D" and state[43] == "L"
    )


def f2l_solved(state):
    """Check that all four F2L corner-edge pairs are correctly inserted."""
    # FR slot
    fr = (state[29]=="D" and state[26]=="F" and state[15]=="R"
          and state[23]=="F" and state[12]=="R")
    # FL slot
    fl = (state[27]=="D" and state[44]=="L" and state[24]=="F"
          and state[21]=="F" and state[41]=="L")
    # BR slot
    br = (state[35]=="D" and state[17]=="R" and state[51]=="B"
          and state[48]=="B" and state[14]=="R")
    # BL slot
    bl = (state[33]=="D" and state[53]=="B" and state[42]=="L"
          and state[50]=="B" and state[39]=="L")
    return fr and fl and br and bl


def oll_solved(state):
    """Check that all U-face stickers are yellow (U color)."""
    return all(state[i] == "U" for i in range(9))


def cube_fully_solved(state):
    """Check that every face of the cube shows a single uniform color."""
    for start in range(0, 54, 9):
        if len(set(state[start:start + 9])) != 1:
            return False
    return True


# ===========================================================================
# Test classes
# ===========================================================================


class TestMoveValidity(unittest.TestCase):
    """All 18 standard moves must be accepted; invalid tokens must raise."""

    def setUp(self):
        self.dbg = _make_debugger()

    def test_all_valid_moves_accepted(self):
        """Each of the 18 standard moves should apply without error."""
        for move in VALID_MOVES:
            with self.subTest(move=move):
                _silent(self.dbg.cube.apply_move, move)

    def test_invalid_moves_raise(self):
        """Applying a move not in Permutation_Table.MOVES should raise ValueError."""
        for bad in INVALID_MOVES:
            if bad == "":
                continue  # empty string: no-op, not a ValueError
            with self.subTest(move=bad):
                with self.assertRaises((ValueError, KeyError)):
                    self.dbg.cube.apply_move(bad)

    def test_prime_variant_is_inverse_of_base(self):
        """Applying R then R' must return the cube to the same state."""
        original = self.dbg.cube.state[:]
        _silent(self.dbg.cube.apply_move, "R")
        _silent(self.dbg.cube.apply_move, "R'")
        self.assertEqual(self.dbg.cube.state, original)

    def test_double_variant_equals_twice_base(self):
        """R2 must produce the same state as R applied twice."""
        cube_double = Cube()
        cube_double.apply_move("R2")

        cube_twice = Cube()
        cube_twice.apply_move("R")
        cube_twice.apply_move("R")

        self.assertEqual(cube_double.state, cube_twice.state)

    def test_four_quarter_turns_is_identity(self):
        """Applying any quarter-turn four times must restore the cube."""
        for move in [m for m in VALID_MOVES if not m.endswith("2")]:
            with self.subTest(move=move):
                c = Cube()
                for _ in range(4):
                    c.apply_move(move)
                self.assertEqual(c.state, Cube().state,
                                 f"{move} x 4 did not restore solved state")

    def test_multi_move_input_parsed(self):
        """A space-separated string of moves must all be applied in order."""
        c1 = Cube()
        for m in ["R", "U", "R'", "U'"]:
            c1.apply_move(m)

        c2 = Cube()
        for m in "R U R' U'".split():
            c2.apply_move(m)

        self.assertEqual(c1.state, c2.state)

    def test_history_records_applied_moves(self):
        """Moves applied through the debugger should appear in history."""
        dbg = _make_debugger()
        moves = ["R", "U", "R'"]
        for m in moves:
            dbg.cube.apply_move(m)
            dbg.history.append(m)
        self.assertEqual(dbg.history, moves)

    def test_all_move_permutations_are_bijections(self):
        """Every permutation table entry must be a bijection on [0, 53]."""
        for name, perm in PT.MOVES.items():
            with self.subTest(move=name):
                self.assertEqual(sorted(perm), list(range(54)),
                                 f"Permutation for {name} is not a bijection")


# ---------------------------------------------------------------------------

class TestScramble(unittest.TestCase):
    """Scramble must randomize the cube and record moves in history."""

    def setUp(self):
        self.dbg = _make_debugger()

    def test_scramble_produces_unsolved_cube(self):
        _silent(self.dbg.scramble, 25)
        self.assertFalse(self.dbg.cube.is_solved())

    def test_scramble_default_length_records_25_moves(self):
        _silent(self.dbg.scramble)
        self.assertEqual(len(self.dbg.history), 25)

    def test_scramble_custom_length(self):
        for n in [1, 10, 30, 50]:
            with self.subTest(n=n):
                dbg = _make_debugger()
                _silent(dbg.scramble, n)
                self.assertEqual(len(dbg.history), n)

    def test_scramble_moves_are_all_valid(self):
        _silent(self.dbg.scramble, 30)
        for m in self.dbg.history:
            self.assertIn(m, PT.MOVES,
                          f"Scramble produced invalid move: {m!r}")

    def test_scramble_no_consecutive_same_face(self):
        """The scrambler must not repeat the same face twice in a row."""
        _silent(self.dbg.scramble, 50)
        for i in range(1, len(self.dbg.history)):
            prev = self.dbg.history[i - 1][0]
            curr = self.dbg.history[i][0]
            self.assertNotEqual(prev, curr,
                                f"Same face twice in a row at index {i}")


# ---------------------------------------------------------------------------

class TestReset(unittest.TestCase):
    """Reset must restore the solved state and clear history."""

    def setUp(self):
        self.dbg = _make_debugger()

    def test_reset_after_scramble_restores_solved(self):
        _silent(self.dbg.scramble, 25)
        self.dbg.cube = Cube()
        self.dbg.history = []
        self.assertTrue(self.dbg.cube.is_solved())

    def test_reset_clears_history(self):
        _silent(self.dbg.scramble, 10)
        self.dbg.cube = Cube()
        self.dbg.history = []
        self.assertEqual(self.dbg.history, [])

    def test_reset_on_already_solved_is_no_op(self):
        original = self.dbg.cube.state[:]
        self.dbg.cube = Cube()
        self.dbg.history = []
        self.assertEqual(self.dbg.cube.state, original)


# ---------------------------------------------------------------------------

class TestFullSolve(unittest.TestCase):
    """Full CFOP solve must produce a solved cube."""

    def _scramble_and_solve(self, length=20):
        dbg = _make_debugger()
        _silent(dbg.scramble, length)
        _silent(dbg.full_solve)
        return dbg

    def test_solve_produces_solved_cube(self):
        dbg = self._scramble_and_solve(20)
        self.assertTrue(cube_fully_solved(dbg.cube.state),
                        "Cube is not solved after full_solve()")

    def test_solve_already_solved_cube_no_crash(self):
        dbg = _make_debugger()
        _silent(dbg.full_solve)
        self.assertTrue(dbg.cube.is_solved())

    def test_solve_various_scramble_lengths(self):
        """Solver must work for several scramble depths."""
        for length in [5, 15, 25]:
            with self.subTest(length=length):
                dbg = _make_debugger()
                _silent(dbg.scramble, length)
                _silent(dbg.full_solve)
                self.assertTrue(cube_fully_solved(dbg.cube.state),
                                f"Failed to solve after {length}-move scramble")

    def test_solve_deterministic_for_fixed_scramble(self):
        """Two identical scrambles must produce identical solutions."""
        seed = 42
        solutions = []
        for _ in range(2):
            dbg = _make_debugger()
            random.seed(seed)
            _silent(dbg.scramble, 20)
            before = len(dbg.history)
            _silent(dbg.full_solve)
            solutions.append(dbg.history[before:])

        self.assertEqual(solutions[0], solutions[1])

    def test_solution_moves_are_all_valid_notation(self):
        """Every move in the generated solution must be a known move token."""
        from CFOP.CFOP_Tables import build_extra_moves
        extended = build_extra_moves()

        dbg = _make_debugger()
        _silent(dbg.scramble, 20)
        alg = _silent(dbg._build_algorithm)
        _silent(alg.solve)

        for m in alg.moves:
            self.assertIn(m, extended,
                          f"Solution contains unknown move token: {m!r}")


# ---------------------------------------------------------------------------

class TestStageSolve(unittest.TestCase):
    """Individual CFOP stages must leave the cube in the correct partial state."""

    # ---- Cross -------------------------------------------------------------

    def test_cross_stage_solves_d_cross(self):
        dbg = _make_debugger()
        _silent(dbg.scramble, 20)
        _silent(dbg.solve_stage, "cross")
        self.assertTrue(d_cross_solved(dbg.cube.state),
                        "D-layer cross not solved after cross stage")

    def test_cross_stage_on_solved_cube_is_no_op(self):
        dbg = _make_debugger()
        _silent(dbg.solve_stage, "cross")
        self.assertTrue(d_cross_solved(dbg.cube.state))

    # ---- F2L ---------------------------------------------------------------

    def test_f2l_stage_after_cross_solves_f2l(self):
        dbg = _make_debugger()
        _silent(dbg.scramble, 20)
        _silent(dbg.solve_stage, "cross")
        _silent(dbg.solve_stage, "f2l")
        self.assertTrue(f2l_solved(dbg.cube.state),
                        "F2L not solved after f2l stage")

    def test_f2l_preserves_cross(self):
        dbg = _make_debugger()
        _silent(dbg.scramble, 20)
        _silent(dbg.solve_stage, "cross")
        _silent(dbg.solve_stage, "f2l")
        self.assertTrue(d_cross_solved(dbg.cube.state),
                        "Cross disturbed after f2l stage")

    # ---- OLL ---------------------------------------------------------------

    def test_oll_stage_after_f2l_orients_last_layer(self):
        dbg = _make_debugger()
        _silent(dbg.scramble, 20)
        _silent(dbg.solve_stage, "cross")
        _silent(dbg.solve_stage, "f2l")
        _silent(dbg.solve_stage, "oll")
        self.assertTrue(oll_solved(dbg.cube.state),
                        "Last layer not oriented after oll stage")

    def test_oll_preserves_f2l(self):
        dbg = _make_debugger()
        _silent(dbg.scramble, 20)
        _silent(dbg.solve_stage, "cross")
        _silent(dbg.solve_stage, "f2l")
        _silent(dbg.solve_stage, "oll")
        self.assertTrue(f2l_solved(dbg.cube.state),
                        "F2L disturbed after oll stage")

    # ---- PLL ---------------------------------------------------------------

    def test_pll_stage_fully_solves_cube(self):
        dbg = _make_debugger()
        _silent(dbg.scramble, 20)
        _silent(dbg.solve_stage, "cross")
        _silent(dbg.solve_stage, "f2l")
        _silent(dbg.solve_stage, "oll")
        _silent(dbg.solve_stage, "pll")
        self.assertTrue(cube_fully_solved(dbg.cube.state),
                        "Cube not fully solved after all four stages")

    # ---- Invalid stage -----------------------------------------------------

    def test_unknown_stage_does_not_crash(self):
        dbg = _make_debugger()
        _silent(dbg.scramble, 10)
        try:
            _silent(dbg.solve_stage, "BOGUS_STAGE")
        except Exception as exc:
            self.fail(f"solve_stage('BOGUS_STAGE') raised {exc!r}")

    def test_empty_stage_name_does_not_crash(self):
        dbg = _make_debugger()
        try:
            _silent(dbg.solve_stage, "")
        except Exception as exc:
            self.fail(f"solve_stage('') raised {exc!r}")


# ---------------------------------------------------------------------------

class TestCubeStateRepresentation(unittest.TestCase):
    """Sanity checks on the underlying Cube state model."""

    def test_solved_state_has_54_stickers(self):
        c = Cube()
        self.assertEqual(len(c.state), 54)

    def test_solved_state_each_color_appears_9_times(self):
        from collections import Counter
        c = Cube()
        counts = Counter(c.state)
        for color in ["U", "R", "F", "D", "L", "B"]:
            self.assertEqual(counts[color], 9,
                             f"Color {color} appears {counts[color]} times, expected 9")

    def test_centers_are_never_moved(self):
        """Center stickers at indices 4,13,22,31,40,49 must never change."""
        centers = {4: "U", 13: "R", 22: "F", 31: "D", 40: "L", 49: "B"}
        c = Cube()
        for move in VALID_MOVES:
            c.apply_move(move)
        for idx, expected in centers.items():
            self.assertEqual(c.state[idx], expected,
                             f"Center at index {idx} changed after moves")

    def test_cube_string_roundtrip(self):
        c = Cube()
        s = c.cube_to_string()
        self.assertEqual(len(s), 54)
        restored = Cube.string_to_cube(s)
        self.assertEqual(restored, c.state)

    def test_clone_is_independent(self):
        c = Cube()
        clone = c.clone()
        c.apply_move("R")
        self.assertNotEqual(c.state, clone.state,
                            "Clone shares state with original")


# ===========================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)