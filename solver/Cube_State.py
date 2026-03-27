"""
SYSC3010 - Pi Cubed | Group L3-G6 | Author: Luke Grundy

Represents the state of a 3x3 Rubik's Cube as a 54-element list and applies
moves to it. Facelet order: U(0-8), R(9-17), F(18-26), D(27-35), L(36-44),
B(45-53). Each face is indexed 0-8 top-left to bottom-right.
"""

import Permutation_Table


class Cube:
    def __init__(self):
        self.state = self.create_solved_state()

    def create_solved_state(self):
        return (
            ['U'] * 9 + ['R'] * 9 + ['F'] * 9 +
            ['D'] * 9 + ['L'] * 9 + ['B'] * 9
        )

    def set_cube_state(self, new_state):
        self.state = new_state

    def apply_move(self, perm):
        if perm not in Permutation_Table.MOVES:
            raise ValueError(f"Invalid move: {perm}")
        
        self.state = Permutation_Table.apply_move(self.state, Permutation_Table.MOVES[perm])

    def apply_sequence(self, move_sequence):
        for move in move_sequence:
            self.apply_move(move)

    def clone(self):
        new_cube = Cube()
        new_cube.set_cube_state(self.state.copy())
        return new_cube

    def is_solved(self):
        for i in range(0, 54, 9):
            if len(set(self.state[i:i+9])) != 1:
                return False
        return True

    def cube_to_string(self):
        return "".join(self.state)

    @staticmethod
    def string_to_cube(s):
        return list(s)