"""
============================================================
SYSC 3010 - End-to-End Demo: Scanner Pi Stub
Author: Luke Grundy
============================================================
"""
from Base_Node import Node
import time

class Scanner(Node):
    def handle_command(self, command, data):
        if command == "SCAN":
            time.sleep(1)
            self.respond("CUBE_STATE_123")
        if command == "CRASH":
            print(f"[{self.name}] Simulating crash...")
            self.sock.close()
            exit(1)

if __name__ == "__main__":
    Scanner("SCANNER")