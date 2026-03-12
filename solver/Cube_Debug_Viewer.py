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
    scramble
    reset
    history
    quit
    
"""

import random
from Cube_State import Cube


# ANSI colors
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

    def run(self):

        print("Rubik's Cube Debug Viewer")
        print("------------------------")
        print("Moves: R L U D F B")
        print("Put a space between moves to apply multiple at once")
        print("Add ' for prime  |  Add 2 for double")
        print("Commands: scramble, reset, history, q\n")

        self.display()

        while True:

            cmd = input("Enter move(s): ").strip()

            if cmd == "quit":
                break

            if cmd == "reset":
                self.cube = Cube()
                self.history = []
                self.display()
                continue

            if cmd == "scramble":
                self.scramble()
                self.display()
                continue

            if cmd == "history":
                print("Move history:")
                print(" ".join(self.history))
                continue

            moves = cmd.split()

            try:

                for m in moves:
                    self.cube.apply_move(m)
                    self.history.append(m)

                self.display()

            except Exception as e:
                print("Invalid move:", e)


if __name__ == "__main__":
    CubeDebugger().run()