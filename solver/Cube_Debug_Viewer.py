"""
SYSC3010 - Pi Cubed | Group L3-G6 | Author: Luke Grundy

Interactive debug viewer for the Rubik's Cube solver. Accepts standard move
notation and the following commands:

    scramble [n]   - random n-move scramble (default 25)
    reset          - return to solved state
    history        - print move history
    solve          - run full CFOP solver
    solve cross/f2l/oll/pll - run a single stage
    q / quit       - exit
"""

import random

from Cube_State import Cube
from Algorithm_Selector import AlgorithmSelector

COLORS = {
    "U": "\033[97m",  # white
    "D": "\033[93m",  # yellow
    "F": "\033[92m",  # green
    "B": "\033[94m",  # blue
    "R": "\033[91m",  # red
    "L": "\033[38;5;208m",  # orange
}
RESET = "\033[0m"

# Standard move notation for scrambling. D moves exluded for compatibillity with motor

MOVES = ["R","R'","R2","U","U'","U2","F","F'","F2","L","L'","L2","B","B'","B2",]

class CubeDebugger:

    def __init__(self):
        self.cube = Cube()
        self.history = []

    def color(self, sticker):
        return COLORS.get(sticker, "") + sticker + RESET

    def display(self):
        """Prints the cube state in a human-readable format."""
        state = self.cube.state

        def row(face, r):
            i = face * 9 + r * 3
            return [self.color(x) for x in state[i : i + 3]]

        print("\n")
        for r in range(3):
            print("       ", *row(0, r))
        for r in range(3):
            print(*row(4, r), " ", *row(2, r), " ", *row(1, r), " ", *row(5, r))
        for r in range(3):
            print("       ", *row(3, r))
        print("\n")

    def scramble(self, length=25):
        """Applies a random scramble of the given length to the cube(default = 25)."""
        scramble_moves = []
        last = None
        for i in range(length):
            move = random.choice(MOVES)
            while (
                last and move[0] == last[0]
            ):  # prevents multiple of the same move in a row
                move = random.choice(MOVES)
            scramble_moves.append(move)
            last = move
        for m in scramble_moves:
            self.cube.apply_move(m)
        self.history.extend(scramble_moves)
        print("\nScramble:")
        print(" ".join(scramble_moves))

    def _build_algorithm(self):
        """Initializes the CFOP algorithm with the current cube state."""
        selector = AlgorithmSelector(self.cube.state[:], "CFOP")
        return selector.get_algorithm()

    def solve_stage(self, stage_name):
        """Runs a single stage of the CFOP algorithm and updates the cube state. used for debugging specific stages."""
        stage = stage_name.lower()
        valid = {"cross", "f2l", "oll", "pll"}
        if stage not in valid:
            print(
                f"  Unknown stage '{stage}'. Valid stages: {', '.join(sorted(valid))}"
            )
            return

        alg = self._build_algorithm()
        stage_map = {
            "cross": ("Cross", alg.solve_cross),
            "f2l": ("F2L", alg.solve_f2l),
            "oll": ("OLL", alg.solve_oll),
            "pll": ("PLL", alg.solve_pll),
        }
        label, method = stage_map[stage]

        before = len(alg.moves)
        method()
        stage_moves = alg.moves[before:]
        self.cube.set_cube_state(alg._working[:])

        print(f"\n  {label} Stage:")
        if not stage_moves:
            print("  (no moves needed)")
            self.display()
            return

        self.history.extend(stage_moves)
        self.display()
        print(f" {len(stage_moves)} Moves: {' '.join(stage_moves)}")

    def full_solve(self):
        """Runs the full CFOP algorithm and updates the cube state. runs in stages to show progress."""
        if self.cube.is_solved():
            print("  The cube is already solved.")
            return

        alg = self._build_algorithm()

        for stage_name, method in [
            ("Cross", alg.solve_cross),
            ("F2L", alg.solve_f2l),
            ("OLL", alg.solve_oll),
            ("PLL", alg.solve_pll),
        ]:
            before = len(alg.moves)
            method()
            stage_moves = alg.moves[before:]
            self.cube.set_cube_state(alg._working[:])

            print(f"\n  {stage_name} Stage:")
            if not stage_moves:
                print("  (no moves needed)")
                self.display()
                continue

            self.history.extend(stage_moves)
            self.display()
            print(f" {len(stage_moves)} Moves: {' '.join(stage_moves)}")

        print(f"\nSolution complete!  Total moves: {len(alg.moves)}")

    def run(self):
        print("Rubik's Cube Debug Viewer")
        print("─" * 40)
        print("Moves : R L U D F B")
        print("Add ' for prime  |  Add 2 for double")
        print("Separate multiple moves with spaces")
        print()
        print("Commands:")
        print("  scramble [n]  - random scramble (default 25 moves)")
        print("  reset         - return cube to solved state")
        print("  history       - print move history")
        print("  solve         - run full CFOP solver")
        print("  solve cross   - run Cross stage only")
        print("  solve f2l     - run F2L stage only (Only works if Cross is solved)")
        print("  solve oll     - run OLL stage only (Only works if F2L is solved)")
        print("  solve pll     - run PLL stage only (Only works if OLL is solved)")
        print("  q / quit      - exit")
        print()

        self.display()

        # --- main interaction loop ---

        while True:
            try:
                cmd = input("Enter move(s): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                break

            if not cmd:
                continue

            if cmd in ("q", "quit"):
                print("Exiting.")
                break

            if cmd == "reset":
                self.cube = Cube()
                self.history = []
                self.display()
                continue

            if cmd == "history":
                if self.history:
                    print(f"Move history ({len(self.history)} moves):")
                    for i in range(0, len(self.history), 20):
                        print(" ", " ".join(self.history[i : i + 20]))
                else:
                    print("  (no moves yet)")
                continue

            if cmd.startswith("scramble"):
                parts = cmd.split()
                length = 25
                if len(parts) == 2:
                    try:
                        length = int(parts[1])
                        if length < 1:
                            raise ValueError
                    except ValueError:
                        print(f"  Invalid scramble length '{parts[1]}'. Using 25.")
                        length = 25
                self.scramble(length)
                self.display()
                continue

            if cmd.startswith("solve"):
                parts = cmd.split()
                if len(parts) == 1:
                    self.full_solve()
                elif len(parts) == 2:
                    self.solve_stage(parts[1])
                else:
                    print(
                        "  Use: solve  |  solve cross  |  solve f2l  |  solve oll  |  solve pll"
                    )
                self.display()
                continue

            tokens = cmd.split()
            try:
                for m in tokens:
                    self.cube.apply_move(m)
                    self.history.append(m)
                self.display()
            except Exception as e:
                print(f"  Invalid move: {e}")


if __name__ == "__main__":
    CubeDebugger().run()
