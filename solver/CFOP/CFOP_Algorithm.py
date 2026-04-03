"""
SYSC3010 - Pi Cubed | Group L3-G6 | Author: Luke Grundy

CFOP solving algorithm (Cross, F2L, OLL, PLL). All lookup tables are built at
construction time. The cross is solved on the D layer so that F2L algorithms
using U/R/F moves do not disturb already-placed cross edges.
"""

import copy
import os

from Cube_Algorithm import CubeAlgorithm
from CFOP import CFOP_Tables


class CFOP_Algorithm(CubeAlgorithm):

    def __init__(self, cube_state):
        super().__init__(cube_state)
        self._working = copy.deepcopy(cube_state)

        self._all_moves = CFOP_Tables.build_extra_moves()

        here = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(here, "Algorithms"),
            here,
            os.path.dirname(here),
        ]

        def _find_json(name):
            for d in candidates:
                p = os.path.join(d, name)
                if os.path.isfile(p):
                    return p
            return os.path.join(candidates[0], name)

        self._oll_lut = CFOP_Tables.build_oll_lookup(
            _find_json("OLL.json"), self._all_moves
        )

        self._f2l_lut = {
            "FR": CFOP_Tables.build_f2l_table(
                "FR", "DFR", "FR", preserve_slots=[], max_depth=5
            ),
            "FL": CFOP_Tables.build_f2l_table(
                "FL", "DFL", "FL", preserve_slots=["FR"], max_depth=5
            ),
            "BR": CFOP_Tables.build_f2l_table(
                "BR", "DBR", "BR", preserve_slots=["FR", "FL"], max_depth=5
            ),
            "BL": CFOP_Tables.build_f2l_table(
                "BL", "DBL", "BL", preserve_slots=["FR", "FL", "BR"], max_depth=5
            ),
        }

        self._pll_lut = CFOP_Tables.build_pll_lookup(
            _find_json("PLL.json"), self._all_moves
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def solve(self) -> list:
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
        """Solve the D-layer white cross. Edges solved in order DF→DR→DB→DL,
        each via BFS that preserves all previously solved edges."""
        print("Solving Cross...")

        solved_edges = []
        for slot in ["DF", "DR", "DB", "DL"]:
            alg = CFOP_Tables.solve_cross_edge(self._working, slot, solved_edges)
            if alg:
                self._working = CFOP_Tables._apply_std(self._working, alg)
                self.moves.extend(alg)
            solved_edges.append(slot)

    # ------------------------------------------------------------------
    # Stage 2 – F2L
    # ------------------------------------------------------------------

    def solve_f2l(self, orientation_face=None):
        """Solve corner-edge pairs FR→FL→BR→BL via per-slot lookup tables.
        Up to three AUF rotations are tried on a cache miss before skipping."""
        print("Solving F2L...")

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
                self._working = CFOP_Tables._apply_std(self._working, alg)
                self.moves.extend(alg)
            else:
                found = False
                for auf in [["U"], ["U'"], ["U2"]]:
                    test = CFOP_Tables._apply_std(self._working, auf)
                    test_sig = CFOP_Tables.get_piece_signature(
                        test, corner_colours, edge_colours
                    )
                    if test_sig in lut:
                        full_alg = auf + lut[test_sig]
                        self._working = CFOP_Tables._apply_std(self._working, full_alg)
                        self.moves.extend(full_alg)
                        found = True
                        break
                if not found:
                    continue

    # ------------------------------------------------------------------
    # Stage 3 – OLL
    # ------------------------------------------------------------------

    def solve_oll(self, orientation_face=None):
        """Orient the last layer using a permutation-invariant orientation key.
        Up to three AUF rotations are tried on a cache miss."""
        print("Solving OLL...")

        if all(self._working[i] == "U" for i in range(9)):
            return

        key = CFOP_Tables.get_oll_orient_key(self._working)
        if key in self._oll_lut:
            alg = self._oll_lut[key]
            self._working = CFOP_Tables._apply_ext(self._working, alg, self._all_moves)
            self.moves.extend(alg)
            return

        for auf in [["U"], ["U'"], ["U2"]]:
            test = CFOP_Tables._apply_std(self._working, auf)
            k2 = CFOP_Tables.get_oll_orient_key(test)
            if k2 in self._oll_lut:
                alg = auf + self._oll_lut[k2]
                self._working = CFOP_Tables._apply_ext(
                    self._working, alg, self._all_moves
                )
                self.moves.extend(alg)
                return

    # ------------------------------------------------------------------
    # Stage 4 – PLL
    # ------------------------------------------------------------------

    def solve_pll(self, orientation_face=None):
        """Permute the last layer using the pre-built PLL table (all 16
        pre/post AUF combinations are stored, so no retry is needed)."""
        print("Solving PLL...")

        pattern = CFOP_Tables.get_pll_pattern(self._working)
        alg = self._pll_lut.get(pattern)
        if alg:
            self._working = CFOP_Tables._apply_ext(self._working, alg, self._all_moves)
            self.moves.extend(alg)
