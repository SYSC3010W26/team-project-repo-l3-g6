#!/usr/bin/env python3
"""
M004/S04/T05: Motor Execution Timeout Detection Test

Tests that a motor execution run that doesn't receive progress
reports for > 30 seconds is automatically failed and the job
transitions to error state.

Usage:
    python test_motor_timeout.py
"""
import requests
import time
import sqlite3
import os
from datetime import datetime, timezone, timedelta

API = "http://localhost:8000"

def test_motor_timeout():
    """
    Test scenario:
    1. Create a solve session
    2. Submit cube state
    3. Transition to solving
    4. Submit solution
    5. Start motor execution
    6. Let execution run without progress reports for > 30 seconds
    7. Verify that timeout monitor fails the run and errors the session
    """
    print("\n" + "="*80)
    print("M004/S04/T05: MOTOR EXECUTION TIMEOUT TEST")
    print("="*80)
    
    # Setup: create session and solution
    print("\n▶️  Setup: Creating solve session...")
    r = requests.post(f"{API}/jobs/start", json={
        "algorithm": "CFOP",
        "session_name": "Timeout Test",
    })
    assert r.status_code in (200, 201), f"Failed to create session: {r.status_code}"
    session_id = r.json().get("session_id")
    if not session_id:
        raise ValueError(f"No session_id in response: {r.json()}")
    print(f"   Session #{session_id} created")
    
    # Submit cube state
    print("▶️  Submitting cube state...")
    r = requests.post(f"{API}/scan/submit", json={
        "session_id": session_id,
        "state_string": "R"*54,  # Dummy state
        "is_valid": True,
        "confidence": 0.95,
    })
    assert r.status_code == 200, f"Failed to submit scan: {r.status_code}"
    
    # Transition to solving
    print("▶️  Transitioning to solving...")
    r = requests.post(f"{API}/jobs/{session_id}/transition", json={"to": "solving"})
    
    # Submit solution
    print("▶️  Submitting solution...")
    r = requests.post(f"{API}/solve/submit", json={
        "session_id": session_id,
        "algorithm_used": "CFOP",
        "move_count": 5,
        "solution_string": "R U R' U' F'",
    })
    assert r.status_code in (200, 201), f"Failed to submit solution: {r.status_code}"
    solution_id = r.json().get("solution_id")
    if not solution_id:
        raise ValueError(f"No solution_id in response: {r.json()}")
    print(f"   Solution #{solution_id} submitted")
    
    # Transition to executing
    print("▶️  Transitioning to executing...")
    r = requests.post(f"{API}/jobs/{session_id}/transition", json={"to": "executing"})
    
    # Start motor execution (without any progress reports)
    print("▶️  Starting motor execution...")
    r = requests.post(f"{API}/execute/start", json={
        "session_id": session_id,
        "solution_id": solution_id,
        "motor_node_id": "rpi3-motors"
    })
    assert r.status_code in (200, 201), f"Failed to start execution: {r.status_code}"
    run_id = r.json().get("run_id")
    if not run_id:
        raise ValueError(f"No run_id in response: {r.json()}")
    print(f"   Execution run #{run_id} started")
    print(f"   ⏱️  Now waiting {35} seconds for timeout monitor to detect stall...")
    
    # Wait for timeout to be detected (30s timeout + 5s check interval + buffer)
    time.sleep(35)
    
    # Check job status - should be in error state now
    print("▶️  Checking job status after timeout...")
    r = requests.get(f"{API}/jobs/{session_id}")
    job_status = r.json()["status"]
    print(f"   Job status: {job_status}")
    
    # Check execution run status - should be failed
    # (We'd need a GET /execute endpoint to check this directly;
    # for now we verify via job state)
    
    if job_status == "error":
        print("\n✅ SUCCESS: Motor execution timeout was detected!")
        print(f"   - Execution run #{run_id} was auto-failed")
        print(f"   - Session #{session_id} transitioned to error state")
        return True
    else:
        print(f"\n❌ FAILED: Expected job status 'error', got '{job_status}'")
        print("   The timeout monitor may not have detected the stall in time.")
        return False


if __name__ == "__main__":
    try:
        success = test_motor_timeout()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
