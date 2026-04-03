from database import crud

def test_submit_solution_stores_steps(client):
    # GIVEN a session exists
    session_resp = client.post("/jobs/start", json={})
    session_id = session_resp.json()["session_id"]

    # WHEN we submit a solution string
    response = client.post("/solve/submit", json={
        "session_id": session_id,
        "algorithm_used": "CFOP",
        "move_count": 5,
        "solution_string": "U R2 F' B D"
    })
    assert response.status_code == 200
    solution_id = response.json()["solution_id"]

    # THEN the solution steps should be stored in the DB
    # (Since client uses a temporary DB, we need to access it)
    from database.db import get_db
    conn = get_db()
    steps = crud.get_solution_steps_by_solution(conn, solution_id)
    assert len(steps) == 5
    
    # Verify first step: U
    assert steps[0]["step_index"] == 0
    assert steps[0]["face"] == "U"
    assert steps[0]["direction"] == "CW"
    assert steps[0]["degrees"] == 90
    
    # Verify second step: R2
    assert steps[1]["step_index"] == 1
    assert steps[1]["face"] == "R"
    assert steps[1]["direction"] == "CW"
    assert steps[1]["degrees"] == 180
    
    # Verify third step: F'
    assert steps[2]["step_index"] == 2
    assert steps[2]["face"] == "F"
    assert steps[2]["direction"] == "CCW"
    assert steps[2]["degrees"] == 90
    conn.close()

def test_get_solution_with_steps(client):
    # GIVEN a solution with steps is submitted
    session_resp = client.post("/jobs/start", json={})
    session_id = session_resp.json()["session_id"]

    client.post("/solve/submit", json={
        "session_id": session_id,
        "algorithm_used": "CFOP",
        "move_count": 2,
        "solution_string": "U L'"
    })
    
    # WHEN we fetch the solution
    response = client.get(f"/solve/{session_id}")
    assert response.status_code == 200
    data = response.json()
    
    # THEN it should include the steps
    assert len(data["steps"]) == 2
    assert data["steps"][0]["move_notation"] == "U"
    assert data["steps"][1]["move_notation"] == "L'"
