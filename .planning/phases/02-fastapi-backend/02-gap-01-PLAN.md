---
phase: 02-fastapi-backend
plan: gap-01
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/routers/execute.py
  - backend/tests/test_integration.py
autonomous: true
requirements: [API-03]
gap_closure: true

must_haves:
  truths:
    - "POST /execute/progress emits sio.emit('execution_progress', ...) after the DB write"
    - "execution_progress payload contains session_id, run_id, current_step, total_steps, move, and pct_complete"
    - "Test verifies the broadcast is emitted with the correct payload on a valid progress request"
  artifacts:
    - path: "backend/routers/execute.py"
      provides: "execution_progress Socket.IO broadcast in report_progress handler"
      contains: "sio.emit('execution_progress'"
    - path: "backend/tests/test_integration.py"
      provides: "test_execution_progress_broadcast covering the emit call"
      contains: "test_execution_progress_broadcast"
  key_links:
    - from: "backend/routers/execute.py"
      to: "backend/main.py"
      via: "from backend.main import sio"
      pattern: "from backend\\.main import sio"
    - from: "backend/routers/execute.py"
      to: "sio.emit('execution_progress', ...)"
      via: "asyncio.run or import asyncio + nest_asyncio, or switch route to async def"
      pattern: "sio\\.emit\\('execution_progress'"
---

<objective>
Close the single failing must-have from Phase 02 verification: the `execution_progress` Socket.IO broadcast is never emitted.

D-04 specifies two frontend broadcasts — `job_state_update` (fully implemented) and `execution_progress` (completely missing). The `POST /execute/progress` handler already receives every field needed for the payload (`session_id`, `run_id`, `current_step`, `total_steps`, `move`) but returns after the DB write without calling `sio.emit`. This plan adds that one missing call and a test that verifies it fires.

Purpose: Fully satisfy API-03 so the frontend Execution Monitor page can display live per-step motor progress.
Output: Updated `execute.py` with the emit call and an updated `test_integration.py` with a broadcast verification test.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/02-fastapi-backend/02-CONTEXT.md
@.planning/phases/02-fastapi-backend/02-VERIFICATION.md

@backend/main.py
@backend/routers/execute.py
@backend/tests/conftest.py
@backend/tests/test_integration.py
</context>

<interfaces>
<!-- Key contracts the executor needs. No codebase exploration required. -->

From backend/main.py:
```python
# sio is the socketio.AsyncServer — import it directly
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
```

From backend/routers/execute.py — current report_progress signature (sync def):
```python
@router.post("/progress", response_model=schemas.MessageResponse)
def report_progress(body: schemas.ExecuteProgressRequest, conn: sqlite3.Connection = Depends(get_db_dep)):
    ...
    crud.create_motor_log(conn, data)
    return schemas.MessageResponse(message="Progress recorded")
```

D-04 execution_progress payload contract:
```python
{
    "session_id": int,
    "run_id": int,
    "current_step": int,
    "total_steps": int,
    "move": str,
    "pct_complete": float,   # current_step / total_steps * 100, rounded to 1 decimal
}
```

From backend/socket_handlers.py (established import pattern for sio):
```python
from backend.main import sio
# ... then call:
await sio.emit("job_state_update", {...})
```

NOTE on sync vs async: `report_progress` is currently `def` (sync). To call `await sio.emit(...)` you must convert it to `async def`. FastAPI supports both; switching to `async def` has no side effects here.

From backend/tests/conftest.py:
```python
@pytest.fixture
def client():
    """Each test gets a fresh SQLite DB + TestClient wrapping fastapi_app only."""
    # ... tempfile DB setup ...
    with TestClient(fastapi_app) as c:
        yield c
```

