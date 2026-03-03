"""
============================================================
SYSC 3010 - End-to-End Demo: Motor Pi Stub
Author: Luke Grundy
============================================================
"""
from Base_Node import Node
import time

class Motor(Node):
    def handle_command(self, command, data):
        if command == "EXECUTE":
            time.sleep(1)
            self.respond("MOVES_EXECUTED")
        if command == "CRASH":
            print(f"[{self.name}] Simulating crash...")
            self.sock.close()
            exit(1)

if __name__ == "__main__":
    Motor("MOTOR")