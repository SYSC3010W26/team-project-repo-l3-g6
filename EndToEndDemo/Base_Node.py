"""
============================================================
SYSC 3010 - End-to-End Demo: Base Node Class
Author: Luke Grundy
============================================================
"""
import socket
import threading
import json
import time

SERVER = "192.168.1.1"  #server_db ip address
PORT = 5000
HEARTBEAT_INTERVAL = 2 

class Node:
    def __init__(self, name):
        self.name = name
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((SERVER, PORT))

        self.register()
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()
        self.listen()

    def register(self):
        """Sends a registration message to the server when the node starts up."""
        msg = {"type": "REGISTER", "node": self.name}
        self.sock.send(json.dumps(msg).encode())

    def heartbeat_loop(self):
        """Sends heartbeat messages at regular intervals to let the server know this node is alive."""
        while True:
            time.sleep(HEARTBEAT_INTERVAL)
            msg = {"type": "HEARTBEAT", "node": self.name}
            self.sock.send(json.dumps(msg).encode())

    def listen(self):
        """Listens for incoming commands from the server and dispatches them to thehandler."""
        while True:
            data = self.sock.recv(1024).decode()
            if not data:
                break

            msg = json.loads(data)

            if msg["type"] == "COMMAND":
                self.handle_command(msg["command"], msg["data"])

    def handle_command(self, command, data):
        """Override this method in subclasses to handle specific commands."""
        pass

    def respond(self, data):
        """Sends a response back to the server."""
        msg = {
            "type": "RESPONSE",
            "node": self.name,
            "data": data
        }
        self.sock.send(json.dumps(msg).encode())