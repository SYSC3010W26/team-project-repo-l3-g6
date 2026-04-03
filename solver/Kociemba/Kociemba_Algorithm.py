"""
SYSC3010 - Pi Cubed Rubik's Cube Solver
Solver Algorithm Pi - Kociemba Two-Phase Algorithm
Group L3-G6

Author: NOT Luke Grundy

    I DID NOT MAKE THIS CODE. this is an adapted version of the Kociemba two-phase algorithm, modified to be used to demonstraite
    that a user can implement a complex algorithm in a reasonable amount of time.

Location: Kociemba/Kociemba_Algorithm.py

Adapted Kociemba two-phase algorithm restricted to the robot's physical move
set: U, F, L, R, B and their prime/double variants (SAFE15).  The D face
motor is absent, so D moves are never generated.

Two-Phase Overview:
    Phase 1  Reduce to the subgroup G1 = <U, R2, F2, L2, B2> using IDA*
             over three coordinates:
               EO  - edge orientation   (2048 states, 11 edges encoded)
               CO  - corner orientation (2187 states, 7 corners encoded)
               UD  - UD-slice edge set  (495 states, combinatorial number system)

    Phase 2  Solve within G1 using IDA* restricted to {U, U', U2, R2, F2, L2, B2}
             (no D, consistent with SAFE15) over three coordinates:
               CP  - corner permutation  (40320 states)
               EP8 - non-slice edge permutation (40320 states)
               SP  - slice edge permutation (24 states)

Robot Constraint:
    SAFE15 = {U, U', U2, R, R', R2, F, F', F2, L, L', L2, B, B', B2}

Coordinate Notes:
    EO, CO: proper group coordinates — each state maps uniquely under any move.
    UD:     combinatorial number system ranking of which 4 of 12 edge slots
            currently hold UD-slice pieces.  Uses C(c_j, j+1) formula (not
            C(c_j, k-j)) to guarantee collision-free encoding across all
            C(12,4) = 495 subsets.
    CP, EP8, SP: Lehmer-code permutation coordinates.

Implementation:
    Move-transition tables are built once in coordinate space (not state space),
    making IDA* fast enough for interactive use (~10-15 s table build,
    sub-second solves for random scrambles).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import copy
from collections import deque

import Permutation_Table as PT
from Cube_Algorithm import CubeAlgorithm
from Cube_State import Cube


# ---------------------------------------------------------------------------
# Move sets
# ---------------------------------------------------------------------------

SAFE15 = ["U", "U'", "U2", "R", "R'", "R2", "F", "F'", "F2",
          "L", "L'", "L2", "B", "B'", "B2"]

# Phase-2 generators: G1 ∩ SAFE15  (D2 excluded — no D motor).
PHASE2_MOVES = ["U", "U'", "U2", "R2", "F2", "L2", "B2"]

_OPPOSITE = {"U": "D", "D": "U", "R": "L", "L": "R", "F": "B", "B": "F"}


def _redundant(prev, move):
    """True when move is redundant after prev (same face, or opposite faces in wrong canonical order)."""
    if prev is None:
        return False
    pf, mf = prev[0], move[0]
    if pf == mf:
        return True
    if _OPPOSITE.get(pf) == mf and pf > mf:
        return True
    return False


# ---------------------------------------------------------------------------
# Piece definitions  (54-facelet layout)
#   U=0-8, R=9-17, F=18-26, D=27-35, L=36-44, B=45-53
#   Each face: row-major 0-8, centre at index 4.
# ---------------------------------------------------------------------------

# 12 edges: (facelet_A, facelet_B).
# A is the reference sticker for orientation convention.
EDGES = [
    (7, 19),   # UF   0
    (5, 10),   # UR   1
    (1, 46),   # UB   2
    (3, 37),   # UL   3
    (28, 25),  # DF   4
    (32, 16),  # DR   5
    (34, 52),  # DB   6
    (30, 43),  # DL   7
    (23, 12),  # FR   8  (UD-slice)
    (21, 41),  # FL   9  (UD-slice)
    (48, 14),  # BR  10  (UD-slice)
    (50, 39),  # BL  11  (UD-slice)
]

# UD-slice edge piece IDs (indices into EDGES in the solved state).
_SLICE_IDS = {8, 9, 10, 11}

# 8 corners: (U/D sticker, CW-1 sticker, CW-2 sticker).
CORNERS = [
    (8,  9,  20),   # UFR  0
    (6,  18, 38),   # UFL  1
    (2,  45, 11),   # UBR  2
    (0,  36, 47),   # UBL  3
    (29, 26, 15),   # DFR  4
    (27, 44, 24),   # DFL  5
    (35, 17, 51),   # DBR  6
    (33, 42, 53),   # DBL  7
]


# ---------------------------------------------------------------------------
# Solved-state colour maps (built once at module load)
# ---------------------------------------------------------------------------

_solved          = Cube().state
_EDGE_COLOUR_ID  = {frozenset([_solved[a], _solved[b]]): i for i, (a, b) in enumerate(EDGES)}
_CORN_COLOUR_ID  = {frozenset([_solved[u], _solved[c1], _solved[c2]]): i
                    for i, (u, c1, c2) in enumerate(CORNERS)}


# ---------------------------------------------------------------------------
# Combinatorial helpers
# ---------------------------------------------------------------------------

def _comb(n, k):
    """Return C(n, k); 0 for out-of-range inputs."""
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    k = min(k, n - k)
    r = 1
    for i in range(k):
        r = r * (n - i) // (i + 1)
    return r


def _comb_rank(positions):
    """
    Combinatorial number system rank for a sorted k-combination from {0..11}.
    Uses the formula  sum C(c_j, j+1)  which produces a unique integer in
    [0, C(12,k)) with no collisions.
    """
    return sum(_comb(p, j + 1) for j, p in enumerate(sorted(positions)))


def _lehmer(perm, n):
    """Lehmer code (factorial number system) for a permutation of length n."""
    used = [False] * n
    code = 0
    for i in range(n):
        cnt = sum(1 for j in range(perm[i]) if not used[j])
        code = code * (n - i) + cnt
        used[perm[i]] = True
    return code


# ---------------------------------------------------------------------------
# Coordinate extraction
# ---------------------------------------------------------------------------

def _eo(state):
    """
    Edge orientation coordinate: 11-bit integer in [0, 2048).

    An edge is correctly oriented (bit=0) when its U/D-colour sticker faces U/D,
    or for equatorial edges, its F/B-colour sticker faces F/B.
    The 12th edge's orientation is determined by parity and is omitted.
    """
    val = 0
    for a, b in EDGES[:11]:
        sa, sb = state[a], state[b]
        if sa in ("U", "D"):
            flip = 0
        elif sb in ("U", "D"):
            flip = 1
        elif sa in ("F", "B"):
            flip = 0
        else:
            flip = 1
        val = (val << 1) | flip
    return val


def _co(state):
    """
    Corner orientation coordinate: base-3 integer in [0, 2187).

    Encodes the twist of corners 0-6 (7th corner's twist is parity-determined).
    Twist 0: U/D sticker faces U/D.  1: CW twist.  2: CCW twist.
    """
    val = 0
    for u, c1, _ in CORNERS[:7]:
        su = state[u]
        if su in ("U", "D"):
            twist = 0
        elif state[c1] in ("U", "D"):
            twist = 1
        else:
            twist = 2
        val = val * 3 + twist
    return val


def _ud(state):
    """
    UD-slice coordinate: combinatorial number system rank in [0, 495).

    Encodes which 4 of the 12 edge slots currently contain the 4 UD-slice
    pieces (FR, FL, BR, BL).  Piece identity is determined by colour-set
    matching against the solved state.  The combinatorial number system
    C(c_j, j+1) formula guarantees a collision-free encoding.
    """
    perm     = [_EDGE_COLOUR_ID.get(frozenset([state[a], state[b]]), -1)
                for a, b in EDGES]
    pos      = [i for i, pid in enumerate(perm) if pid in _SLICE_IDS]
    return _comb_rank(pos)


def _cp(state):
    """Corner permutation: Lehmer code in [0, 40320)."""
    perm = [_CORN_COLOUR_ID.get(frozenset([state[u], state[c1], state[c2]]), i)
            for i, (u, c1, c2) in enumerate(CORNERS)]
    return _lehmer(perm, 8)


def _ep8(state):
    """Non-slice edge permutation: Lehmer code in [0, 40320) for edges 0-7."""
    ref  = [frozenset([_solved[a], _solved[b]]) for a, b in EDGES[:8]]
    perm = []
    for a, b in EDGES[:8]:
        cs = frozenset([state[a], state[b]])
        try:
            perm.append(ref.index(cs))
        except ValueError:
            perm.append(len(perm))  # out-of-place slice edge
    return _lehmer(perm, 8)


def _sp(state):
    """Slice edge permutation: Lehmer code in [0, 24) for edges 8-11."""
    ref  = [frozenset([_solved[a], _solved[b]]) for a, b in EDGES[8:]]
    perm = []
    for a, b in EDGES[8:]:
        cs = frozenset([state[a], state[b]])
        try:
            perm.append(ref.index(cs))
        except ValueError:
            perm.append(len(perm))
    return _lehmer(perm, 4)


# ---------------------------------------------------------------------------
# Coordinate-space move-transition table builder
# ---------------------------------------------------------------------------

def _build_move_table(coord_fn, n_states, move_list):
    """
    Build move-transition table: table[coord][move_index] -> new_coord.

    Uses BFS from the solved state to discover all reachable coordinates,
    computing transitions by applying moves to representative states.
    Unreachable coordinates default to -1.
    """
    solved  = Cube().state[:]
    start_c = coord_fn(solved)
    table   = [[-1] * len(move_list) for _ in range(n_states)]
    visited = {start_c: solved}
    queue   = deque([(solved, start_c)])

    while queue:
        state, c = queue.popleft()
        for mi, m in enumerate(move_list):
            ns  = PT.apply_move(state, PT.MOVES[m])
            nc  = coord_fn(ns)
            table[c][mi] = nc
            if nc not in visited:
                visited[nc] = ns
                queue.append((ns, nc))

    return table


# ---------------------------------------------------------------------------
# Coordinate-space pruning table builder (bytearray for speed)
# ---------------------------------------------------------------------------

def _build_pruning_table(mt_a, n_a, mt_b, n_b, move_list, goal_a, goal_b, max_depth):
    """
    BFS backward from the goal in coordinate space.

    Returns a bytearray of length n_a * n_b where entry [a*n_b + b] holds the
    minimum number of moves to reach (goal_a, goal_b) from (a, b).
    Entries that are never reached are set to 255 (used as infinity).
    """
    table        = bytearray(b'\xff' * (n_a * n_b))
    start_idx    = goal_a * n_b + goal_b
    table[start_idx] = 0
    queue        = deque([(goal_a, goal_b, 0)])

    while queue:
        a, b, d = queue.popleft()
        if d >= max_depth:
            continue
        for mi in range(len(move_list)):
            na = mt_a[a][mi]
            nb = mt_b[b][mi]
            if na < 0:
                na = a
            if nb < 0:
                nb = b
            idx = na * n_b + nb
            if table[idx] == 255:
                table[idx] = d + 1
                queue.append((na, nb, d + 1))

    return table, n_b


# ---------------------------------------------------------------------------
# Kociemba Algorithm class
# ---------------------------------------------------------------------------

class Kociemba_Algorithm(CubeAlgorithm):
    """
    Adapted Kociemba two-phase Rubik's Cube solving algorithm.

    Restricted to SAFE15 (no D moves) to match the robot's physical move set.
    All transition and pruning tables are built at construction time in
    coordinate space.

    Typical performance:
        Table construction: ~10-15 s (one-time, at instantiation).
        Solve time per scramble: under 1 s.
        Solution length: 18-28 moves for random scrambles.
    """

    _MAX_PHASE1 = 12
    _MAX_PHASE2 = 20

    def __init__(self, cube_state):
        super().__init__(cube_state)
        self._working = copy.deepcopy(cube_state)
        self._build_tables()

    # ------------------------------------------------------------------
    # Table construction
    # ------------------------------------------------------------------

    def _build_tables(self):
        """Build all coordinate transition and pruning tables."""
        print("Kociemba: building coordinate tables...")

        solved = Cube().state[:]
        self._goal_eo  = _eo(solved)
        self._goal_co  = _co(solved)
        self._goal_ud  = _ud(solved)
        self._goal_cp  = _cp(solved)
        self._goal_ep8 = _ep8(solved)
        self._goal_sp  = _sp(solved)

        # Phase-1 move tables (SAFE15, 15 moves)
        print("  Phase 1 move tables...")
        self._mt_eo  = _build_move_table(_eo,  2048,  SAFE15)
        self._mt_co  = _build_move_table(_co,  2187,  SAFE15)
        self._mt_ud  = _build_move_table(_ud,  495,   SAFE15)

        # Phase-2 move tables (PHASE2_MOVES, 7 moves)
        print("  Phase 2 move tables...")
        self._mt_cp  = _build_move_table(_cp,  40320, PHASE2_MOVES)
        self._mt_ep8 = _build_move_table(_ep8, 40320, PHASE2_MOVES)
        self._mt_sp  = _build_move_table(_sp,  24,    PHASE2_MOVES)

        # Phase-1 pruning tables (depth 8 covers all reachable P1 states)
        print("  Phase 1 pruning tables...")
        self._pr_eo_co, self._N_CO = _build_pruning_table(
            self._mt_eo, 2048, self._mt_co, 2187, SAFE15,
            self._goal_eo, self._goal_co, 8)
        self._pr_eo_ud, self._N_UD = _build_pruning_table(
            self._mt_eo, 2048, self._mt_ud, 495, SAFE15,
            self._goal_eo, self._goal_ud, 8)

        # Phase-2 pruning tables (depth 12)
        print("  Phase 2 pruning tables...")
        self._pr_cp_sp, self._N_SP1 = _build_pruning_table(
            self._mt_cp, 40320, self._mt_sp, 24, PHASE2_MOVES,
            self._goal_cp, self._goal_sp, 12)
        self._pr_ep_sp, self._N_SP2 = _build_pruning_table(
            self._mt_ep8, 40320, self._mt_sp, 24, PHASE2_MOVES,
            self._goal_ep8, self._goal_sp, 12)

        print("Kociemba: tables ready.")

    # ------------------------------------------------------------------
    # Heuristics
    # ------------------------------------------------------------------

    def _h1(self, eo, co, ud):
        """Phase-1 admissible lower bound (max of two pruning table lookups)."""
        v1 = self._pr_eo_co[eo * self._N_CO + co]
        v2 = self._pr_eo_ud[eo * self._N_UD + ud]
        h1 = self._MAX_PHASE1 if v1 == 255 else v1
        h2 = self._MAX_PHASE1 if v2 == 255 else v2
        return max(h1, h2)

    def _h2(self, cp, ep8, sp):
        """Phase-2 admissible lower bound."""
        v1 = self._pr_cp_sp[cp  * self._N_SP1 + sp]
        v2 = self._pr_ep_sp[ep8 * self._N_SP2 + sp]
        h1 = self._MAX_PHASE2 if v1 == 255 else v1
        h2 = self._MAX_PHASE2 if v2 == 255 else v2
        return max(h1, h2)

    # ------------------------------------------------------------------
    # Phase 1 IDA*
    # ------------------------------------------------------------------

    def _p1_search(self, eo, co, ud, g, bound, path, prev_mi):
        h = self._h1(eo, co, ud)
        f = g + h
        if f > bound:
            return f
        if eo == self._goal_eo and co == self._goal_co and ud == self._goal_ud:
            return path[:]

        min_t = float("inf")
        for mi, move in enumerate(SAFE15):
            if prev_mi is not None and _redundant(SAFE15[prev_mi], move):
                continue
            neo = self._mt_eo[eo][mi]
            nco = self._mt_co[co][mi]
            nud = self._mt_ud[ud][mi]
            if neo < 0:
                neo = eo
            if nco < 0:
                nco = co
            if nud < 0:
                nud = ud
            path.append(mi)
            result = self._p1_search(neo, nco, nud, g + 1, bound, path, mi)
            path.pop()
            if isinstance(result, list):
                return result
            if result < min_t:
                min_t = result
        return min_t

    def solve_phase1(self, state):
        """Return move list that reduces state to G1 (EO=CO=0, UD=solved)."""
        eo = _eo(state)
        co = _co(state)
        ud = _ud(state)
        if eo == self._goal_eo and co == self._goal_co and ud == self._goal_ud:
            return []
        bound = self._h1(eo, co, ud)
        while bound <= self._MAX_PHASE1:
            path   = []
            result = self._p1_search(eo, co, ud, 0, bound, path, None)
            if isinstance(result, list):
                return [SAFE15[mi] for mi in result]
            if result == float("inf"):
                break
            bound = result
        return []

    # ------------------------------------------------------------------
    # Phase 2 IDA*
    # ------------------------------------------------------------------

    def _p2_search(self, cp, ep8, sp, g, bound, path, prev_mi):
        h = self._h2(cp, ep8, sp)
        f = g + h
        if f > bound:
            return f
        if cp == self._goal_cp and ep8 == self._goal_ep8 and sp == self._goal_sp:
            return path[:]

        min_t = float("inf")
        for mi, move in enumerate(PHASE2_MOVES):
            if prev_mi is not None and _redundant(PHASE2_MOVES[prev_mi], move):
                continue
            ncp  = self._mt_cp[cp][mi]
            nep8 = self._mt_ep8[ep8][mi]
            nsp  = self._mt_sp[sp][mi]
            if ncp < 0:
                ncp = cp
            if nep8 < 0:
                nep8 = ep8
            if nsp < 0:
                nsp = sp
            path.append(mi)
            result = self._p2_search(ncp, nep8, nsp, g + 1, bound, path, mi)
            path.pop()
            if isinstance(result, list):
                return result
            if result < min_t:
                min_t = result
        return min_t

    def solve_phase2(self, state):
        """Return move list within G1 that fully solves state."""
        cp  = _cp(state)
        ep8 = _ep8(state)
        sp  = _sp(state)
        if cp == self._goal_cp and ep8 == self._goal_ep8 and sp == self._goal_sp:
            return []
        bound = self._h2(cp, ep8, sp)
        while bound <= self._MAX_PHASE2:
            path   = []
            result = self._p2_search(cp, ep8, sp, 0, bound, path, None)
            if isinstance(result, list):
                return [PHASE2_MOVES[mi] for mi in result]
            if result == float("inf"):
                break
            bound = result
        return []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def solve(self) -> list:
        """
        Execute the two-phase search and return the full move list.

        Phase 1 reduces to G1 using SAFE15.
        Phase 2 solves within G1 using {U, U', U2, R2, F2, L2, B2}.
        """
        self._working = copy.deepcopy(self.cube_state)
        self.moves    = []

        print("Kociemba Phase 1: reducing to G1...")
        p1 = self.solve_phase1(self._working)
        for m in p1:
            self._working = PT.apply_move(self._working, PT.MOVES[m])
        self.moves.extend(p1)
        print(f"  Phase 1: {len(p1)} moves  {' '.join(p1) or '(none)'}")

        print("Kociemba Phase 2: solving within G1...")
        p2 = self.solve_phase2(self._working)
        for m in p2:
            self._working = PT.apply_move(self._working, PT.MOVES[m])
        self.moves.extend(p2)
        print(f"  Phase 2: {len(p2)} moves  {' '.join(p2) or '(none)'}")

        print(f"Kociemba: total = {len(self.moves)} moves.")
        return self.moves
