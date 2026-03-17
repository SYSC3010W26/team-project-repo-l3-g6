"""
SYSC3010 - Pi Cubed Rubik's Cube Solver
Solver Algorithm Pi - CFOP Tables Module
Group L3-G6

Author: Luke Grundy

Location: CFOP/CFOP_Tables.py

Purpose:
    Provides all supporting data structures and helper functions used by
    CFOP_Algorithm.py.  Specifically:

        AlgorithmTable       - thin JSON loader kept for backward compatibility
        build_extra_moves()  - extended move permutations (r, f, M, x, y …)
        Cube index constants - CORNER_INDICES, EDGE_INDICES, ALL18, SAFE15
        apply_alg()          - apply a move sequence to a cube state
        invert_alg()         - reverse a move sequence

        Cross stage:
            d_cross_ok()         - check whether D-layer cross is solved
            cross_edge_solved()  - check one edge of the cross
            solve_cross_edge()   - BFS to insert one cross edge

        F2L stage:
            F2L_SLOT_SOLVED       - per-slot solved-state lambdas
            get_piece_signature() - hashable (corner, edge) position descriptor
            build_f2l_table()     - per-slot reverse-BFS lookup-table builder

        OLL stage:
            get_oll_pattern()   - 20-bit U-layer fingerprint
            build_oll_lookup()  - OLL pattern → (auf, alg) table

        PLL stage:
            get_pll_pattern()   - 12-element side top-row fingerprint
            build_pll_lookup()  - PLL pattern → (auf, alg) table

Orientation Convention:
    White = 'U' colour (top face in solved state).
    The cross is solved on the D layer so that F2L algorithms using U/R/F moves
    do not disturb already-placed cross edges.
"""

import json
from collections import deque

import Permutation_Table

class AlgorithmTable:
    """Loads an algorithm table from a JSON file and provides accessor methods."""

    def __init__(self, filepath="algorithms.json"):
        """ Load algorithm table from a JSON file. """
        with open(filepath, "r") as f:
            self.algorithms = json.load(f)

    def get_algorithm(self, stage, case_id):
        """ Retrieve the move sequence for a specific stage and case. """
        return self.algorithms.get(stage, {}).get(case_id)

    def get_stage_cases(self, stage):
        """Return all cases (as a dict) for a given stage of solving."""
        return self.algorithms.get(stage, {})

    def list_stages(self):
        """Return a list of all stage names present in the loaded table."""
        return list(self.algorithms.keys())


# ===========================================================================
# Extra permutations
# ===========================================================================

def build_extra_moves():
    """
    Build and return a move-name + permutation dict that extends
    Permutation_Table.MOVES with the following additional moves:

        r, r', r2   - right wide move
        f, f'       - front wide move
        M, M', M2   - middle slice
        y, y'       - whole-cube rotation like U
        x, x'       - whole-cube rotation like R

    """
    def identity():
        return list(range(54))

    def compose(p1, p2):
        return [p1[p2[i]] for i in range(54)]

    # =========================
    # M slice                 |
    # =========================
    M = identity()

    M[1],  M[4],  M[7]  = 52, 49, 46
    M[52], M[49], M[46] = 34, 31, 28
    M[28], M[31], M[34] = 19, 22, 25
    M[19], M[22], M[25] =  1,  4,  7
    M_prime = Permutation_Table.invert_perm(M)
    M2 = compose(M, M)

    # =========================
    # S slice                 |
    # =========================
    S = identity()

    S[3],  S[4],  S[5]  = 43, 40, 37
    S[43], S[40], S[37] = 30, 31, 32
    S[30], S[31], S[32] = 10, 13, 16
    S[10], S[13], S[16] =  3,  4,  5

    # =========================
    # r move (Right Wide)     |
    # =========================
    # r = R + M'
    r = compose(M_prime, Permutation_Table.MOVES["R"])
    r_prime = Permutation_Table.invert_perm(r)
    r2 = compose(r, r)

    # =========================
    # f move (Front Wide)     |
    # =========================
    # f = F + S
    f = compose(S, Permutation_Table.MOVES["F"])
    f_prime = Permutation_Table.invert_perm(f)

    # =========================
    # E slice                 |
    # =========================
    E = identity()

    E[12], E[13], E[14] = 48, 49, 50
    E[48], E[49], E[50] = 39, 40, 41
    E[39], E[40], E[41] = 21, 22, 23
    E[21], E[22], E[23] = 12, 13, 14

    # =========================
    # y rotation              |
    # =========================
    # y = U + E + D'
    y = compose(Permutation_Table.MOVES["D'"], compose(E, Permutation_Table.MOVES["U"]))
    y_prime = Permutation_Table.invert_perm(y)

    # =========================
    # x rotation              |
    # =========================
    # x = R + M' + L'
    x = compose(Permutation_Table.MOVES["L'"], compose(M_prime, Permutation_Table.MOVES["R"]))
    x_prime = Permutation_Table.invert_perm(x)

    extra = dict(Permutation_Table.MOVES)
    extra.update({
        "r": r,  "r'": r_prime, "r2": r2,
        "f": f,  "f'": f_prime,
        "M": M,  "M'": M_prime, "M2": M2,
        "y": y,  "y'": y_prime,
        "x": x,  "x'": x_prime,
    })
    return extra


