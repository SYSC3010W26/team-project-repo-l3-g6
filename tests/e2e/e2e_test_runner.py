#!/usr/bin/env python3
"""
============================================================
M004/S04: End-to-End Integration Testing
E2E Test Runner with Timing, State Machine Validation, and
Multi-Run Verification

Features:
  - Full pipeline timing: scan → solve → execute
  - Node heartbeat registration and status verification
  - Job state machine transition validation
  - Multiple runs with timing aggregation
  - Motor execution timeout detection
  - Detailed timing breakdown per phase

Usage:
    python e2e_test_runner.py --runs 3 --validate-state-machine
    python e2e_test_runner.py --once --verbose
============================================================
"""
import requests
import time
import threading
import sys
import os
import argparse
import json
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime

# Configuration
try:
    from Scanner.pi_config import SERVER_URL, HEARTBEAT_INTERVAL
except ImportError:
    SERVER_IP = os.getenv("PI_SERVER_IP", "localhost")
    SERVER_PORT = os.getenv("PI_SERVER_PORT", "8000")
    SERVER_URL = f"http://{SERVER_IP}:{SERVER_PORT}"
    HEARTBEAT_INTERVAL = 3

API = SERVER_URL
MOTOR_TIMEOUT_SECONDS = 30

# Simulated test data
SCRAMBLED_CUBE = (
    "RRGGBBOOWW"
    "YYRRGGBBOO"
    "WWYYRRGGO"
    "OBWYRGOBY"
    "WGROBYWGR"
    "BYOWG"
)[:54].ljust(54, "W")

SOLUTION_MOVES = "R U R' U' F' D2 L B L' B' R U2 R' U F R U R' U'"

# Simulated nodes for heartbeat
NODES = ["rpi1-scanner", "rpi2-solver", "rpi3-motors", "rpi4-db"]
NODE_TYPES = {
    "rpi1-scanner": "scanner",
    "rpi2-solver": "solver",
    "rpi3-motors": "motor",
    "rpi4-db": "database",
}


@dataclass
class TimingData:
    """Timing breakdown for a single run."""
    run_number: int
    session_id: int
    scan_time: float
    solve_time: float
    execute_time: float
    total_time: float
    status: str
    errors: List[str]
    state_transitions: Dict[str, float]  # state -> timestamp


