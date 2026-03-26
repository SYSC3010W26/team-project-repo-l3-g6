"""
============================================================
SYSC3010 L3-G6 — Backend Integration Tests
Done By : Saim Hashmi

Full end-to-end pipeline tests covering the happy path (scan -> solve ->
execute -> complete), error cases (404, 422), heartbeat CRUD, and logs.
Each test is fully self-contained with its own isolated SQLite DB.
============================================================
"""


def test_health_check(client):
    """GET / returns 200 with status: ok."""
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_full_pipeline_happy_path(client):
    """Happy-path: start job -> scan -> solve -> execute -> complete.

    Proves the full scan-solve-execute pipeline flow end-to-end.
    """
    # Step 1: Create a new solve session
    r = client.post("/jobs/start", json={"algorithm": "CFOP"})
    assert r.status_code == 201
    session_id = r.json()["session_id"]
    assert isinstance(session_id, int)

    # Step 2: Verify session starts in pending state
    r = client.get(f"/jobs/{session_id}")
    assert r.status_code == 200
    assert r.json()["status"] == "pending"

    # Step 3: Submit a cube scan
    r = client.post(
        "/scan/submit",
        json={"session_id": session_id, "state_string": "U" * 54, "is_valid": True},
    )
    assert r.status_code == 200
    cube_state_id = r.json()["cube_state_id"]
    assert isinstance(cube_state_id, int)

    # Step 4: Read back the scan result
    r = client.get(f"/scan/{session_id}")
    assert r.status_code == 200
    assert r.json()["state_string"] == "U" * 54

    # Step 5: Submit a solution
    r = client.post(
        "/solve/submit",
        json={
            "session_id": session_id,
            "algorithm_used": "CFOP",
            "move_count": 4,
            "solution_string": "R U R' U'",
        },
    )
    assert r.status_code == 200
    solution_id = r.json()["solution_id"]
    assert isinstance(solution_id, int)

    # Step 6: Read back the solution result
    r = client.get(f"/solve/{session_id}")
    assert r.status_code == 200
    assert r.json()["move_count"] == 4

    # Step 7: Start execution
    r = client.post(
        "/execute/start",
        json={"session_id": session_id, "solution_id": solution_id},
    )
    assert r.status_code == 200
    run_id = r.json()["run_id"]
    assert isinstance(run_id, int)

    # Step 8: Report progress
    r = client.post(
        "/execute/progress",
        json={
            "session_id": session_id,
            "run_id": run_id,
            "current_step": 1,
            "total_steps": 4,
            "move": "R",
        },
    )
    assert r.status_code == 200

    # Step 9: Mark execution complete
    r = client.post(
        "/execute/complete",
        json={"session_id": session_id, "run_id": run_id, "status": "success"},
    )
    assert r.status_code == 200

    # Step 10: Session should now be in completed state
    r = client.get(f"/jobs/{session_id}")
    assert r.status_code == 200
    assert r.json()["status"] == "completed"


def test_job_not_found(client):
    """GET /jobs/9999 returns 404 with 'not found' in the detail."""
    r = client.get("/jobs/9999")
    assert r.status_code == 404
    body = r.json()
    detail = body.get("detail", "").lower()
    assert "not found" in detail


def test_scan_not_found(client):
    """GET /scan/9999 returns 404 when no scan exists for that session."""
    r = client.get("/scan/9999")
    assert r.status_code == 404


def test_invalid_request_body(client):
    """Validate request body handling: defaults, missing required fields, wrong types."""
    # POST /jobs/start with {} — algorithm defaults to "CFOP", should succeed
    r = client.post("/jobs/start", json={})
    assert r.status_code == 201

    # POST /scan/submit with {} — all fields required, should fail with 422
    r = client.post("/scan/submit", json={})
    assert r.status_code == 422

    # POST /scan/submit with wrong type for session_id — should fail with 422
    r = client.post(
        "/scan/submit",
        json={"session_id": "not-an-int", "state_string": "x", "is_valid": True},
    )
    assert r.status_code == 422


def test_heartbeat_and_node_status(client):
    """POST /nodes/heartbeat writes node records; GET /nodes/status returns them."""
    # Register motor node
    r = client.post(
        "/nodes/heartbeat",
        json={"node_id": "motor-pi-1", "node_type": "motor", "status": "online"},
    )
    assert r.status_code == 200

    # Register scanner node
    r = client.post(
        "/nodes/heartbeat",
        json={"node_id": "scanner-pi-1", "node_type": "scanner", "status": "online"},
    )
    assert r.status_code == 200

    # Verify both nodes appear in /nodes/status
    r = client.get("/nodes/status")
    assert r.status_code == 200
    nodes = r.json()
    assert len(nodes) == 2
    node_ids = {n["node_id"] for n in nodes}
    assert "motor-pi-1" in node_ids
    assert "scanner-pi-1" in node_ids


def test_logs_endpoint(client):
    """GET /logs returns 200 with a list (may be empty on fresh DB)."""
    r = client.get("/logs")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_execution_progress_broadcast(client):
    """POST /execute/progress emits execution_progress Socket.IO event per D-04."""
    from unittest.mock import AsyncMock, patch

    # Build precondition: session + scan + solution + run
    session_id = client.post("/jobs/start", json={}).json()["session_id"]
    client.post(
        "/scan/submit",
        json={"session_id": session_id, "state_string": "U" * 54, "is_valid": True},
    )
    solution_id = client.post(
        "/solve/submit",
        json={
            "session_id": session_id,
            "algorithm_used": "CFOP",
            "move_count": 4,
            "solution_string": "R U R' U'",
        },
    ).json()["solution_id"]
    run_id = client.post(
        "/execute/start",
        json={"session_id": session_id, "solution_id": solution_id},
    ).json()["run_id"]

    # Patch sio on the execute router module, then call progress
    with patch("backend.routers.execute.sio") as mock_sio:
        mock_sio.emit = AsyncMock()
        r = client.post(
            "/execute/progress",
            json={
                "session_id": session_id,
                "run_id": run_id,
                "current_step": 1,
                "total_steps": 4,
                "move": "R",
            },
        )
        assert r.status_code == 200

        mock_sio.emit.assert_called_once_with(
            "execution_progress",
            {
                "session_id": session_id,
                "run_id": run_id,
                "current_step": 1,
                "total_steps": 4,
                "move": "R",
                "pct_complete": 25.0,
            },
        )
