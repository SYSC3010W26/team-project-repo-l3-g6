"""
SYSC3010 - Pi Cubed Rubik's Cube Solver
Solver Algorithm Pi - Cube Debug Viewer
Group L3-G6

Author: Luke Grundy

Commands:
    U, R, F, D, L, B
    U', R', F', D', L', B'
    U2, R2, F2, D2, L2, B2

Extra commands:
    scramble <n>        - apply an n-move random scramble (default n=25)
    reset               - return cube to solved state
    history             - print the full move history
    solve               - run the full CFOP solver and animate the solution
    solve cross         - run only the Cross stage
    solve f2l           - run only the F2L stage
    solve oll           - run only the OLL stage
    solve pll           - run only the PLL stage
    q / quit            - exit the viewer
    
"""

import random


from Cube_State import Cube
from Algorithm_Selector import AlgorithmSelector

# ANSI helper
COLORS = {
    'U': '\033[97m',        # white
    'D': '\033[93m',        # yellow
    'F': '\033[92m',        # green
    'B': '\033[94m',        # blue
    'R': '\033[91m',        # red
    'L': '\033[38;5;208m',  # orange
}

RESET = '\033[0m'

MOVES = ["R","R'","R2","U","U'","U2","F","F'","F2",
         "L","L'","L2","D","D'","D2","B","B'","B2"]


class CubeDebugger:

    def __init__(self):
        self.cube = Cube()
        self.history = []

# ------------------------------------------------------------------
# Display
# ------------------------------------------------------------------

    def color(self, sticker):
        return COLORS.get(sticker, '') + sticker + RESET


    def display(self):

        state = self.cube.state

        def row(face, r):
            i = face * 9 + r * 3
            return [self.color(x) for x in state[i:i+3]]

        print("\n")

        # Print Top face "U"
        for r in range(3):
            print("       ", *row(0, r))

        # Print Left, Front, Right, and Back faces "L, F, R, B"
        for r in range(3):
            print(
                *row(4, r), " ",
                *row(2, r), " ",
                *row(1, r), " ",
                *row(5, r)
            )

        # Print Bottom face "D"
        for r in range(3):
            print("       ", *row(3, r))

        print("\n")

# ------------------------------------------------------------------
# Scramble and Solve
# ------------------------------------------------------------------

    def scramble(self, length=25): 
        """ Default scramble set at 25 moves. 25 is just above what competition scrambles are (20-22 moves) """

        scramble_moves = []
        last = None

        for i in range(length):

            move = random.choice(MOVES)

            while last and move[0] == last[0]: # prevents multiple of the same move in a row
                move = random.choice(MOVES)

            scramble_moves.append(move)
            last = move

        for m in scramble_moves:
            self.cube.apply_move(m)

        self.history.extend(scramble_moves)

        print("\nScramble:")
        print(" ".join(scramble_moves))


    def _build_algorithm(self):
        selector = AlgorithmSelector(self.cube.state[:], "CFOP")
        return selector.get_algorithm()


    def solve_stage(self, stage_name):
        stage = stage_name.lower()
        valid = {"cross", "f2l", "oll", "pll"}
        if stage not in valid:
            print(f"  Unknown stage '{stage}'. Valid stages: {', '.join(sorted(valid))}")
            return
 
        alg = self._build_algorithm()
        if alg is None:
            return
 
        stage_map = {
            "cross": ("Cross", alg.solve_cross),
            "f2l":   ("F2L",   alg.solve_f2l),
            "oll":   ("OLL",   alg.solve_oll),
            "pll":   ("PLL",   alg.solve_pll),
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
        """Run all four CFOP stages in sequence."""
        if self.cube.is_solved():
            print("  The cube is already solved.")
            return
 
        alg = self._build_algorithm()
        if alg is None:
            return
 
        # Each stage_fn calls the stage method on `alg` and returns its moves.
        # We patch the working state back onto self.cube after each stage so
        # the viewer stays in sync.
 
        def make_stage(method):
            def _fn():
                method()
                # Sync the algorithm's working state back to our cube
                self.cube.set_cube_state(alg._working[:])
                return alg.moves[len(self.history):]  # moves added this stage
            return _fn
 
        # We drive the stages manually so we can interleave the display.
        for stage_name, method in [
            ("Cross", alg.solve_cross),
            ("F2L",   alg.solve_f2l),
            ("OLL",   alg.solve_oll),
            ("PLL",   alg.solve_pll),
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
                self.cube    = Cube()
                self.history = []
                self.display()
                continue
 
            if cmd == "history":
                if self.history:
                    print(f"Move history ({len(self.history)} moves):")
                    # Print in rows of 20
                    for i in range(0, len(self.history), 20):
                        print(" ", " ".join(self.history[i:i+20]))
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
                    print("  Use: solve  |  solve cross  |  solve f2l  |  solve oll  |  solve pll")
                self.display()
                continue

            MOVES = cmd.split()
            try:
                for m in MOVES:
                    self.cube.apply_move(m)
                    self.history.append(m)
                self.display()
            except Exception as e:
                print(f"  Invalid move: {e}")


if __name__ == "__main__":
    CubeDebugger().run()