# ===========================================================================
# Cube index constants
# ===========================================================================

# Corner slots, each mapped to the indices of its three stickers in the cube state list.
CORNER_INDICES = {
    "UFR": (8,  20,  9),  "UFL": (6,  38, 18),
    "UBR": (2,  11, 45),  "UBL": (0,  47, 36),
    "DFR": (29, 26, 15),  "DFL": (27, 44, 24),
    "DBR": (35, 17, 51),  "DBL": (33, 53, 42),
}

# Edge slots, each mapped to the indices of its two stickers in the cube state list.
EDGE_INDICES = {
    "UF": (7,  19), "UR": (5,  10), "UB": (1,  46), "UL": (3,  37),
    "FR": (23, 12), "FL": (21, 41), "BR": (48, 14),  "BL": (50, 39),
    "DF": (28, 25), "DR": (32, 16), "DB": (34, 52),  "DL": (30, 43),
}

# All 18 standard face moves
ALL18 = [
    "U", "U'", "U2",
    "R", "R'", "R2",
    "F", "F'", "F2",
    "L", "L'", "L2",
    "B", "B'", "B2",
    "D", "D'", "D2",
]

# Subset of ALL18 that excludes D-face moves.
# Used when generating composite BFS moves for F2L table building so that
# single-step D moves (which unconditionally disturb the D-cross) are never
# used as primitives.
SAFE15 = [m for m in ALL18 if not m.startswith("D")]


# ===========================================================================
# Generic move helpers
# ===========================================================================

def apply_alg(state, alg, move_map=None):
    """
    Apply a sequence of move strings to a cube state list.

    state    - list of 54 sticker strings
    alg      - list of move strings, e.g. ["R", "U", "R'"]
    move_map - dict of move-name → permutation list; defaults to
               Permutation_Table.MOVES (standard 18 face moves only)

    Returns a new state list; the input is not modified.
    """
    s     = state[:]
    table = move_map if move_map is not None else Permutation_Table.MOVES
    for m in alg:
        if m in table:
            s = Permutation_Table.apply_move(s, table[m])
    return s


def invert_alg(alg):
    """
    Return the inverse of a move sequence (reversed order, each move inverted).
    Handles standard face moves, wide moves, slice moves, and rotations.
    """
    inv_map = {
        "U":  "U'",  "U'": "U",  "U2": "U2",
        "R":  "R'",  "R'": "R",  "R2": "R2",
        "F":  "F'",  "F'": "F",  "F2": "F2",
        "L":  "L'",  "L'": "L",  "L2": "L2",
        "B":  "B'",  "B'": "B",  "B2": "B2",
        "D":  "D'",  "D'": "D",  "D2": "D2",
        "r":  "r'",  "r'": "r",  "r2": "r2",
        "f":  "f'",  "f'": "f",
        "M":  "M'",  "M'": "M",  "M2": "M2",
        "x":  "x'",  "x'": "x",
        "y":  "y'",  "y'": "y",
    }
    return [inv_map[m] for m in reversed(alg) if m in inv_map]


