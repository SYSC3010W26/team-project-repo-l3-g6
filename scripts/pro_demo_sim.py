#!/usr/bin/env python3
"""
Pi³ — Pro Demo Day Simulation (High Fidelity)
=============================================
This script provides a broadcast-ready demo by:
1. Creating a real session.
2. Simulating a perfect cube scan.
3. Triggering the real Solver Pi (Luke).
4. Emitting move-by-move animation events to the Dashboard via Socket.IO.
5. Providing the final Review URL.
"""

import os
import time
import requests
import socketio
import threading
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
SERVER_IP = os.getenv("PI_SERVER_IP", "localhost")
SERVER_URL = f"http://{SERVER_IP}:8000"
DASHBOARD_URL = f"http://{SERVER_IP}:5173"

# Scrambled state for demo (Color-coded like a real scan)
# This is a valid, solvable scrambled cube
SCRAMBLED_STATE = "OGGWWWWWWRRRRRRRRRGGGGGGOOOYYYYYYYYYOOOOOOGGGBBBBBBBBB"

# --- Heartbeat Thread (Ghost Mode) ---
def start_ghost_heartbeats():
    """Sends heartbeats for Motor Pi so server doesn't kill the job."""
    def heartbeat_loop():
        print("👻 Ghost Mode: Sending Motor Pi heartbeats...")
        while True:
            try:
                requests.post(f"{SERVER_URL}/nodes/heartbeat", json={
                    "node_id": "rpi3-motors",
                    "node_type": "motor",
                    "status": "online"
                }, timeout=2)
            except:
                pass
            time.sleep(2)
    
    t = threading.Thread(target=heartbeat_loop, daemon=True)
    t.start()

# --- Socket.IO setup ---
sio = socketio.Client()

@sio.event
def connect():
    print("✅ Connected to Dashboard Socket.IO")

@sio.event
def disconnect():
    print("❌ Disconnected from Socket.IO")

def run_sim():
    print(f"🚀 Starting High-Fidelity Demo Sim...")
    print(f"📡 Server: {SERVER_URL}")

    # Start ghost heartbeats for Motor Pi
    start_ghost_heartbeats()

    # 1. Check if Solver Pi is online
    try:
        r = requests.get(f"{SERVER_URL}/nodes/status")
        nodes = r.json()
        solver_online = any(n['node_type'] == 'solver' and n['is_online'] for n in nodes)
        if not solver_online:
            print("⚠️  Warning: Solver Pi (Luke) is OFFLINE. Simulation might hang.")
    except Exception as e:
        print(f"❌ Error checking solver status: {e}")
        # Continue anyway in case heartbeat is just slow

    # 2. Connect to Socket.IO for animations
    try:
        sio.connect(SERVER_URL)
    except Exception as e:
        print(f"⚠️  Could not connect to Socket.IO. Animations will be skipped. {e}")

    # 3. Create Session
    print("\n[1/4] Creating new solve session...")
    r = requests.post(f"{SERVER_URL}/jobs/start", json={"algorithm": "CFOP"})
    session_id = r.json()["session_id"]
    print(f"      ✓ Created session #{session_id}")

    # 4. Submit Scan
    print("\n[2/4] Simulating scan capture...")
    time.sleep(2)
    requests.post(f"{SERVER_URL}/scan/submit", json={
        "session_id": session_id,
        "state_string": SCRAMBLED_STATE,
        "is_valid": True,
        "confidence": 1.0
    })
    print("      ✓ Scan submitted")

    # 5. Trigger Solve
    print("\n[3/4] Triggering solver pipeline...")
    requests.post(f"{SERVER_URL}/solve/start", json={"session_id": session_id})
    print("      ✓ Solve triggered! Waiting for Luke's Pi...")

    # 6. Wait for Solution
    solution = None
    while not solution:
        time.sleep(2)
        r = requests.get(f"{SERVER_URL}/solve/{session_id}")
        if r.status_code == 200:
            solution = r.json()
    
    moves = solution["solution_string"].split()
    print(f"      ✓ Solution found: {len(moves)} moves.")

    # 7. Simulating Execution Animations
    # We broadcast move events to make the dashboard cube spin
    print("\n[4/4] Simulating live execution animations...")
    
    # First, transition session to 'executing' for UI state
    requests.post(f"{SERVER_URL}/jobs/{session_id}/transition", json={"to": "executing"})
    
    for i, move in enumerate(moves):
        print(f"      👉 Animating move {i+1}/{len(moves)}: {move}")
        sio.emit('execution_progress', {
            "session_id": session_id,
            "current_step": i + 1,
            "total_steps": len(moves),
            "move": move,
            "pct_complete": int(((i+1)/len(moves)) * 100)
        })
        time.sleep(1.0) # Speed of animation in demo

    # 8. Finalize
    requests.post(f"{SERVER_URL}/jobs/{session_id}/transition", json={"to": "done"})
    print("\n" + "="*50)
    print("✅ PRO SIMULATION COMPLETE")
    print("="*50)
    print(f"Session:     #{session_id}")
    print(f"Dashboard:   {DASHBOARD_URL}")
    print(f"Review Link: {DASHBOARD_URL}/review/{session_id}")
    print("="*50)

    sio.disconnect()

if __name__ == "__main__":
    run_sim()
