#!/usr/bin/env python3
"""
Pi³ — Full E2E Demo Simulation
===============================
Complete end-to-end demo using REAL solver:
1. Creates a session
2. Submits a scrambled cube scan
3. Triggers solve (Solver Pi solves it)
4. Waits for solution
5. Animates move-by-move on Dashboard

Prerequisites:
- Server must be running on SERVER_IP
- Solver Pi must be connected and running solver_listener.py
"""

import os
import sys
import time
import requests
import socketio
import threading

# Add solver module to path so we can generate a valid scramble
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "solver"))
from Solver import Solver

from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
SERVER_IP = os.getenv("PI_SERVER_IP", "localhost")
SERVER_URL = f"http://{SERVER_IP}:8000"
DASHBOARD_URL = f"http://{SERVER_IP}:5173"


# --- Heartbeat Thread (Ghost Mode for Motor Pi) ---
def start_ghost_heartbeats():
    """Sends heartbeats for Motor Pi so server doesn't kill the job."""

    def heartbeat_loop():
        print("👻 Ghost Mode: Sending Motor Pi heartbeats...")
        while True:
            try:
                requests.post(
                    f"{SERVER_URL}/nodes/heartbeat",
                    json={
                        "node_id": "rpi3-motors",
                        "node_type": "motor",
                        "status": "online",
                    },
                    timeout=2,
                )
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


def wait_for_server(timeout=30):
    """Wait for server to be responsive."""
    print("⏳ Waiting for server...")
    for i in range(timeout):
        try:
            r = requests.get(f"{SERVER_URL}/", timeout=2)
            if r.status_code == 200:
                print("✅ Server is ready!")
                return True
        except:
            pass
        time.sleep(1)
    return False


def get_scrambled_cube():
    """Generate a scrambled cube using the real Solver module."""
    solver = Solver()
    solver.load_state("UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB")
    scramble = solver.scramble(length=12)  # 12 moves scramble
    state = solver.get_state_string()
    return state, scramble


