"""
SYSC3010 - Pi Cubed Rubik's Cube Solver
Solver Algorithm Pi - Algorithm Selector Module
Group L3-G6

Author: Luke Grundy

Purpose:
    This module is used to select the desired solving algorithm based on a given input.
    getAlgorithm() takes a string and returns the corresponding solving algorithm method (Begining with CFOP, more to be implemented depending on available time).

"""

# Import Algorithm Implementations
from CFOP.CFOP_Algorithm import CFOP_Algorithm

class AlgorithmSelector:
    """ Responsible for selecting and executing the requested cube algorithm. """

    ALGORITHMS = {
        "CFOP": CFOP_Algorithm,
    }

    def __init__(self, cube_state, algorithm_name):

        self.cube_state = cube_state
        self.algorithm_name = algorithm_name
        self.algorithm = None

    def get_algorithm(self):
        """ Initialize the requested algorithm. """

        cls = self.ALGORITHMS.get(self.algorithm_name.upper())
        if cls is None:
            raise ValueError(f"Unsupported algorithm: {self.algorithm_name}")
        self.algorithm = cls(self.cube_state)
        return self.algorithm

    def solve(self):
        """ Run the selected algorithm and return solution moves. """

        if self.algorithm is None:
            self.get_algorithm()
        return self.algorithm.solve()