Mocking pattern for sio.emit in tests (unittest.mock):
```python
from unittest.mock import AsyncMock, patch

def test_execution_progress_broadcast(client):
    with patch("backend.routers.execute.sio") as mock_sio:
        mock_sio.emit = AsyncMock()
        # ... POST /execute/progress ...
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
```
</interfaces>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Emit execution_progress broadcast in report_progress handler</name>
  <files>backend/routers/execute.py</files>
  <behavior>
    - After `crud.create_motor_log(conn, data)` succeeds, `sio.emit('execution_progress', payload)` is awaited
    - Payload keys: session_id, run_id, current_step, total_steps, move, pct_complete
    - pct_complete = round(current_step / total_steps * 100, 1) — guarded against division by zero (if total_steps is 0, pct_complete = 0.0)
    - Handler is converted from `def` to `async def` to allow `await sio.emit(...)`
    - `sio` is imported from `backend.main` at the top of execute.py (same pattern as socket_handlers.py line 23)
    - The DB write (crud.create_motor_log) still happens before the emit — emit is the last step
    - Response remains `schemas.MessageResponse(message="Progress recorded")` — no change to return value
  </behavior>
  <action>
    Per D-04 and gap identified in 02-VERIFICATION.md truth #19.

    1. Add import at top of `backend/routers/execute.py` (after existing imports):
       ```python
       from backend.main import sio
       ```

    2. Change the `report_progress` function signature from `def` to `async def`:
       ```python
       @router.post("/progress", response_model=schemas.MessageResponse)
       async def report_progress(body: schemas.ExecuteProgressRequest, conn: sqlite3.Connection = Depends(get_db_dep)):
       ```

    3. After `crud.create_motor_log(conn, data)` and before `return`, add:
       ```python
       pct = round(body.current_step / body.total_steps * 100, 1) if body.total_steps else 0.0
       await sio.emit(
           "execution_progress",
           {
               "session_id": body.session_id,
               "run_id": body.run_id,
               "current_step": body.current_step,
               "total_steps": body.total_steps,
               "move": body.move,
               "pct_complete": pct,
           },
       )
       ```

    Do NOT change any other handler in execute.py. Do NOT touch start_execution or complete_execution.
  </action>
  <verify>
    <automated>cd /home/anakafeel/linuxworkspace/3010-group-repo/team-project-repo-l3-g6 && grep -n "sio.emit.*execution_progress" backend/routers/execute.py</automated>
  </verify>
  <done>
    `grep -n "sio.emit.*execution_progress" backend/routers/execute.py` returns at least one match.
    `grep -n "from backend.main import sio" backend/routers/execute.py` returns a match.
    `grep -n "async def report_progress" backend/routers/execute.py` returns a match.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Add test_execution_progress_broadcast to test_integration.py</name>
  <files>backend/tests/test_integration.py</files>
  <behavior>
    - Test creates a full pipeline precondition (session + scan + solution + execution run) then calls POST /execute/progress
    - sio.emit is patched with AsyncMock on the module-level `sio` name imported by execute.py
    - Test asserts emit was called exactly once with event name "execution_progress" and correct payload dict
    - pct_complete in expected payload = 25.0 (1/4 * 100) matching the test inputs current_step=1, total_steps=4
    - Existing 29-test suite still passes — no existing tests modified
  </behavior>
  <action>
    Append a new test function to `backend/tests/test_integration.py`. Do NOT modify any existing test.

    ```python
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
    ```
  </action>
  <verify>
    <automated>cd /home/anakafeel/linuxworkspace/3010-group-repo/team-project-repo-l3-g6 && python -m pytest backend/tests/test_integration.py::test_execution_progress_broadcast -v</automated>
  </verify>
  <done>
    `pytest backend/tests/test_integration.py::test_execution_progress_broadcast` reports PASSED.
    Full suite `python -m pytest backend/tests/ database/tests/ -x -q` still reports all tests passing (30 passed, was 29).
  </done>
</task>

</tasks>

<verification>
Run the full test suite to confirm no regressions and the new test passes:

```
cd /home/anakafeel/linuxworkspace/3010-group-repo/team-project-repo-l3-g6
python -m pytest backend/tests/ database/tests/ -x -q
```

Expected: 30 passed (was 29).

Confirm the emit call exists in execute.py:

```
grep -n "sio.emit.*execution_progress" backend/routers/execute.py
grep -n "from backend.main import sio" backend/routers/execute.py
grep -n "async def report_progress" backend/routers/execute.py
```

All three greps must return matches.
</verification>

<success_criteria>
- `sio.emit('execution_progress', ...)` is called in `backend/routers/execute.py` after `crud.create_motor_log`
- Payload contains: session_id, run_id, current_step, total_steps, move, pct_complete
- `test_execution_progress_broadcast` passes and asserts emit was called once with correct payload
- Full test suite passes: 30 tests (29 pre-existing + 1 new)
- API-03 is fully satisfied: both `job_state_update` and `execution_progress` broadcasts are implemented
</success_criteria>

<output>
After completion, create `.planning/phases/02-fastapi-backend/02-gap-01-SUMMARY.md` with:
- What was changed (execute.py: added sio import, async def, emit call; test_integration.py: new test)
- Verification result (pytest output line count)
- Gap status: CLOSED — truth #19 now verified
</output>
```