def _invert_seq(seq):
    """
    Invert a short move sequence drawn from SAFE15.
    Used internally to reverse BFS backward-path segments.
    """
    inv_map = {
        "U": "U'", "U'": "U", "U2": "U2",
        "R": "R'", "R'": "R", "R2": "R2",
        "F": "F'", "F'": "F", "F2": "F2",
        "L": "L'", "L'": "L", "L2": "L2",
        "B": "B'", "B'": "B", "B2": "B2",
    }
    return [inv_map[m] for m in reversed(seq)]


# ===========================================================================
# Cross helpers
# ===========================================================================

def d_cross_ok(state):
    """
    Return True when all four D-layer cross edges are in their solved positions:
        DF: D sticker at index 28, F sticker at index 25
        DR: D sticker at index 32, R sticker at index 16
        DB: D sticker at index 34, B sticker at index 52
        DL: D sticker at index 30, L sticker at index 43
    """
    return (
        state[28] == "D" and state[25] == "F" and
        state[32] == "D" and state[16] == "R" and
        state[34] == "D" and state[52] == "B" and
        state[30] == "D" and state[43] == "L"
    )


def cross_edge_solved(state, slot):
    """
    Return True if the given D-layer cross edge is in its solved position.

    slot - one of "DF", "DR", "DB", "DL"
    """
    checks = {
        "DF": lambda s: s[28] == "D" and s[25] == "F",
        "DR": lambda s: s[32] == "D" and s[16] == "R",
        "DB": lambda s: s[34] == "D" and s[52] == "B",
        "DL": lambda s: s[30] == "D" and s[43] == "L",
    }
    return checks[slot](state)


def solve_cross_edge(state, slot, already_solved):
    """
    BFS to insert one D-layer cross edge into its solved position without
    disturbing any edges that are already solved.

    state          - current cube state (list of 54 strings)
    slot           - target edge: one of "DF", "DR", "DB", "DL"
    already_solved - list of edge slot names that must remain solved

    Returns a list of move strings (empty if the edge is already in place).
    Maximum search depth is 9 moves.
    """
    if cross_edge_solved(state, slot):
        return []

    start   = tuple(state)
    queue   = deque([(start, [])])
    visited = {start}

    while queue:
        current, moves = queue.popleft()
        if len(moves) >= 9:
            continue
        for move in ALL18:
            ns = tuple(Permutation_Table.apply_move(list(current), Permutation_Table.MOVES[move]))
            if ns in visited:
                continue
            nm  = moves + [move]
            nsl = list(ns)
            if cross_edge_solved(nsl, slot) and all(
                cross_edge_solved(nsl, s) for s in already_solved
            ):
                return nm
            if len(nm) < 9:
                visited.add(ns)
                queue.append((ns, nm))

    return []


# ===========================================================================
# F2L helpers
# ===========================================================================

# Lambda for each slot: returns True when the corner-edge pair is correctly
# inserted.  Keyed by the slot name used in CFOP_Algorithm.
F2L_SLOT_SOLVED = {
    "FR": lambda s: (s[29]=="D" and s[26]=="F" and s[15]=="R"
                     and s[23]=="F" and s[12]=="R"),
    "FL": lambda s: (s[27]=="D" and s[44]=="L" and s[24]=="F"
                     and s[21]=="F" and s[41]=="L"),
    "BR": lambda s: (s[35]=="D" and s[17]=="R" and s[51]=="B"
                     and s[48]=="B" and s[14]=="R"),
    "BL": lambda s: (s[33]=="D" and s[53]=="B" and s[42]=="L"
                     and s[50]=="B" and s[39]=="L"),
}


