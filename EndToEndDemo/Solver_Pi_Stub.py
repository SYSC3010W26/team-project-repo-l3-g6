"""
============================================================
SYSC 3010 - End-to-End Demo: Solver Pi Stub
Author: Luke Grundy
============================================================
"""
from Base_Node import Node
import time

class Solver(Node):
    def handle_command(self, command, data):
        if command == "SOLVE":
            time.sleep(1)
            self.respond("R U R' U'")
        if command == "CRASH":
            print(f"[{self.name}] Simulating crash...")
            self.sock.close()
            exit(1)

if __name__ == "__main__":
    Solver("SOLVER")