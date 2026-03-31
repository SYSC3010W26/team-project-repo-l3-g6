#!/usr/bin/env python3
"""
SYSC3010 L3-G6 — Solver Pi Polling Listener
Author: Antigravity (Agent)

Polls the backend API for solve sessions in the 'solving' state,
computes the solution using the local Solver class, and POSTs
the solution back to the API.
"""

import os
import time
import logging
import requests
from typing import Optional, Dict
import sys
from pathlib import Path

# Add the script's directory to sys.path to allow importing local Solver module
sys.path.insert(0, str(Path(__file__).parent))

# Import the Solver class from the same directory
from Solver import Solver, CubeNotSolvableError

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "2.0"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────

def setup_logging() -> logging.Logger:
    logger = logging.getLogger("solver_listener")
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

logger = setup_logging()

# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def transform_colors_to_faces(state_string: str) -> str:
    """
    Map scanner color letters (W, Y, R, O, B, G) to solver face letters (U, R, F, D, L, B).
    
    The mapping is determined by the center sticker of each face in the 54-char string.
    Face order in 54-char string: U, R, F, D, L, B (9 stickers each)
    Center indices: 4, 13, 22, 31, 40, 49
    """
    if len(state_string) != 54:
        raise ValueError(f"State string must be 54 characters, got {len(state_string)}")

    # Centers define which color is which face
    # Index 4  -> U
    # Index 13 -> R
    # Index 22 -> F
    # Index 31 -> D
    # Index 40 -> L
    # Index 49 -> B
    mapping = {
        state_string[4]:  "U",
        state_string[13]: "R",
        state_string[22]: "F",
        state_string[31]: "D",
        state_string[40]: "L",
        state_string[49]: "B"
    }
    
    # Ensure all 6 colors are present in the mapping (centers must be unique)
    if len(mapping) != 6:
        centers = [state_string[i] for i in [4, 13, 22, 31, 40, 49]]
        raise ValueError(f"Cube centers are not unique: {centers}. Cannot determine color mapping.")

    # Apply mapping
    face_string = "".join(mapping.get(c, c) for c in state_string)
    return face_string

# ─────────────────────────────────────────────────────────────────────────────
# CORE LOGIC
# ─────────────────────────────────────────────────────────────────────────────

class SolverListener:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.solver = Solver()

    def poll_for_jobs(self):
        """Find sessions with status 'solving'."""
        try:
            print(f"🔍 Polling {self.base_url}/jobs...")
            response = requests.get(f"{self.base_url}/jobs", timeout=5.0)
            response.raise_for_status()
            jobs = response.json()
            active = [j for j in jobs if j["status"] == "solving"]
            if active:
                print(f"✅ Found {len(active)} active jobs!")
            return active
        except Exception as e:
            print(f"❌ Error polling for jobs: {e}")
            return []

    def get_cube_state(self, session_id: int) -> Optional[str]:
        """Fetch the most recent scan for a session."""
        try:
            response = requests.get(f"{self.base_url}/scan/{session_id}", timeout=5.0)
            response.raise_for_status()
            data = response.json()
            return data["state_string"]
        except Exception as e:
            logger.error(f"Error fetching cube state for session {session_id}: {e}")
            return None

    def submit_solution(self, session_id: int, algorithm: str, solution: str):
        """POST the solution back to the API."""
        move_count = len(solution.split()) if solution else 0
        payload = {
            "session_id": session_id,
            "algorithm_used": algorithm,
            "move_count": move_count,
            "solution_string": solution
        }
        try:
            response = requests.post(f"{self.base_url}/solve/submit", json=payload, timeout=5.0)
            response.raise_for_status()
            logger.info(f"✓ Solution submitted for session {session_id} ({move_count} moves)")
            return True
        except Exception as e:
            logger.error(f"Error submitting solution for session {session_id}: {e}")
            return False

    def process_job(self, job: Dict):
        session_id = job["session_id"]
        algorithm = job["selected_algorithm"]
        
        print(f"🧠 Processing session {session_id} (Algorithm: {algorithm})...")
        
        state_string = self.get_cube_state(session_id)
        if not state_string:
            print(f"⚠️  Could not retrieve cube state for session {session_id}. Skipping.")
            return

        try:
            # Transform colors to face letters
            print(f"🎨 Transforming colors: {state_string}")
            face_string = transform_colors_to_faces(state_string)
            print(f"🧩 Face string: {face_string}")
            
            # Load and solve
            self.solver.select_algorithm(algorithm)
            self.solver.load_state(face_string)
            print(f"⚡ Running {algorithm} solver...")
            solution = self.solver.solve()
            print(f"🎉 Solution found! {solution}")
            
            # Submit
            self.submit_solution(session_id, algorithm, solution)
            print(f"🏁 Solution submitted to backend.")
            logger.error(f"Cube not solvable for session {session_id}: {e}")
            # Optional: Transition session to 'error' status
            self.report_error(session_id, str(e))
        except Exception as e:
            logger.exception(f"Unexpected error solving session {session_id}: {e}")
            self.report_error(session_id, str(e))

    def report_error(self, session_id: int, message: str):
        """Transition session to 'error' status."""
        try:
            requests.post(
                f"{self.base_url}/jobs/{session_id}/transition",
                json={"to": "error"},
                timeout=5.0
            )
            # Log to the system log if endpoint exists
            # (Assuming /logs might exist but we'll stick to job transition for now)
        except Exception as e:
            logger.error(f"Failed to report error for session {session_id}: {e}")

    def run(self):
        logger.info(f"Solver Listener started. Polling {self.base_url} every {POLL_INTERVAL}s")
        while True:
            jobs = self.poll_for_jobs()
            for job in jobs:
                self.process_job(job)
            time.sleep(POLL_INTERVAL)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    listener = SolverListener(API_BASE_URL)
    try:
        listener.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
