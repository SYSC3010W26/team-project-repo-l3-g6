"""
SYSC3010 - Pi Cubed Rubik's Cube Solver
Solver Algorithm Pi - Cube State Module
Group L3-G6

Author: Luke Grundy

Purpose:
    This module is used to represent the state of a given Rubik's cube and to apply moves to that state.

Design Goals:
    - Represent the cube state in a way that allows for easy manipulation and database storage.

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
    Indices 4, 13, 22, 31, 40, 49 are centers.
    Never modified by permutations.

Move Convention:
    Standard turns rotate the cube clockwise while looking directly at the indicated face (U, R, F, D, L, B).
    A prime (') indicates counterclockwise, and a '2' indicates a 180-degree turn.

Supported Moves:
    U, R, F, D, L, B
    U', R', F', D', L', B'
    U2, R2, F2, D2, L2, B2

"""

# Import necessary libraries

import Permutation_Table

# Define the Cube class to represent the state of the cube
class Cube:
    def __init__(self):
        # Initialize the cube in a solved state
        self.state = self.create_solved_state()

    def create_solved_state(self):
        # Create a representation of the solved cube state
        # Each face is represented by a list of 9 stickers (excluding the center piece)
        # the 9 stickers are ordered in from top-left to bottom-right (0-8) with the center pice at index 4
        return [
                'U','U','U','U','U','U','U','U','U',   # 0–8
                'R','R','R','R','R','R','R','R','R',   # 9–17
                'F','F','F','F','F','F','F','F','F',   # 18–26
                'D','D','D','D','D','D','D','D','D',   # 27–35
                'L','L','L','L','L','L','L','L','L',   # 36–44
                'B','B','B','B','B','B','B','B','B'    # 45–53
            ]
        
    
    def set_cube_state(self, new_state):
        self.state = new_state

    def apply_move(self, perm):
        # Apply a permutation to the cube state
        if perm not in Permutation_Table.MOVES:
            raise ValueError(f"Invalid move: {perm}")

        self.state = Permutation_Table.apply_move(self.state,Permutation_Table.MOVES[perm])

    def apply_sequence(self, move_sequence):
        # Apply a sequence of moves to the cube state
        for move in move_sequence:
            self.apply_move(move)

    def clone(self):
        # Create a copy of the cube state
        new_cube = Cube()
        new_cube.set_cube_state(self.state.copy())
        return new_cube

    def is_solved(self):
        # Check if the cube is in a solved state
        faces = [self.state[i:i+9] for i in range(0, 54, 9)]
        for face in faces:
            if len(set(face)) != 1:
                return False
        return True
    
    def __str__(self):
        # Return a string representation of the cube state
        return ''.join(self.state)
    