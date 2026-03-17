"""
SYSC3010 - Pi Cubed Rubik's Cube Solver
Solver Algorithm Pi - Cube Algorithm Module
Group L3-G6

Author: Luke Grundy

Purpose:
    This module is uesed as an interface for implemented cube solving algorithms.
    It provides a standardized way to access and execute a solve() function, 
    which takes a cube state as input and returns a sequence of moves to solve the cube.

"""

from abc import ABC, abstractmethod

class CubeAlgorithm(ABC):
    """ Abstract base class for Rubik's Cube solving algorithms. """

    def __init__(self, cube_state):
        """ Initialize algorithm with cube state. """
        self.cube_state = cube_state
        self.moves = []

    @abstractmethod
    def solve(self) -> list:
        """ Compute solution moves. """
        pass

    def get_moves(self):
        """ Return generated move sequence. """
        return self.moves