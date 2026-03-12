"""
SYSC3010 - Pi Cubed Rubik's Cube Solver
Solver Algorithm Pi - Permutation Table Module
Group L3-G6

Author: Luke Grundy

Purpose:
    This module defines the permutation tables for a 3x3 Rubik's Cube using the 54-facelet representation.

Cube Representation:
    The cube is represented as a list of 54 facelets in the following order:

        U:  0-8
        R:  9-17
        F: 18-26
        D: 27-35
        L: 36-44
        B: 45-53

    Each face is indexed as follows:

        0 1 2
        3 4 5
        6 7 8

Centers:
    Indices 4, 13, 22, 31, 40, 49 are the center of each face.
    Never modified by permutations.

Move Notation:
    Standard moves rotate the cube clockwise while looking directly at the indicated face (U, R, F, D, L, B).
    A prime (') indicates counterclockwise, and a '2' indicates a 180-degree turn.

Supported Moves:
    U,  R,  F,  D,  L,  B
    U', R', F', D', L', B'
    U2, R2, F2, D2, L2, B2

"""


# Helper Functions

def identity_perm():
    """Return identity state for 54-element cube."""
    return list(range(54))


def invert_perm(p):
    """Return inverse permutation."""
    inv = [0] * 54
    for i in range(54):
        inv[p[i]] = i
    return inv


def compose_perm(p1, p2):
    """Compose two permutations: apply p2, then p1."""
    return [p1[p2[i]] for i in range(54)]


def apply_move(cube, perm):
    """
    Apply permutation to cube state.

    cube: list of 54 elements |
    perm: permutation list of length 54
    """
    return [cube[perm[i]] for i in range(54)]



# Base Move Definitions

# Each move is built from identity and modified only where needed.

# =========================
# U Move (Up Clockwise)   |
# =========================
U = identity_perm()

# Rotate U face
U[0], U[1], U[2], U[3], U[5], U[6], U[7], U[8] = \
U[6], U[3], U[0], U[7], U[1], U[8], U[5], U[2]

# Side cycle
U[9], U[10], U[11]   = 45, 46, 47
U[45], U[46], U[47]  = 36, 37, 38
U[36], U[37], U[38]  = 18, 19, 20
U[18], U[19], U[20]  = 9, 10, 11


# =========================
# D Move (Down Clockwise) |
# =========================
D = identity_perm()

# Rotate D face
D[27], D[28], D[29], D[30], D[32], D[33], D[34], D[35] = \
D[33], D[30], D[27], D[34], D[28], D[35], D[32], D[29]

# Side cycle
D[15], D[16], D[17]  = 24, 25, 26
D[51], D[52], D[53]  = 15, 16, 17
D[42], D[43], D[44]  = 51, 52, 53
D[24], D[25], D[26]  = 42, 43, 44


# =========================
# R Move (Right Clockwise)|
# =========================
R = identity_perm()

# Rotate R face
R[9], R[10], R[11], R[12], R[14], R[15], R[16], R[17] = \
R[15], R[12], R[9], R[16], R[10], R[17], R[14], R[11]

# Side cycle
R[2], R[5], R[8]     = 20, 23, 26
R[51], R[48], R[45]  = 2, 5, 8
R[29], R[32], R[35]  = 51, 48, 45
R[20], R[23], R[26]  = 29, 32, 35


# =========================
# L Move (Left Clockwise) |
# =========================
L = identity_perm()

# Rotate L face
L[36], L[37], L[38], L[39], L[41], L[42], L[43], L[44] = \
L[42], L[39], L[36], L[43], L[37], L[44], L[41], L[38]

# Side cycle
L[0], L[3], L[6]     = 53, 50, 47
L[53], L[50], L[47]  = 27, 30, 33
L[27], L[30], L[33]  = 18, 21, 24
L[18], L[21], L[24]  = 0, 3, 6


# =========================
# F Move (Front Clockwise)|
# =========================
F = identity_perm()

# Rotate F face
F[18], F[19], F[20], F[21], F[23], F[24], F[25], F[26] = \
F[24], F[21], F[18], F[25], F[19], F[26], F[23], F[20]

# Side cycle
F[6], F[7], F[8]     = 44, 41, 38
F[9], F[12], F[15]   = 6, 7, 8
F[29], F[28], F[27]  = 9, 12, 15
F[44], F[41], F[38]  = 29, 28, 27


# =========================
# B Move (Back Clockwise) |
# =========================
B = identity_perm()

# Rotate B face
B[45], B[46], B[47], B[48], B[50], B[51], B[52], B[53] = \
B[51], B[48], B[45], B[52], B[46], B[53], B[50], B[47]

# Side cycle
B[0], B[1], B[2]     = 11, 14, 17
B[42], B[39], B[36]  = 0, 1, 2
B[35], B[34], B[33]  = 42, 39, 36
B[11], B[14], B[17]  = 35, 34, 33




# Generate All Moves

MOVES = {}

base_moves = {
    "U": U,
    "R": R,
    "F": F,
    "D": D,
    "L": L,
    "B": B,
}

for name, perm in base_moves.items():
    MOVES[name] = perm
    MOVES[name + "2"] = compose_perm(perm, perm)
    MOVES[name + "'"] = invert_perm(perm)



# Utility Functions

def apply_move_sequence(cube, move_list):
    """
    Apply a sequence of moves.

    cube: 54-element list |
    move_list: ["R", "U", "R'", "U'"]
    """
    for move in move_list:
        cube = apply_move(cube, MOVES[move])
    return cube

