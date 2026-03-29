# Pi Cubed — Rubik's Cube Solver

**SYSC3010 Group L3-G6**  
Author: Luke Grundy

A Rubik's Cube solver built for a Raspberry Pi robot with five motors controlling the U, F, L, R, and B faces. The solver generates a sequence of standard move notation strings that the robot can execute to solve a given cube.

---

## Hardware Constraints

The robot has no D-face motor and cannot perform wide moves, slice moves, or cube rotations. The solver's legal move set is:

```
U  U'  U2
R  R'  R2
F  F'  F2
L  L'  L2
B  B'  B2
```

All Cross and F2L BFS tables are built exclusively from a **SAFE15** move set that only contains moves the robot can execute. OLL and PLL algorithms sourced from external references (mainly jperm.net) have been verified or replaced to contain only legal moves.

---

## Project Structure

```
solver/
├── Solver.py                  # Top-level public API
├── Algorithm_Selector.py      # Maps algorithm name → implementation
├── Cube_State.py              # Cube representation and move application
├── Cube_Algorithm.py          # Abstract base class for solving algorithms
├── Permutation_Table.py       # 54-facelet permutation tables for basic moves
├── Cube_Debug_Viewer.py       # Interactive CLI viewer
├── Test_Cube_Debug_Viewer.py  # 35-test unit test suite
└── CFOP/
    ├── __init__.py
    ├── CFOP_Algorithm.py      # Cross, F2L, OLL, PLL implementations
    ├── CFOP_Tables.py         # Lookup table builders and helper functions
    └── Algorithms/
        ├── OLL.json           # 64-entry orientation lookup table
        └── PLL.json           # 22 PLL algorithms
```

---

## Cube State Format

The cube is represented as a **54-character string** (or list) in face order:

| Indices | Face |
|---------|------|
| 0–8     | U    |
| 9–17    | R    |
| 18–26   | F    |
| 27–35   | D    |
| 36–44   | L    |
| 45–53   | B    |

Each face is read left-to-right, top-to-bottom (index 4 is always the center, which never moves). Stickers are single-character color codes: `U R F D L B` based on the orient of the input cube.

A solved cube string:
```
UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDLLLLLLLLLBBBBBBBBB
```

---

## Public API — `Solver.py`

```python
from Solver import Solver

solver = Solver()
solver.load_state("UUUUUUUUU...")   # 54-char string representing the cube to be solved
moves = solver.solve()              # returns "R U R' U' ..." or raises CubeNotSolvableError
```

| Method | Description |
|--------|-------------|
| `load_state(s)` | Load cube from a 54-character face-string |
| `select_algorithm(name)` | Switch solving algorithm (currently defaults to `"CFOP"`) |
| `solve()` | Run the solver; returns a space-separated move string |
| `scramble(n)` | Apply an n-move random scramble (default 25) |
| `get_state_string()` | Return the current cube state as a 54-char string (used for exporting soloution) |
| `is_solved()` | Return `True` if the cube is in the solved state |

---

## Algorithm — CFOP

The solver implements a four-stage algorithm method **CFOP** (Cross → F2L → OLL → PLL), with U relating to the bottom face on an input cube and the cross solved on the D layer. This is done because the algorithms assume the user will solve the "top" face last, requiring permutation of U face. With the limitations of the solver robot, the solver treats the real bottom face as the cubes U face so that algorithms don't need to be translated.

### Stage 1 — Cross
This stage of the solving method requires human intuition. Because of this, a bredth first search is used to find a soloution to this step. The BFS inserts the four D-layer edges (DF → DR → DB → DL) one at a time, preserving already-solved edges. Maximum search depth is 9 moves. 

### Stage 2 — F2L (First Two Layers)
Four corner-edge pairs (FR → FL → BR → BL) are resolved using a per-slot lookup table built by a reverse BFS from a  solved state. Each BFS uses only composite move sequences preserving the D-cross and all previously solved slots, so no stored moveset can disturb earlier work. Up to three AUF (Augment Upper Face using U/U'/U2) pre-rotations are tried per slot if the direct signature is not found.

### Stage 3 — OLL (Orient Last Layer)
An 8-tuple orientation key (4 corner twists + 4 edge flips) is computed and looked up in a 64-entry table built  from `OLL.json`. The key is built to only consider where "U" face stickers are, so the same algorithm handles any U-layer piece arrangement for a given pattern without considering the exact piece. Up to three AUF (Augment Upper Face) rotations are tried if the key is not found directly to find the fingerprint without having to generate the 4 differnt orientations of the fingerprint.

### Stage 4 — PLL (Permute Last Layer)
A 12-element top-row fingerprint is computed and looked up in a 269-entry table built at startup from the 22 canonical PLL algorithms in `PLL.json`. The table enumerates all 16 pre-AUF and post-AUF combinations, so every reachable post-OLL state has a direct entry requiring no retry loop. This is done because for each OLL pattern, four seperate sticker combinations exist (one for each side edge colour). To generate the four PLL combinations, three seperate AUF rotations are used when adding a PLL algorithm to the lookup table.

---

## Interactive Debug Viewer

```
python Cube_Debug_Viewer.py
```

### Commands

| Command | Description |
|---------|-------------|
| `R U F L B` (etc.) | Apply one or more moves (space-separated, allows moves not compatible with robot) |
| `scramble [n]` | Random n-move scramble (default 25) |
| `reset` | Return to solved state |
| `history` | Print full move history |
| `solve` | Run full CFOP solver with per-stage output |
| `solve cross` | Run Cross stage only |
| `solve f2l` | Run F2L stage only (requires solved cross) |
| `solve oll` | Run OLL stage only (requires solved F2L) |
| `solve pll` | Run PLL stage only (requires solved OLL) |
| `q` / `quit` | Exit |

---

## Running Tests

```
python -m unittest Test_Cube_Debug_Viewer -v
```

The suite contains **35 tests** across five classes:

| Class | What it covers |
|-------|----------------|
| `TestMoveValidity` | All 18 moves accepted; invalid moves raise; prime/double variants correct |
| `TestScramble` | Cube is not solved after scramble; history length matches n; no consecutive same-face moves |
| `TestReset` | Cube returns to solved state; history cleared |
| `TestFullSolve` | Solver produces solved cube; deterministic for fixed seed; all solution tokens are valid moves |
| `TestStageSolve` | Each CFOP stage leaves the cube in the correct partial state; earlier stages are not disturbed |
| `TestCubeStateRepresentation` | 54 stickers; 9 of each color; centers never move; string round-trip; clone independence |

---

## Dependencies

- Python 3.8+
- Standard library only (`json`, `collections`, `copy`, `abc`, `random`, `os`)
- No third-party packages required

---

## Move Notation Reference

| Suffix | Meaning |
|--------|---------|
| *(none)* | 90° clockwise |
| `'` | 90° counterclockwise |
| `2` | 180° |

Face letters: **U** (top), **R** (right), **F** (front), **D** (bottom), **L** (left), **B** (back).