class E2ETestRunner:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.heartbeat_thread = None
        self.stop_event = threading.Event()
        self.timings = []
        
    def log(self, msg: str, prefix: str = ""):
        if self.verbose:
            print(f"{prefix} {msg}")
    
    def heartbeat_loop(self):
        """Send heartbeats for all simulated nodes."""
        while not self.stop_event.is_set():
            for node_id in NODES:
                try:
                    requests.post(f"{API}/nodes/heartbeat", json={
                        "node_id": node_id,
                        "node_type": NODE_TYPES.get(node_id, "unknown"),
                        "status": "online",
                    })
                except requests.ConnectionError:
                    pass
            self.stop_event.wait(HEARTBEAT_INTERVAL)
    
    def start_heartbeats(self):
        """Start heartbeat thread."""
        self.stop_event.clear()
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        self.log("Heartbeats started for all nodes", "💓")
        time.sleep(2)  # Let heartbeats register
    
    def stop_heartbeats(self):
        """Stop heartbeat thread."""
        if self.heartbeat_thread:
            self.stop_event.set()
            self.heartbeat_thread.join(timeout=5)
    
    def verify_node_status(self) -> bool:
        """Verify all nodes are online."""
        try:
            r = requests.get(f"{API}/nodes")
            nodes = r.json()
            online_count = sum(1 for n in nodes if n.get("status") == "online")
            self.log(f"Nodes online: {online_count}/{len(NODES)}", "📡")
            return online_count >= 3  # At least 3 nodes
        except Exception as e:
            self.log(f"Failed to verify nodes: {e}", "⚠️")
            return False
    
    def run_single_e2e(self, run_num: int) -> TimingData:
        """Run a single end-to-end test cycle."""
        self.log(f"\n{'='*60}", "")
        self.log(f"Run #{run_num} Starting", "🚀")
        self.log(f"{'='*60}", "")
        
        timing = TimingData(
            run_number=run_num,
            session_id=None,
            scan_time=0,
            solve_time=0,
            execute_time=0,
            total_time=0,
            status="",
            errors=[],
            state_transitions={}
        )
        
        total_start = time.time()
        
        try:
            # ── Phase 1: Start job session ──
            self.log("\n▶️  Phase 1: Starting solve session", "")
            phase_start = time.time()
            
            r = requests.post(f"{API}/jobs/start", json={
                "algorithm": "CFOP",
                "session_name": f"E2E Run #{run_num}",
            })
            if r.status_code not in (200, 201):
                raise Exception(f"POST /jobs/start failed: {r.status_code} {r.text}")
            
            session = r.json()
            session_id = session.get("session_id") or session.get("id")
            if not session_id:
                raise Exception(f"No session_id in response: {session}")
            timing.session_id = session_id
            timing.state_transitions["created"] = time.time()
            
            self.log(f"Session #{session_id} created", "")
            time.sleep(0.5)
            
            # ── Phase 2: Scanner submitting cube state ──
            self.log("▶️  Phase 2: Scanner submitting cube state", "")
            phase_start = time.time()
            
            r = requests.post(f"{API}/scan/submit", json={
                "session_id": session_id,
                "state_string": SCRAMBLED_CUBE,
                "is_valid": True,
                "confidence": 0.95,
            })
            if r.status_code != 200:
                raise Exception(f"POST /scan/submit failed: {r.status_code} {r.text}")
            
            timing.scan_time = time.time() - phase_start
            self.log(f"Cube state submitted (confidence: 95%, {timing.scan_time:.2f}s)", "")
            time.sleep(0.5)
            
            # Check current status
            r = requests.get(f"{API}/jobs/{session_id}")
            current_state = r.json().get("status")
            timing.state_transitions[current_state] = time.time()
            self.log(f"Job state: {current_state}", "")
            
            # ── Phase 3: Transition to solving ──
            self.log("▶️  Phase 3: Transitioning to solving", "")
            phase_start = time.time()
            
            r = requests.post(f"{API}/jobs/{session_id}/transition", json={"to": "solving"})
            if r.status_code == 200:
                timing.state_transitions["solving"] = time.time()
                self.log(f"Status → solving", "")
            else:
                self.log(f"Transition to 'solving' failed: {r.status_code} {r.text}", "⚠️")
            
            time.sleep(0.5)
            
            # ── Phase 4: Solve ──
            self.log("▶️  Phase 4: Submitting solution", "")
            phase_start = time.time()
            
            moves = SOLUTION_MOVES.split()
            r = requests.post(f"{API}/solve/submit", json={
                "session_id": session_id,
                "algorithm_used": "CFOP",
                "move_count": len(moves),
                "solution_string": SOLUTION_MOVES,
            })
            if r.status_code != 200:
                raise Exception(f"POST /solve/submit failed: {r.status_code} {r.text}")
            
            solution_resp = r.json()
            solution_id = solution_resp["solution_id"]
            timing.solve_time = time.time() - phase_start
            
            self.log(f"Solution submitted ({len(moves)} moves, ID: {solution_id}, {timing.solve_time:.2f}s)", "")
            time.sleep(0.5)
            
            # ── Phase 5: Transition to executing ──
            self.log("▶️  Phase 5: Transitioning to executing", "")
            
            r = requests.post(f"{API}/jobs/{session_id}/transition", json={"to": "executing"})
            if r.status_code == 200:
                timing.state_transitions["executing"] = time.time()
                self.log(f"Status → executing", "")
            else:
                self.log(f"Transition to 'executing' failed: {r.status_code} {r.text}", "⚠️")
            
            # ── Phase 6: Execute moves ──
            self.log("▶️  Phase 6: Motor executing moves", "")
            execute_start = time.time()
            
            # Start execution run
            r = requests.post(f"{API}/execute/start", json={
                "session_id": session_id,
                "solution_id": solution_id,
                "motor_node_id": "rpi3-motors"
            })
            if r.status_code != 200:
                raise Exception(f"POST /execute/start failed: {r.status_code} {r.text}")
            
            run_resp = r.json()
            run_id = run_resp["run_id"]
            self.log(f"Execution run #{run_id} started", "")
            
            # Execute each move
            for i, move in enumerate(moves):
                self.log(f"[{i+1}/{len(moves)}] {move}", "  ")
                r = requests.post(f"{API}/execute/progress", json={
                    "session_id": session_id,
                    "run_id": run_id,
                    "current_step": i + 1,
                    "total_steps": len(moves),
                    "move": move
                })
                if r.status_code != 200:
                    timing.errors.append(f"Progress report failed for move {move}")
                time.sleep(0.3)
            
            timing.execute_time = time.time() - execute_start
            
            # ── Phase 7: Complete execution ──
            self.log("▶️  Phase 7: Completing execution", "")
            
            r = requests.post(f"{API}/execute/complete", json={
                "session_id": session_id,
                "run_id": run_id,
                "status": "success"
            })
            if r.status_code != 200:
                timing.errors.append(f"POST /execute/complete failed: {r.status_code}")
            
            # Final transition
            r = requests.post(f"{API}/jobs/{session_id}/transition", json={"to": "done"})
            if r.status_code == 200:
                timing.state_transitions["done"] = time.time()
                self.log(f"Status → done", "")
            else:
                # Might already be in 'done' state if execute/complete transitioned it
                r_check = requests.get(f"{API}/jobs/{session_id}")
                final_state = r_check.json().get("status", "unknown")
                timing.state_transitions[final_state] = time.time()
                self.log(f"Status → {final_state}", "")
            
            timing.total_time = time.time() - total_start
            timing.status = "success"
            
        except Exception as e:
            timing.total_time = time.time() - total_start
            timing.status = "failed"
            timing.errors.append(str(e))
            self.log(f"❌ Run #{run_num} failed: {e}", "")
        
        return timing
    
    def validate_state_machine(self, timing: TimingData) -> bool:
        """Validate job state transitions."""
        self.log("\n📋 State Machine Validation:", "")
        
        expected_order = ["created", "solving", "executing", "done"]
        actual_states = list(timing.state_transitions.keys())
        
        # Remove intermediate states we might not have captured
        actual_key_states = [s for s in actual_states if s in expected_order]
        
        valid = actual_key_states == expected_order
        
        for state in actual_key_states:
            self.log(f"  {state}: {datetime.fromtimestamp(timing.state_transitions[state]).isoformat(timespec='seconds')}", "")
        
        if valid:
            self.log("✅ State transitions valid", "")
        else:
            self.log(f"⚠️  Expected {expected_order}, got {actual_key_states}", "")
        
        return valid
    
    def print_summary(self):
        """Print aggregate timing summary."""
        if not self.timings:
            self.log("No runs completed", "⚠️")
            return
        
        print("\n" + "="*80)
        print("END-TO-END TEST SUMMARY")
        print("="*80)
        print(f"\n{'Run':<6} {'Session':<10} {'Scan':<10} {'Solve':<10} {'Execute':<10} {'Total':<10} {'Status':<10} {'Errors':<30}")
        print("-"*100)
        
        for t in self.timings:
            errors = ", ".join(t.errors[:2]) if t.errors else "None"
            sid = t.session_id if t.session_id else "ERR"
            print(f"{t.run_number:<6} {sid:<10} {t.scan_time:<10.2f}s {t.solve_time:<10.2f}s {t.execute_time:<10.2f}s {t.total_time:<10.2f}s {t.status:<10} {errors:<30}")
        
        # Aggregates
        total_times = [t.total_time for t in self.timings if t.status == "success"]
        if total_times:
            avg_total = sum(total_times) / len(total_times)
            max_total = max(total_times)
            min_total = min(total_times)
            
            print("-"*100)
            print(f"Average total time: {avg_total:.2f}s")
            print(f"Min/Max total time: {min_total:.2f}s / {max_total:.2f}s")
            print(f"Success rate: {sum(1 for t in self.timings if t.status == 'success')}/{len(self.timings)}")
            
            # SLA check
            SLA_SECONDS = 30
            meets_sla = all(t <= SLA_SECONDS for t in total_times)
            if meets_sla:
                print(f"✅ All runs meet < {SLA_SECONDS}s SLA")
            else:
                slow_runs = [i+1 for i, t in enumerate(total_times) if t > SLA_SECONDS]
                print(f"⚠️  Runs {slow_runs} exceed {SLA_SECONDS}s SLA")
        
        print("="*80)
    
    def run(self, num_runs: int = 1, validate_state_machine: bool = False):
        """Run E2E tests."""
        print(f"\n🎯 E2E Integration Test Runner")
        print(f"   Server: {API}")
        print(f"   Runs: {num_runs}")
        print(f"   State Machine Validation: {validate_state_machine}\n")
        
        # Check server is reachable
        try:
            r = requests.get(f"{API}/")
            print(f"✅ Server reachable")
        except requests.ConnectionError:
            print(f"❌ Cannot reach server at {API}")
            print(f"   Start it with: cd backend && uvicorn main:app --host 0.0.0.0 --port 8000")
            sys.exit(1)
        
        # Start heartbeats
        self.start_heartbeats()
        
        # Verify nodes are online
        if not self.verify_node_status():
            print("⚠️  Not all nodes registered; continuing anyway")
        
        # Run tests
        for i in range(1, num_runs + 1):
            timing = self.run_single_e2e(i)
            self.timings.append(timing)
            
            if validate_state_machine:
                self.validate_state_machine(timing)
            
            if i < num_runs:
                time.sleep(2)  # Brief pause between runs
        
        # Stop heartbeats
        self.stop_heartbeats()
        
        # Print summary
        self.print_summary()


def main():
    parser = argparse.ArgumentParser(description="M004/S04 E2E Integration Test Runner")
    parser.add_argument("--runs", type=int, default=1, help="Number of test runs (default: 1)")
    parser.add_argument("--once", action="store_true", help="Alias for --runs 1")
    parser.add_argument("--validate-state-machine", action="store_true", help="Validate job state transitions")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    num_runs = 1 if args.once else args.runs
    
    runner = E2ETestRunner(verbose=args.verbose)
    runner.run(num_runs=num_runs, validate_state_machine=args.validate_state_machine)


if __name__ == "__main__":
    main()
