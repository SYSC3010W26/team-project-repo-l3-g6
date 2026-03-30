"""
Live Playwright E2E fixtures (conftest.py) for S06 Slice.

Manages:
1. live_backend: session-scoped fixture that launches a real FastAPI backend
   on port 8000 with a temporary SQLite DB, waits for readiness, and tears down.
2. seeded_session_id: session-scoped fixture that seeds a known session/scan in
   the backend via real API calls.
3. live_frontend: session-scoped fixture that builds and runs vite preview
   on port 5173.

All three work together to provide a fully live testing environment with
no page.route() mocking.
"""

import os
import sys
import subprocess
import time
import tempfile
import uuid
import signal
import requests
import pytest
from pathlib import Path

# Add backend module to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture(scope="session")
def live_backend():
    """
    Session-scoped fixture: Launch a real FastAPI backend on port 8000.
    
    - Creates a temporary SQLite database
    - Sets DATABASE_URL and PYTHONPATH environment variables
    - Launches: uvicorn backend.main:app --port 8000
    - Waits up to 20s for GET / to return 200
    - Logs to /tmp/live-backend.log
    - Yields the PID
    - On teardown: terminate() with 5s timeout, fallback to kill()
    """
    db_file = f"/tmp/s06-test-{uuid.uuid4().hex[:8]}.db"
    log_file = "/tmp/live-backend.log"
    
    env = os.environ.copy()
    env["DATABASE_URL"] = db_file
    env["PYTHONPATH"] = "."
    
    # Launch uvicorn process
    with open(log_file, "w") as log_f:
        proc = subprocess.Popen(
            ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
            env=env,
            stdout=log_f,
            stderr=subprocess.STDOUT,
            cwd=str(Path(__file__).parent.parent.parent),
        )
    
    pid = proc.pid
    print(f"[live_backend] Started uvicorn PID {pid}, DB: {db_file}, logs: {log_file}")
    
    # Wait for backend to be ready (up to 20s)
    start_time = time.time()
    ready = False
    while time.time() - start_time < 20:
        try:
            resp = requests.get("http://localhost:8000/", timeout=2)
            if resp.status_code == 200:
                ready = True
                print(f"[live_backend] Backend is ready (took {time.time() - start_time:.1f}s)")
                break
        except requests.ConnectionError:
            pass
        time.sleep(0.5)
    
    if not ready:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        raise RuntimeError(
            f"Backend failed to start within 20s. Check {log_file} for details."
        )
    
    yield pid
    
    # Teardown: terminate gracefully, fallback to kill
    print(f"[live_backend] Tearing down PID {pid}")
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        print(f"[live_backend] Terminate timeout, killing PID {pid}")
        proc.kill()
        proc.wait()
    
    # Clean up temp DB
    if os.path.exists(db_file):
        try:
            os.unlink(db_file)
        except Exception as e:
            print(f"[live_backend] Warning: could not delete {db_file}: {e}")


@pytest.fixture(scope="session")
def seeded_session_id(live_backend):
    """
    Session-scoped fixture: Create a seeded solve session with scanned cube state.
    
    Flow:
    1. POST /jobs/start with algorithm=CFOP -> get session_id
    2. POST /scan/submit with a valid solved cube state (WWWWWWWWWYYYYYYYYYRRRRRRRRROOOOOOOOOBBBBBBBBBGGGGGGGGG)
    3. POST /solve/start to transition to 'solving' state
    4. Yield the session_id
    
    The seeded session has:
    - status: solving
    - A valid cube state in the DB
    - Exists in the live backend so tests can query it
    """
    base_url = "http://localhost:8000"
    
    # 1. Create a job
    resp = requests.post(f"{base_url}/jobs/start", json={"algorithm": "CFOP"})
    assert resp.status_code == 201, f"Failed to start job: {resp.text}"
    session_id = resp.json()["session_id"]
    print(f"[seeded_session_id] Created session {session_id}")
    
    # 2. Submit a scanned cube state
    # Use the solved cube string: centers are unique (W,Y,R,O,B,G)
    state_string = "WWWWWWWWWYYYYYYYYYRRRRRRRRROOOOOOOOOBBBBBBBBBGGGGGGGGG"
    resp = requests.post(
        f"{base_url}/scan/submit",
        json={
            "session_id": session_id,
            "state_string": state_string,
            "is_valid": True,
            "confidence": 0.95,
        }
    )
    assert resp.status_code == 200, f"Failed to submit scan: {resp.text}"
    cube_state_id = resp.json()["cube_state_id"]
    print(f"[seeded_session_id] Submitted cube state {cube_state_id}")
    
    # 3. Start solving (transitions to 'solving' state)
    resp = requests.post(
        f"{base_url}/solve/start",
        json={"session_id": session_id}
    )
    assert resp.status_code == 200, f"Failed to start solve: {resp.text}"
    print(f"[seeded_session_id] Started solve for session {session_id}")
    
    yield session_id
    # No cleanup needed; the session will exist in the live DB for the test duration


@pytest.fixture(scope="session")
def live_frontend(live_backend):
    """
    Session-scoped fixture: Build and run vite preview on port 5173.
    
    - Runs: npm run build (in frontend/)
    - Runs: npm run preview (which runs vite preview --port 5173)
    - Waits up to 30s for port 5173 to respond
    - Yields the base URL: http://localhost:5173
    - On teardown: terminate the vite process
    """
    frontend_dir = str(Path(__file__).parent.parent.parent / "frontend")
    
    print("[live_frontend] Running npm run build...")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=frontend_dir,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        print(f"[live_frontend] Build failed:\n{result.stderr}")
        raise RuntimeError(f"npm run build failed: {result.stderr}")
    print("[live_frontend] Build completed successfully")
    
    # Launch vite preview
    print("[live_frontend] Running npm run preview...")
    proc = subprocess.Popen(
        ["npm", "run", "preview"],
        cwd=frontend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    
    # Wait for vite preview to be ready (up to 30s)
    start_time = time.time()
    ready = False
    while time.time() - start_time < 30:
        try:
            resp = requests.get("http://localhost:5173/", timeout=2)
            ready = True
            print(f"[live_frontend] Frontend is ready (took {time.time() - start_time:.1f}s)")
            break
        except requests.ConnectionError:
            pass
        time.sleep(0.5)
    
    if not ready:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        raise RuntimeError("Frontend failed to start within 30s")
    
    yield "http://localhost:5173"
    
    # Teardown: terminate vite preview
    print("[live_frontend] Tearing down vite preview")
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        print("[live_frontend] Terminate timeout, killing process")
        proc.kill()
        proc.wait()


@pytest.fixture(autouse=True)
def ensure_artifacts_dir():
    """Ensure the artifacts directory exists for screenshots."""
    artifacts_dir = "tests/e2e/artifacts"
    os.makedirs(artifacts_dir, exist_ok=True)