def get_piece_signature(state, corner_colours, edge_colours):
    """
    Return a hashable descriptor of where the specified corner and edge pieces
    currently are and how they are oriented.

    corner_colours - 3-character string of the corner's face colours, e.g. "DFR"
    edge_colours   - 2-character string of the edge's face colours, e.g. "FR"

    Returns a 2-tuple:
        ( (corner_slot_name, sticker_orientation_tuple),
          (edge_slot_name,   sticker_orientation_tuple) )
    Either element is None if the piece is not found.
    """
    tc = frozenset(corner_colours)
    te = frozenset(edge_colours)
    cs = es = None

    for slot, idxs in CORNER_INDICES.items():
        if frozenset(state[i] for i in idxs) == tc:
            cs = (slot, tuple(state[i] for i in idxs))
            break
    for slot, idxs in EDGE_INDICES.items():
        if frozenset(state[i] for i in idxs) == te:
            es = (slot, tuple(state[i] for i in idxs))
            break

    return (cs, es)


def _generate_safe_composites(solved, preserve_slots, max_len=3):
    """
    Generate all composite move sequences of length 1 to max_len drawn from
    SAFE15 that, when applied to the solved state, satisfy both:
        - the D-layer cross remains solved  (d_cross_ok)
        - every slot in preserve_slots remains solved

    These sequences are used as atomic BFS edges when building F2L tables,
    ensuring every stored algorithm is inherently safe to apply after the
    listed slots have been solved.

    Returns a list of move-string lists.
    """
    safe = []

    for length in range(1, max_len + 1):
        if length == 1:
            for m in SAFE15:
                t = apply_alg(solved, [m])
                if d_cross_ok(t) and all(F2L_SLOT_SOLVED[sl](t) for sl in preserve_slots):
                    safe.append([m])

        elif length == 2:
            for m1 in SAFE15:
                for m2 in SAFE15:
                    t = apply_alg(solved, [m1, m2])
                    if d_cross_ok(t) and all(F2L_SLOT_SOLVED[sl](t) for sl in preserve_slots):
                        safe.append([m1, m2])

        elif length == 3:
            for m1 in SAFE15:
                for m2 in SAFE15:
                    for m3 in SAFE15:
                        t = apply_alg(solved, [m1, m2, m3])
                        if d_cross_ok(t) and all(F2L_SLOT_SOLVED[sl](t) for sl in preserve_slots):
                            safe.append([m1, m2, m3])

    return safe


def build_f2l_table(slot, corner_colours, edge_colours,
                    preserve_slots, max_depth=3):
    """
    Build and return a lookup table:
        piece_signature  →  move_sequence_that_solves_the_slot

    The table is constructed via a reverse BFS starting from the fully solved
    cube.  Only the composite sequences produced by _generate_safe_composites()
    are used as BFS edges, so every stored algorithm is guaranteed to:
        - preserve the D-layer cross
        - leave all slots in preserve_slots undisturbed

    slot           - slot name, e.g. "FR"
    corner_colours  - 3-char string of the corner piece's face colours, e.g. "DFR"
    edge_colours    - 2-char string of the edge piece's face colours, e.g. "FR"
    preserve_slots - list of slot names that must remain solved throughout
    max_depth      - maximum number of composite BFS steps (each step is up to
                     3 actual moves, so the stored algorithms are at most
                     max_depth x 3 = 9 moves long)

    Returns a dict: signature_tuple → list of move strings
    """
    solved = (
        ["U"] * 9 + ["R"] * 9 + ["F"] * 9 +
        ["D"] * 9 + ["L"] * 9 + ["B"] * 9
    )
    slot_done  = F2L_SLOT_SOLVED[slot]
    sig_fn     = lambda s: get_piece_signature(s, corner_colours, edge_colours)
    composites = _generate_safe_composites(solved, preserve_slots, max_len=3)

    lut         = {}
    initial_sig = sig_fn(solved)
    queue       = deque([(solved, [])])
    visited     = {initial_sig}

    while queue:
        current, backward_path = queue.popleft()
        if len(backward_path) >= max_depth:
            continue
        for seq in composites:
            ns = apply_alg(current, seq)
            if not d_cross_ok(ns):
                continue
            if not all(F2L_SLOT_SOLVED[sl](ns) for sl in preserve_slots):
                continue
            k = sig_fn(ns)
            if k in visited:
                continue
            new_path = backward_path + [seq]
            # The forward (solving) algorithm is the inverse of the backward path
            if not slot_done(ns) and k not in lut:
                forward = [m for seg in reversed(new_path) for m in _invert_seq(seg)]
                lut[k]  = forward
            visited.add(k)
            queue.append((ns, new_path))

    return lut


