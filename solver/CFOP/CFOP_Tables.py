"""
SYSC3010 - Pi Cubed | Group L3-G6 | Author: Luke Grundy

Supporting data structures and helpers for CFOP_Algorithm. Provides:
  build_extra_moves()       - extended move set (r, f, M, x, y and inverses)
  _apply_std / _apply_ext   - state application helpers
  Cross: d_cross_ok, cross_edge_solved, solve_cross_edge (BFS)
  F2L:   F2L_SLOT_SOLVED, get_piece_signature, build_f2l_table (reverse BFS)
  OLL:   get_oll_orient_key, build_oll_lookup
  PLL:   get_pll_pattern, build_pll_lookup
"""

import json
from collections import deque

from Cube_State import Cube
import Permutation_Table


# ------------------------------------------------------------------
# Extended move set: 
#   wide moves (r, f), slice moves (M), and cube rotations (x, y).
#   used to map basic CFOP algorithms before I created algs that map to motor pi
# ------------------------------------------------------------------

def build_extra_moves():
    """
    Extend Permutation_Table.MOVES with wide moves (r, f), slice moves (M, M2),
    and whole-cube rotations (x, y) plus their inverses/doubles.
    """
    def identity():
        return list(range(54))

    def compose(p1, p2):
        return [p1[p2[i]] for i in range(54)]

    # M slice (middle layer, same direction as L)
    M = identity()
    M[1],  M[4],  M[7]  = 19, 22, 25
    M[19], M[22], M[25] = 28, 31, 34
    M[28], M[31], M[34] = 52, 49, 46
    M[52], M[49], M[46] =  1,  4,  7
    M_prime = Permutation_Table.invert_perm(M)
    M2 = compose(M, M)

    # S slice (middle layer, same direction as F)
    S = identity()
    S[3],  S[4],  S[5]  = 43, 40, 37
    S[43], S[40], S[37] = 30, 31, 32
    S[30], S[31], S[32] = 10, 13, 16
    S[10], S[13], S[16] =  3,  4,  5

    # E slice (middle layer, same direction as D)
    E = identity()
    E[12], E[13], E[14] = 48, 49, 50
    E[48], E[49], E[50] = 39, 40, 41
    E[39], E[40], E[41] = 21, 22, 23
    E[21], E[22], E[23] = 12, 13, 14

    r = compose(M_prime, Permutation_Table.MOVES["R"])
    r_prime = Permutation_Table.invert_perm(r)
    r2 = compose(r, r)

    f = compose(S, Permutation_Table.MOVES["F"])
    f_prime = Permutation_Table.invert_perm(f)

    y = compose(Permutation_Table.MOVES["D'"], compose(E, Permutation_Table.MOVES["U"]))
    y_prime = Permutation_Table.invert_perm(y)

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


# ------------------------------------------------------------------
# Cube index constants
#   Maps facelet indexes to recognize pieces and patterns.
# ------------------------------------------------------------------

CORNER_INDICES = {
    "UFR": (8,  20,  9),  "UFL": (6,  38, 18),
    "UBR": (2,  11, 45),  "UBL": (0,  47, 36),
    "DFR": (29, 26, 15),  "DFL": (27, 44, 24),
    "DBR": (35, 17, 51),  "DBL": (33, 53, 42),
}

EDGE_INDICES = {
    "UF": (7,  19), "UR": (5,  10), "UB": (1,  46), "UL": (3,  37),
    "FR": (23, 12), "FL": (21, 41), "BR": (48, 14),  "BL": (50, 39),
    "DF": (28, 25), "DR": (32, 16), "DB": (34, 52),  "DL": (30, 43),
}

# 15 moves excluding D-face, used for cross/F2L BFS so D-cross is never disturbed.
SAFE15 = [m for m in
    ["U","U'","U2","R","R'","R2","F","F'","F2","L","L'","L2","B","B'","B2"]
]


# ------------------------------------------------------------------
# Move helpers
# ------------------------------------------------------------------

def _apply_std(state, alg):
    """Apply standard face moves to a state list; returns new state."""
    c = Cube()
    c.set_cube_state(state[:])
    c.apply_sequence(alg)
    return c.state


