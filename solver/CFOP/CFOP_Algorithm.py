"""
SYSC3010 - Pi Cubed Rubik's Cube Solver
Solver Algorithm Pi - CFOP Algorithm Module
Group L3-G6

Author: Luke Grundy

Location: CFOP/CFOP_Algorithm.py

Implementation of the CFOP solving algorithm
(Cross, F2L, OLL, PLL)

Orientation Convention:
    White = 'U' colour (top face in solved state).
    The cross is solved on the D layer so that F2L algorithms using U/R/F moves
    do not disturb already-placed cross edges.

Stage Summary:
    Cross  - Per-edge BFS, solving DF → DR → DB → DL while preserving earlier edges.
    F2L    - Lookup-table per slot (FR → FL → BR → BL). Each table is built from
             composite move sequences guaranteed to preserve the D-cross and every
             previously solved slot.
    OLL    - 20-bit U-layer pattern matched against a pre-built lookup table;
             4 AUF rotations tried.
    PLL    - 12-element side top-row pattern matched against a pre-built lookup
             table; 4 AUF rotations tried, followed by a final AUF alignment.
"""

import copy
import os

from Cube_Algorithm import CubeAlgorithm
from CFOP import CFOP_Tables


class CFOP_Algorithm(CubeAlgorithm):
    """
    CFOP Rubik's Cube solving algorithm.

    All lookup tables are built once at construction time.  The cube state
    passed in must be a list of 54 sticker strings in face order:
        U(0-8), R(9-17), F(18-26), D(27-35), L(36-44), B(45-53)
    """

    def __init__(self, cube_state):
        super().__init__(cube_state)
        self._working = copy.deepcopy(cube_state)

        # Extended move map (adds r, f, M, x, y and their inverses)
        self._all_moves = CFOP_Tables.build_extra_moves()

        # JSON files live in CFOP/Algorithms/ relative to this file
        here     = os.path.dirname(os.path.abspath(__file__))
        alg_dir  = os.path.join(here, "Algorithms")
        oll_path = os.path.join(alg_dir, "OLL.json")
        pll_path = os.path.join(alg_dir, "PLL.json")

        # OLL and PLL pattern → (auf_moves, alg_moves)
        self._oll_lut = CFOP_Tables.build_oll_lookup(oll_path, self._all_moves)
        self._pll_lut = CFOP_Tables.build_pll_lookup(pll_path, self._all_moves)

        # F2L lookup tables - one per slot, built in solve order so that each
        # table's composite moves preserve every previously solved slot.
        self._f2l_lut = {
            "FR": CFOP_Tables.build_f2l_table(
                "FR", "DFR", "FR", preserve_slots=[]
            ),
            "FL": CFOP_Tables.build_f2l_table(
                "FL", "DFL", "FL", preserve_slots=["FR"]
            ),
            "BR": CFOP_Tables.build_f2l_table(
                "BR", "DBR", "BR", preserve_slots=["FR", "FL"]
            ),
            "BL": CFOP_Tables.build_f2l_table(
                "BL", "DBL", "BL", preserve_slots=["FR", "FL", "BR"]
            ),
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def solve(self) -> list:
        """Execute all four CFOP stages and return the full move list."""
        self._working = copy.deepcopy(self.cube_state)

        self.solve_cross()
        self.solve_f2l()
        self.solve_oll()
        self.solve_pll()

        return self.moves

    # ------------------------------------------------------------------
    # Stage 1 – Cross
    # ------------------------------------------------------------------

    def solve_cross(self, orientation_face=None):
        """
        Solve the D-layer white cross.

        Edges are solved in the order DF → DR → DB → DL.  Each edge is placed
        with a BFS that preserves all previously solved edges.

        The orientation_face parameter is accepted for API compatibility but is
        not used; the cross orientation is always fixed to the D face.
        """
        print("Solving Cross...")

        solved_edges = []
        for slot in ["DF", "DR", "DB", "DL"]:
            alg = CFOP_Tables.solve_cross_edge(self._working, slot, solved_edges)
            if alg:
                self._working = CFOP_Tables.apply_alg(self._working, alg)
                self.moves.extend(alg)
            solved_edges.append(slot)

    # ------------------------------------------------------------------
    # Stage 2 – F2L
    # ------------------------------------------------------------------

    def solve_f2l(self, orientation_face=None):
        """
        Solve the first two layers using per-slot lookup tables.

        Processes corner-edge pairs in order: FR → FL → BR → BL.  Each pair is
        looked up by its piece signature (where the pieces currently are and how
        they are oriented).  If the exact signature is not in the table, up to
        three AUF (U, U', U2) rotations are tried before the slot is skipped.

        Skipping a slot is safer than applying a wrong algorithm; it means a
        subsequent OLL/PLL step will simply not recognise the pattern rather
        than silently corrupting an already-solved layer.
        """
        print("Solving F2L...")

        # Maps each slot to the colour set of its target corner and edge pieces
        slot_pieces = {
            "FR": ("DFR", "FR"),
            "FL": ("DFL", "FL"),
            "BR": ("DBR", "BR"),
            "BL": ("DBL", "BL"),
        }

        for slot in ["FR", "FL", "BR", "BL"]:
            if CFOP_Tables.F2L_SLOT_SOLVED[slot](self._working):
                continue

            corner_colours, edge_colours = slot_pieces[slot]
            sig = CFOP_Tables.get_piece_signature(
                self._working, corner_colours, edge_colours
            )
            lut = self._f2l_lut[slot]

            if sig in lut:
                alg = lut[sig]
                self._working = CFOP_Tables.apply_alg(self._working, alg)
                self.moves.extend(alg)
            else:
                # Try AUF rotations to find a matching signature
                found = False
                for auf in [["U"], ["U'"], ["U2"]]:
                    test     = CFOP_Tables.apply_alg(self._working, auf)
                    test_sig = CFOP_Tables.get_piece_signature(
                        test, corner_colours, edge_colours
                    )
                    if test_sig in lut:
                        full_alg      = auf + lut[test_sig]
                        self._working = CFOP_Tables.apply_alg(self._working, full_alg)
                        self.moves.extend(full_alg)
                        found = True
                        break
                if not found:
                    continue

    # ------------------------------------------------------------------
    # Stage 3 – OLL
    # ------------------------------------------------------------------

    def solve_oll(self, orientation_face=None):
        """
        Orient the last layer.

        Computes a 20-bit fingerprint of the U-face and surrounding side top-row
        stickers and looks it up in the pre-built OLL table.  All four AUF
        rotations (none, U, U', U2) are tried before concluding the layer is
        already oriented.
        """
        print("Solving OLL...")

        # Skip if U face is already fully oriented
        if all(self._working[i] == "U" for i in range(9)):
            return

        pat = CFOP_Tables.get_oll_pattern(self._working)

        if pat in self._oll_lut:
            auf_moves, alg = self._oll_lut[pat]
            full          = auf_moves + alg
            self._working = CFOP_Tables.apply_alg(self._working, full, self._all_moves)
            self.moves.extend(full)
        else:
            for auf in [["U"], ["U'"], ["U2"]]:
                test = CFOP_Tables.apply_alg(self._working, auf, self._all_moves)
                pat  = CFOP_Tables.get_oll_pattern(test)
                if pat in self._oll_lut:
                    auf_moves, alg = self._oll_lut[pat]
                    full          = auf + auf_moves + alg
                    self._working = CFOP_Tables.apply_alg(
                        self._working, full, self._all_moves
                    )
                    self.moves.extend(full)
                    return

    # ------------------------------------------------------------------
    # Stage 4 – PLL
    # ------------------------------------------------------------------

    def solve_pll(self, orientation_face=None):
        """
        Permute the last layer.

        Computes a 12-element fingerprint of the side top-row stickers and looks
        it up in the pre-built PLL table.  After applying the algorithm a final
        AUF is performed to align the last layer with the rest of the cube
        (all four side-face top rows show a uniform colour).
        """
        print("Solving PLL...")

        pat = CFOP_Tables.get_pll_pattern(self._working)

        if pat in self._pll_lut:
            auf_moves, alg = self._pll_lut[pat]
            full          = auf_moves + alg
            self._working = CFOP_Tables.apply_alg(self._working, full, self._all_moves)
            self.moves.extend(full)
        else:
            for auf in [["U"], ["U'"], ["U2"]]:
                test = CFOP_Tables.apply_alg(self._working, auf, self._all_moves)
                pat  = CFOP_Tables.get_pll_pattern(test)
                if pat in self._pll_lut:
                    auf_moves, alg = self._pll_lut[pat]
                    full          = auf + auf_moves + alg
                    self._working = CFOP_Tables.apply_alg(
                        self._working, full, self._all_moves
                    )
                    self.moves.extend(full)
                    break

        # Final AUF: rotate U layer until all faces show a uniform top row
        for auf in [["U"], ["U'"], ["U2"]]:
            test = CFOP_Tables.apply_alg(self._working, auf, self._all_moves)
            if self._is_solved(test):
                self._working = test
                self.moves.extend(auf)
                return

    # ------------------------------------------------------------------
    # Internal utility
    # ------------------------------------------------------------------

    def _is_solved(self, state):
        """Return True if every face of the cube shows a single uniform colour."""
        for face_start in range(0, 54, 9):
            if len(set(state[face_start:face_start + 9])) != 1:
                return False
        return True