# ===========================================================================
# OLL helpers
# ===========================================================================

def get_oll_pattern(state):
    """
    Return a 20-element tuple of 0s and 1s indicating which stickers around
    the top layer currently show the U colour.

    Indices checked (in this order):
        U-face corners & edges : 0, 1, 2, 3, 5, 6, 7, 8
        F top row              : 18, 19, 20
        R top row              :  9, 10, 11
        B top row              : 45, 46, 47
        L top row              : 36, 37, 38
    """
    idxs = [0, 1, 2, 3, 5, 6, 7, 8,
            18, 19, 20, 9, 10, 11,
            45, 46, 47, 36, 37, 38]
    return tuple(1 if state[i] == "U" else 0 for i in idxs)


def build_oll_lookup(json_path, all_moves):
    """
    Build and return the OLL lookup table:
        oll_pattern  →  (auf_moves, alg_moves)

    For each algorithm in OLL.json the inverse is applied to the solved state
    to produce the corresponding setup state, then the OLL fingerprint is
    recorded for each of the four AUF (Adjust U Face) rotations:
    no rotation, U, U', U2.

    json_path - absolute path to OLL.json
    all_moves - extended move-map returned by build_extra_moves()

    Returns a dict: tuple(int, ...) → (list[str], list[str])
    Returns an empty dict if the file cannot be read.
    """
    solved = (
        ["U"] * 9 + ["R"] * 9 + ["F"] * 9 +
        ["D"] * 9 + ["L"] * 9 + ["B"] * 9
    )
    try:
        with open(json_path) as fh:
            oll_data = json.load(fh).get("OLL", {})
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return {}

    lut      = {}
    auf_list = [[], ["U"], ["U'"], ["U2"]]

    for _name, alg in oll_data.items():
        if not alg:
            continue
        inv   = invert_alg(alg)
        setup = apply_alg(solved, inv, all_moves)
        for auf in auf_list:
            test = apply_alg(setup, auf, all_moves)
            pat  = get_oll_pattern(test)
            if pat not in lut:
                lut[pat] = (list(auf), alg)

    return lut


# ===========================================================================
# PLL helpers
# ===========================================================================

def get_pll_pattern(state):
    """
    Return a 12-element tuple of the sticker colours in the top row of each
    side face.  Used to fingerprint the PLL case.

    Indices: F top row [18,19,20], R top row [9,10,11],
             B top row [45,46,47], L top row [36,37,38]
    """
    idxs = [18, 19, 20, 9, 10, 11, 45, 46, 47, 36, 37, 38]
    return tuple(state[i] for i in idxs)


def build_pll_lookup(json_path, all_moves):
    """
    Build and return the PLL lookup table:
        pll_pattern  →  (auf_moves, alg_moves)

    Constructed identically to the OLL table but using the PLL fingerprint
    function and PLL.json.

    json_path - absolute path to PLL.json
    all_moves - extended move-map returned by build_extra_moves()

    Returns a dict: tuple(str, ...) → (list[str], list[str])
    Returns an empty dict if the file cannot be read.
    """
    solved = (
        ["U"] * 9 + ["R"] * 9 + ["F"] * 9 +
        ["D"] * 9 + ["L"] * 9 + ["B"] * 9
    )
    try:
        with open(json_path) as fh:
            pll_data = json.load(fh).get("PLL", {})
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return {}

    lut      = {}
    auf_list = [[], ["U"], ["U'"], ["U2"]]

    for _name, alg in pll_data.items():
        if not alg:
            continue
        inv   = invert_alg(alg)
        setup = apply_alg(solved, inv, all_moves)
        for auf in auf_list:
            test = apply_alg(setup, auf, all_moves)
            pat  = get_pll_pattern(test)
            if pat not in lut:
                lut[pat] = (list(auf), alg)

    return lut