def _apply_ext(state, alg, move_map):
    """Apply extended moves (wide/slice/rotation) to a state list; returns new state."""
    s = state[:]
    for m in alg:
        if m in move_map:
            s = Permutation_Table.apply_move(s, move_map[m])
    return s


def _invert_seq(seq):
    """Invert a short move sequence drawn from SAFE15."""
    inv_map = {
        "U": "U'", "U'": "U", "U2": "U2",
        "R": "R'", "R'": "R", "R2": "R2",
        "F": "F'", "F'": "F", "F2": "F2",
        "L": "L'", "L'": "L", "L2": "L2",
        "B": "B'", "B'": "B", "B2": "B2",
    }
    return [inv_map[m] for m in reversed(seq)]


# ------------------------------------------------------------------
# Cross helpers
# ------------------------------------------------------------------

def d_cross_ok(state):
    """Return True when all four D-layer cross edges are solved."""
    return (
        state[28] == "D" and state[25] == "F" and
        state[32] == "D" and state[16] == "R" and
        state[34] == "D" and state[52] == "B" and
        state[30] == "D" and state[43] == "L"
    )


def cross_edge_solved(state, slot):
    """Return True if the given D-layer cross edge (DF/DR/DB/DL) is solved."""
    checks = {
        "DF": lambda s: s[28] == "D" and s[25] == "F",
        "DR": lambda s: s[32] == "D" and s[16] == "R",
        "DB": lambda s: s[34] == "D" and s[52] == "B",
        "DL": lambda s: s[30] == "D" and s[43] == "L",
    }
    return checks[slot](state)


def solve_cross_edge(state, slot, already_solved):
    """
    BFS to insert one D-layer cross edge without disturbing already-solved edges.
    Uses only SAFE15 moves (no D moves). Max depth 9. Returns move list or [].
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
        for move in SAFE15:
            newstate = tuple(Permutation_Table.apply_move(list(current), Permutation_Table.MOVES[move]))
            if newstate in visited:
                continue
            newmove = moves + [move]
            newstatelist = list(newstate)
            if cross_edge_solved(newstatelist, slot) and all(
                cross_edge_solved(newstatelist, s) for s in already_solved
            ):
                return newmove
            if len(newmove) < 9:
                visited.add(newstate)
                queue.append((newstate, newmove))

    return []


# ------------------------------------------------------------------
# F2L helpers
# ------------------------------------------------------------------

# Per-slot solved-state predicates.
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
    Return a hashable descriptor of where the corner and edge pieces are and
    how they are oriented. Used as the F2L lookup key.
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
    Generate composite sequences of length 1 to max_len drawn from SAFE15 that
    preserve both the D-cross and all slots in preserve_slots. These are used
    as atomic BFS edges when building F2L tables.
    """
    safe = []

    for length in range(1, max_len + 1):
        if length == 1:
            for m in SAFE15:
                t = _apply_std(solved, [m])
                if d_cross_ok(t) and all(F2L_SLOT_SOLVED[sl](t) for sl in preserve_slots):
                    safe.append([m])
        elif length == 2:
            for m1 in SAFE15:
                for m2 in SAFE15:
                    t = _apply_std(solved, [m1, m2])
                    if d_cross_ok(t) and all(F2L_SLOT_SOLVED[sl](t) for sl in preserve_slots):
                        safe.append([m1, m2])
        elif length == 3:
            for m1 in SAFE15:
                for m2 in SAFE15:
                    for m3 in SAFE15:
                        t = _apply_std(solved, [m1, m2, m3])
                        if d_cross_ok(t) and all(F2L_SLOT_SOLVED[sl](t) for sl in preserve_slots):
                            safe.append([m1, m2, m3])

    return safe


def build_f2l_table(slot, corner_colours, edge_colours, preserve_slots, max_depth=3):
    """
    Build a reverse-BFS lookup table: piece_signature -> solving_move_sequence.

    Starts from the solved cube and explores states reachable via safe composite
    moves (those that preserve cross and all preserve_slots). The stored
    algorithm for each state is the inverse of the path back to solved, so every
    entry is guaranteed safe to apply after the listed slots are complete.
    """
    solved     = Cube().state
    slot_done  = F2L_SLOT_SOLVED[slot]

    def sig_fn(s):
        return get_piece_signature(s, corner_colours, edge_colours)

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
            ns = _apply_std(current, seq)
            if not d_cross_ok(ns):
                continue
            if not all(F2L_SLOT_SOLVED[sl](ns) for sl in preserve_slots):
                continue
            k = sig_fn(ns)
            if k in visited:
                continue
            new_path = backward_path + [seq]
            if not slot_done(ns) and k not in lut:
                forward = [m for seg in reversed(new_path) for m in _invert_seq(seg)]
                lut[k]  = forward
            visited.add(k)
            queue.append((ns, new_path))

    return lut


