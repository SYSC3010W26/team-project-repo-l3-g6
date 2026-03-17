"""
SYSC3010 - Pi Cubed Rubik's Cube Solver
Solver Algorithm Pi - Top Level Solver Module
Group L3-G6

Author: Luke Grundy

Description:
This program implements solver algorithms for a standard
3x3 Rubik's Cube. The program represents the cubes state in
a compact database-storable format and generates a string of move
notations to transform the cube toward the solved state.

To Do list:
    - Cube state representation DONE
    - Move definitions and permutations DONE
    - Standard Rubik's Cube move notation (U, D, L, R, F, B, + primes and doubles) DONE
    - Scramble input parsing 
    - Move execution and state transitions
    - Solver algorithm (e.g., beginner method / CFOP / search-based)
    - Solution output in standard notation
    - Optional state serialization for database storage

"""

from Algorithm_Selector import AlgorithmSelector
import Cube_State
    

class Solver:
    """SYSC3010 - Pi Cubed Rubik's Cube Solver
        Solver Algorithm Pi - Top Level Solver Module"""
    
    def __init__(self):
        """Initialize the solver with a solved cube and algorithm selector."""
        self.cube = Cube_State.Cube()
        self.selector = AlgorithmSelector(self.cube.state, "CFOP")
        self.algorithm = self.selector.get_algorithm()

    def loadState(self,stateString):
        """Load cube state from a 54-character string."""
        if len(stateString)!=54:
            raise ValueError("Cube state must be 54 chars")

        self.cube.set_cube_state(list(stateString))

    def selectAlgorithm(self,type):
        """ Selects the solving algorithm based on the provided type string. """
        self.selector = AlgorithmSelector(self.cube.state[:], type)
        self.algorithm = self.selector.get_algorithm()
        
    def solve(self):
        """ Generates a sequence of moves to solve the cube from its current state. """
        if not self.algorithm:
            raise Exception("No algorithm selected")

        return self.algorithm.solve()

