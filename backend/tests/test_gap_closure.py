"""
============================================================
SYSC3010 L3-G6 — Gap Closure Tests (04-04)
Done By : Saim Hashmi

Tests for API contract gap fixes:
  - Task 1: GET /jobs list endpoint (Gap 1)
  - Task 2: GET /solve/{session_id} returns steps array (Gap 2)
  - Task 3: GET /logs uses severity + node params (Gap 3)
============================================================
"""

# ---------------------------------------------------------------------------
# Task 1: GET /jobs list endpoint (Gap 1)
# ---------------------------------------------------------------------------

def test_get_jobs_returns_200_with_array(client):
    """GET /jobs returns HTTP 200 with a JSON array (can be empty)."""
    r = client.get("/jobs")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_jobs_contains_created_session(client):
    """After POST /jobs/start, GET /jobs returns an array with at least one item."""
    client.post("/jobs/start", json={"algorithm": "CFOP"})
    r = client.get("/jobs")
    assert r.status_code == 200
    sessions = r.json()
    assert len(sessions) >= 1


def test_get_jobs_item_has_required_fields(client):
    """Each item in GET /jobs response has session_id, status, selected_algorithm, started_at."""
    client.post("/jobs/start", json={"algorithm": "CFOP"})
    r = client.get("/jobs")
    assert r.status_code == 200
    item = r.json()[0]
    assert "session_id" in item
    assert isinstance(item["session_id"], int)
    assert "status" in item
    assert isinstance(item["status"], str)
    assert "selected_algorithm" in item
    assert isinstance(item["selected_algorithm"], str)
    assert "started_at" in item
    assert isinstance(item["started_at"], str)


# ---------------------------------------------------------------------------
# Task 2: GET /solve/{session_id} returns steps array (Gap 2)
# ---------------------------------------------------------------------------

def test_solve_response_has_steps_key(client):
    """GET /solve/{session_id} for a session with solution returns 200 with a 'steps' key."""
    session_id = client.post("/jobs/start", json={}).json()["session_id"]
    client.post("/solve/submit", json={
        "session_id": session_id,
        "algorithm_used": "CFOP",
        "move_count": 4,
        "solution_string": "R U R' U'",
    })
    r = client.get(f"/solve/{session_id}")
    assert r.status_code == 200
    body = r.json()
    assert "steps" in body
    assert isinstance(body["steps"], list)


def test_solve_steps_empty_when_no_steps_inserted(client):
    """When no solution steps inserted, steps is [] (not missing/null)."""
    session_id = client.post("/jobs/start", json={}).json()["session_id"]
    client.post("/solve/submit", json={
        "session_id": session_id,
        "algorithm_used": "CFOP",
        "move_count": 2,
        "solution_string": "R U",
    })
    r = client.get(f"/solve/{session_id}")
    assert r.status_code == 200
    assert r.json()["steps"] == []


def test_solve_steps_have_step_index_and_move_notation(client):
    """Each step in the steps list has step_index (int) and move_notation (str)."""
    import database.db as db_module
    from database.crud import create_solution_step
    from database.models import SolutionStepCreate

    session_id = client.post("/jobs/start", json={}).json()["session_id"]
    sol_resp = client.post("/solve/submit", json={
        "session_id": session_id,
        "algorithm_used": "CFOP",
        "move_count": 1,
        "solution_string": "R",
    })
    solution_id = sol_resp.json()["solution_id"]

    # Insert a solution step directly into the DB
    conn = db_module.get_db()
    create_solution_step(conn, SolutionStepCreate(
        solution_id=solution_id,
        step_index=0,
        face="R",
        direction="clockwise",
        degrees=90,
    ))
    conn.commit()
    conn.close()

    r = client.get(f"/solve/{session_id}")
    assert r.status_code == 200
    steps = r.json()["steps"]
    assert len(steps) == 1
    step = steps[0]
    assert "step_index" in step
    assert isinstance(step["step_index"], int)
    assert "move_notation" in step
    assert isinstance(step["move_notation"], str)


def test_solve_step_move_notation_format(client):
    """move_notation is constructed as '{face} {direction}'."""
    import database.db as db_module
    from database.crud import create_solution_step
    from database.models import SolutionStepCreate

    session_id = client.post("/jobs/start", json={}).json()["session_id"]
    sol_resp = client.post("/solve/submit", json={
        "session_id": session_id,
        "algorithm_used": "CFOP",
        "move_count": 1,
        "solution_string": "U",
    })
    solution_id = sol_resp.json()["solution_id"]

    conn = db_module.get_db()
    create_solution_step(conn, SolutionStepCreate(
        solution_id=solution_id,
        step_index=0,
        face="U",
        direction="counterclockwise",
        degrees=90,
    ))
    conn.commit()
    conn.close()

    r = client.get(f"/solve/{session_id}")
    assert r.status_code == 200
    steps = r.json()["steps"]
    assert steps[0]["move_notation"] == "U counterclockwise"