# ------------------------------------------------------------------
# OLL helpers
# ------------------------------------------------------------------

def get_oll_orient_key(state):
    """
    Return the 8-tuple orientation key (UFR_twist, UFL_twist, UBR_twist,
    UBL_twist, UF_flip, UR_flip, UB_flip, UL_flip) for the current U layer.

    Corner twist: 0=U-sticker up, 1=CW, 2=CCW.
    Edge flip:    0=U-sticker up, 1=flipped.

    This key is permutation-invariant: it encodes orientation only, so the
    same algorithm applies regardless of which piece sits in which slot.
    """
    _corner_idxs = ((8, 20, 9), (6, 18, 38), (2, 45, 11), (0, 36, 47))
    _edge_idxs   = ((7, 19), (5, 10), (1, 46), (3, 37))
    key = []
    for i0, i1, i2 in _corner_idxs:
        if state[i0] in ("U", "D"):
            key.append(0)
        elif state[i1] in ("U", "D"):
            key.append(1)
        else:
            key.append(2)
    for i0, i1 in _edge_idxs:
        key.append(0 if state[i0] in ("U", "D") else 1)
    return tuple(key)


def build_oll_lookup(json_path, all_moves):
    """
    Load OLL.json and return a dict: orient_key_tuple -> solving_move_list.
    Reads the OLL_orient section only. Returns {} on file error.
    """
    import ast as _ast

    try:
        with open(json_path) as fh:
            raw = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

    lut = {}
    for key_str, alg in raw.get("OLL_orient", {}).items():
        try:
            key = tuple(_ast.literal_eval(key_str))
        except (ValueError, SyntaxError):
            continue
        lut[key] = alg

    return lut


# ------------------------------------------------------------------
# PLL helpers
# ------------------------------------------------------------------

def get_pll_pattern(state):
    """
    Return the 12-element tuple of side-face top-row sticker colours.
    Indices: F[18-20], R[9-11], B[45-47], L[36-38].
    """
    idxs = [18, 19, 20, 9, 10, 11, 45, 46, 47, 36, 37, 38]
    return tuple(state[i] for i in idxs)


def build_pll_lookup(json_path, all_moves):
    """
    Build and return the PLL lookup table: pll_pattern -> complete_solving_sequence.

    For every PLL case in PLL.json (including PLL_skip), all 16 combinations of
    pre-AUF x post-AUF are generated and put in a lookup table. 
    The scrambled state that each full sequence solves is recovered via inversion, 
    and the full sequence is stored as the value.
    This means no AUF retry is needed at solve time.
    """
    _INV = {
        "U": "U'", "U'": "U", "U2": "U2",
        "R": "R'", "R'": "R", "R2": "R2",
        "F": "F'", "F'": "F", "F2": "F2",
        "L": "L'", "L'": "L", "L2": "L2",
        "B": "B'", "B'": "B", "B2": "B2",
        "D": "D'", "D'": "D", "D2": "D2",
        "r": "r'", "r'": "r", "r2": "r2",
        "f": "f'", "f'": "f",
        "M": "M'", "M'": "M", "M2": "M2",
        "x": "x'", "x'": "x",
        "y": "y'", "y'": "y",
    }

    def _inv_alg(alg):
        return [_INV[m] for m in reversed(alg) if m in _INV]

    try:
        with open(json_path) as fh:
            raw = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

    solved = Cube().state
    lut    = {}
    _AUF   = ([], ["U"], ["U'"], ["U2"])

    for name, alg in raw.get("PLL", {}).items():
        for pre in _AUF:
            for post in _AUF:
                inv_full = _inv_alg(pre + alg + post)
                state    = _apply_ext(solved[:], inv_full, all_moves)
                pattern  = get_pll_pattern(state)
                if pattern not in lut:
                    lut[pattern] = pre + alg + post

    return lut