def run_e2e_demo():
    print(f"\n{'=' * 60}")
    print("🚀 Pi³ FULL E2E DEMO SIMULATION")
    print(f"{'=' * 60}")
    print(f"📡 Server:    {SERVER_URL}")
    print(f"🖥️  Dashboard: {DASHBOARD_URL}")
    print(f"{'=' * 60}\n")

    # Connect to Socket.IO
    try:
        sio.connect(SERVER_URL, wait_timeout=10)
    except Exception as e:
        print(f"⚠️  Could not connect to Socket.IO: {e}")

    # Start ghost heartbeats for Motor Pi
    start_ghost_heartbeats()

    # Wait for server
    if not wait_for_server():
        print("❌ Server not responding. Exiting.")
        return

    # ─── Step 1: Create Session ───
    print("\n📋 [1/5] Creating new solve session...")
    r = requests.post(f"{SERVER_URL}/jobs/start", json={"algorithm": "CFOP"})
    if r.status_code != 201:
        print(f"❌ Failed to create session: {r.text}")
        return
    session_id = r.json()["session_id"]
    print(f"      ✅ Session #{session_id} created")

    # ─── Step 2: Generate & Submit Scan ───
    print("\n📷 [2/5] Generating scrambled cube...")

    # Get a valid scrambled cube state
    state_string, scramble = get_scrambled_cube()
    print(f"      🔀 Scramble: {scramble}")
    print(f"      📦 State: {state_string[:30]}...")

    r = requests.post(
        f"{SERVER_URL}/scan/submit",
        json={
            "session_id": session_id,
            "state_string": state_string,
            "is_valid": True,
            "confidence": 0.95,
        },
    )
    if r.status_code != 200:
        print(f"❌ Failed to submit scan: {r.text}")
        return
    print(f"      ✅ Cube scanned and validated!")

    # Emit scan complete event
    if sio.connected:
        sio.emit("scan_complete", {"session_id": session_id})
        sio.emit(
            "job_state_update",
            {"session_id": session_id, "status": "scanning", "node_status": {}},
        )

    # ─── Step 3: Trigger Solve ───
    print("\n🧠 [3/5] Starting solver...")

    r = requests.post(f"{SERVER_URL}/solve/start", json={"session_id": session_id})
    if r.status_code != 200:
        print(f"❌ Failed to start solve: {r.text}")
        return
    print(f"      ✅ Solver triggered! (Real solver will pick this up)")

    if sio.connected:
        sio.emit(
            "job_state_update",
            {"session_id": session_id, "status": "solving", "node_status": {}},
        )

    # ─── Step 4: Wait for Solution ───
    print("\n⏳ [4/5] Waiting for real solver to compute solution...")
    print("      (Luke's Pi is solving this...)\n")

    solution = None
    max_wait = 120  # 2 minutes max
    start_time = time.time()

    while not solution:
        if time.time() - start_time > max_wait:
            print("❌ Timeout waiting for solution!")
            return

        time.sleep(2)
        try:
            r = requests.get(f"{SERVER_URL}/solve/{session_id}", timeout=5)
            if r.status_code == 200:
                solution = r.json()
                print(f"\n      ✅ SOLUTION FOUND!")
                print(f"      📊 Algorithm: {solution['algorithm_used']}")
                print(f"      📈 Moves: {solution['move_count']}")
                print(f"      🔧 Solution: {solution['solution_string'][:50]}...")
        except Exception as e:
            pass

        # Show progress dots
        elapsed = int(time.time() - start_time)
        print(f"      ⏳ Solver working... ({elapsed}s)", end="\r")

    moves = solution["solution_string"].split()
    print(f"\n\n      🎯 Solution: {' '.join(moves)}")

    # ─── Step 5: Animate Execution ───
    print(f"\n🎬 [5/5] Animating {len(moves)} moves on Dashboard...")

    # Transition to executing
    requests.post(
        f"{SERVER_URL}/jobs/{session_id}/transition", json={"to": "executing"}
    )

    if sio.connected:
        sio.emit(
            "job_state_update",
            {"session_id": session_id, "status": "executing", "node_status": {}},
        )

    # Create execution run
    requests.post(
        f"{SERVER_URL}/execute/start",
        json={
            "session_id": session_id,
            "solution_id": solution["solution_id"],
            "motor_node_id": "motor-node",
        },
    )

    # Animate each move
    for i, move in enumerate(moves):
        pct = int(((i + 1) / len(moves)) * 100)
        print(f"      👉 Move {i + 1}/{len(moves)}: {move} ({pct}%)")

        if sio.connected:
            sio.emit(
                "execution_progress",
                {
                    "session_id": session_id,
                    "current_step": i + 1,
                    "total_steps": len(moves),
                    "move": move,
                    "pct_complete": pct,
                },
            )

        # Report progress to backend
        requests.post(
            f"{SERVER_URL}/execute/progress",
            json={
                "session_id": session_id,
                "run_id": 1,
                "current_step": i + 1,
                "total_steps": len(moves),
                "move": move,
            },
        )

        time.sleep(0.8)  # Animation speed

    # ─── Complete ───
    print("\n🎉 Completing solve...")

    requests.post(
        f"{SERVER_URL}/execute/complete",
        json={"session_id": session_id, "run_id": 1, "status": "success"},
    )
    requests.post(f"{SERVER_URL}/jobs/{session_id}/transition", json={"to": "done"})

    if sio.connected:
        sio.emit(
            "job_state_update",
            {"session_id": session_id, "status": "done", "node_status": {}},
        )

    # ─── Summary ───
    print(f"\n{'=' * 60}")
    print("✅ E2E DEMO COMPLETE!")
    print(f"{'=' * 60}")
    print(f"📋 Session ID:   #{session_id}")
    print(f"🔧 Algorithm:   {solution['algorithm_used']}")
    print(f"📊 Moves:       {len(moves)}")
    print(f"🎯 Solution:    {solution['solution_string']}")
    print(f"🔀 Scramble:    {scramble}")
    print(f"{'=' * 60}")
    print(f"🌐 Dashboard:   {DASHBOARD_URL}")
    print(f"📝 Review:      {DASHBOARD_URL}/review/{session_id}")
    print(f"{'=' * 60}\n")

    if sio.connected:
        sio.disconnect()


if __name__ == "__main__":
    run_e2e_demo()
