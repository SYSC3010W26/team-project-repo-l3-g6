"""
SYSC3010 - Pi Cubed | Group L3-G6 | Author: Luke Grundy

Abstract base class for Rubik's Cube solving algorithms. Subclasses implement
solve() to return a move sequence that solves the given cube state.
"""

from abc import ABC, abstractmethod


class CubeAlgorithm(ABC):

    def __init__(self, cube_state):
        self.cube_state = cube_state
        self.moves = []

    @abstractmethod
    def solve(self) -> list:
        pass