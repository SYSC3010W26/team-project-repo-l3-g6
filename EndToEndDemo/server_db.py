"""
============================================================
SYSC 3010 - End-to-End Demo: Server Database
Author: Luke Grundy
============================================================
"""
import socket
import threading
import json
import time

HOST = "0.0.0.0"
PORT = 5000
HEARTBEAT_TIMEOUT = 5

clients = {}
heartbeats = {}
lock = threading.Lock()

def handle_client(conn, addr):
    """Handles incoming messages from a client node. Updates heartbeats and prints responses."""
    try:
        data = conn.recv(1024).decode()
        msg = json.loads(data)

        if msg["type"] == "REGISTER":
            node = msg["node"]
            with lock:
                clients[node] = conn
                heartbeats[node] = time.time()
            print(f"[DB] {node} registered from {addr}")

        while True:
            data = conn.recv(1024).decode()
            if not data:
                break

            msg = json.loads(data)

            if msg["type"] == "HEARTBEAT":
                with lock:
                    heartbeats[msg["node"]] = time.time()

            elif msg["type"] == "RESPONSE":
                print(f"[DB] Response from {msg['node']}: {msg['data']}")

    except:
        pass
    finally:
        conn.close()

def heartbeat_monitor():
    """Monitors heartbeats from all registered nodes and removes any that have timed out."""
    while True:
        time.sleep(1)
        now = time.time()
        with lock:
            for node, last in list(heartbeats.items()):
                if now - last > HEARTBEAT_TIMEOUT:
                    print(f"[DB] {node} HEARTBEAT TIMEOUT")
                    del heartbeats[node]

def send_command(node, command, payload=None):
    """Sends a command to a specific node if it is registered."""
    if node in clients:
        msg = {
            "type": "COMMAND",
            "command": command,
            "data": payload
        }
        clients[node].send(json.dumps(msg).encode())

def start_server():
    """Starts the server and listens for incoming client connections. creates a thread for each client and a separate thread for monitoring heartbeats."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print("[DB] Server running")

    threading.Thread(target=heartbeat_monitor, daemon=True).start()

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()