"""
SYSC3010 - Pi Cubed | Group L3-G6 | Author: Luke Grundy

Selects and initializes a solving algorithm by name. Currently supports CFOP.
"""

from CFOP.CFOP_Algorithm import CFOP_Algorithm


class AlgorithmSelector:

    ALGORITHMS = {
        "CFOP": CFOP_Algorithm,
    }

    def __init__(self, cube_state, algorithm_name):
        self.cube_state = cube_state
        self.algorithm_name = algorithm_name
        self.algorithm = None

    def get_algorithm(self):
        cls = self.ALGORITHMS.get(self.algorithm_name.upper())
        if cls is None:
            raise ValueError(f"Unsupported algorithm: {self.algorithm_name}")
        self.algorithm = cls(self.cube_state)
        return self.algorithm

    def solve(self):
        if self.algorithm is None:
            self.get_algorithm()
        return self.algorithm.solve()