# ---------------------------------------------------------------------------
# Task 3: GET /logs uses severity + node params (Gap 3)
# ---------------------------------------------------------------------------

def test_logs_returns_severity_field_not_level(client):
    """GET /logs response objects contain 'severity' key (not 'level')."""
    r = client.get("/logs")
    assert r.status_code == 200
    logs = r.json()
    # If any logs exist, verify they have severity not level
    for log in logs:
        assert "severity" in log
        assert "level" not in log


def test_logs_severity_filter(client):
    """GET /logs?severity=error returns only rows where system_logs.level = 'error'."""
    # Register nodes first (node_id is FK to node_status)
    client.post("/nodes/heartbeat", json={"node_id": "scanner", "node_type": "scanner", "status": "online"})
    client.post("/nodes/heartbeat", json={"node_id": "motor", "node_type": "motor", "status": "online"})

    import database.db as db_module
    from database.crud import create_log
    from database.models import SystemLogCreate

    conn = db_module.get_db()
    create_log(conn, SystemLogCreate(
        session_id=None,
        node_id="scanner",
        level="error",
        event_type="test",
        message="error log",
    ))
    create_log(conn, SystemLogCreate(
        session_id=None,
        node_id="motor",
        level="info",
        event_type="test",
        message="info log",
    ))
    conn.commit()
    conn.close()

    r = client.get("/logs?severity=error")
    assert r.status_code == 200
    logs = r.json()
    assert len(logs) >= 1
    for log in logs:
        assert log["severity"] == "error"


def test_logs_node_filter(client):
    """GET /logs?node=scanner returns only rows where node_id = 'scanner'."""
    # Register nodes first (node_id is FK to node_status)
    client.post("/nodes/heartbeat", json={"node_id": "scanner", "node_type": "scanner", "status": "online"})
    client.post("/nodes/heartbeat", json={"node_id": "motor", "node_type": "motor", "status": "online"})

    import database.db as db_module
    from database.crud import create_log
    from database.models import SystemLogCreate

    conn = db_module.get_db()
    create_log(conn, SystemLogCreate(
        session_id=None,
        node_id="scanner",
        level="info",
        event_type="test",
        message="scanner log",
    ))
    create_log(conn, SystemLogCreate(
        session_id=None,
        node_id="motor",
        level="info",
        event_type="test",
        message="motor log",
    ))
    conn.commit()
    conn.close()

    r = client.get("/logs?node=scanner")
    assert r.status_code == 200
    logs = r.json()
    assert len(logs) >= 1
    for log in logs:
        assert log["node_id"] == "scanner"


def test_logs_severity_and_node_combined_filter(client):
    """GET /logs?severity=warning&node=motor returns rows filtered by BOTH conditions."""
    # Register nodes first (node_id is FK to node_status)
    client.post("/nodes/heartbeat", json={"node_id": "scanner", "node_type": "scanner", "status": "online"})
    client.post("/nodes/heartbeat", json={"node_id": "motor", "node_type": "motor", "status": "online"})

    import database.db as db_module
    from database.crud import create_log
    from database.models import SystemLogCreate

    conn = db_module.get_db()
    create_log(conn, SystemLogCreate(
        session_id=None,
        node_id="motor",
        level="warning",
        event_type="test",
        message="motor warning",
    ))
    create_log(conn, SystemLogCreate(
        session_id=None,
        node_id="scanner",
        level="warning",
        event_type="test",
        message="scanner warning",
    ))
    create_log(conn, SystemLogCreate(
        session_id=None,
        node_id="motor",
        level="info",
        event_type="test",
        message="motor info",
    ))
    conn.commit()
    conn.close()

    r = client.get("/logs?severity=warning&node=motor")
    assert r.status_code == 200
    logs = r.json()
    assert len(logs) == 1
    assert logs[0]["severity"] == "warning"
    assert logs[0]["node_id"] == "motor"


def test_logs_no_filter_returns_all(client):
    """GET /logs with no params returns all rows (no filter applied)."""
    # Use null node_id to avoid FK constraint
    import database.db as db_module
    from database.crud import create_log
    from database.models import SystemLogCreate

    conn = db_module.get_db()
    for i in range(3):
        create_log(conn, SystemLogCreate(
            session_id=None,
            node_id=None,
            level="info",
            event_type="test",
            message=f"log {i}",
        ))
    conn.commit()
    conn.close()

    r = client.get("/logs")
    assert r.status_code == 200
    logs = r.json()
    assert len(logs) >= 3
