---
phase: 04-web-dashboard-core-pages
verified: 2026-03-27T00:00:00Z
status: gaps_found
score: 2/4 success criteria verified
gaps:
  - truth: "All 5 pages render and show real data from the database"
    status: failed
    reason: "GET /jobs (list all sessions) endpoint is missing from the backend. All three pages that call getSessions() — Dashboard, SolveResults, ExecutionMonitor — will receive a 404/405 on every load and display no session data. Additionally, GET /solve/{session_id} returns a flat SolveResultResponse (with solution_string) not a steps array, so SolutionReview and ExecutionMonitor move lists will always be empty."
    artifacts:
      - path: "backend/routers/jobs.py"
        issue: "Only GET /jobs/{session_id} exists. No GET /jobs list endpoint. Frontend getSessions() calls /api/jobs which hits this router prefix and returns 404 (no route matches empty path segment)."
      - path: "backend/routers/solve.py"
        issue: "GET /solve/{session_id} returns SolveResultResponse{session_id, solution_id, algorithm_used, move_count, solution_string, generated_at}. Frontend expects solution.steps (SolutionStep[]) — this field does not exist in the response. solution?.steps is always undefined, move lists render empty."
      - path: "frontend/src/lib/api.ts"
        issue: "getSessions() calls api.get('/jobs') — matches no backend route. getSolution() calls api.get('/solve/${sessionId}') — route exists but response shape mismatch (no .steps array)."
    missing:
      - "Add GET /jobs endpoint to backend/routers/jobs.py that returns a list of all solve sessions from the DB (crud.get_all_solve_sessions or equivalent)"
      - "Add GET /solve/{session_id}/steps endpoint (or extend SolveResultResponse with steps: list[SolutionStep]) so the frontend can retrieve individual move steps"
      - "Alternatively: update getSolution() in api.ts to fetch from the correct endpoint and transform response to include steps array"

  - truth: "Start/Stop/Reset/Rescan buttons trigger correct control flag writes"
    status: partial
    reason: "The control flag POST endpoint exists and writes to DB correctly (POST /jobs/{session_id}/control). Start uses POST /jobs/start which also works. However the Start button relies on getSessions() to get the current sessionId — since GET /jobs is missing, sessionId is always null, meaning Stop/Reset/Rescan calls postControlFlag(null!, action) which throws or sends /api/jobs/null/control. Start itself works in isolation."
    artifacts:
      - path: "frontend/src/pages/Dashboard.tsx"
        issue: "sessionId = latestSession?.id ?? null; latestSession comes from getSessions() which returns nothing (GET /jobs missing). doControl mutation calls postControlFlag(sessionId!, action) with sessionId=null."
    missing:
      - "Depends on fixing GET /jobs endpoint — once session list loads, sessionId will be populated and all four control actions will function correctly"

  - truth: "All 5 pages render and show real data — System Logs field name mismatch and missing node filter"
    status: failed
    reason: "Backend LogEntryResponse uses field 'level' (not 'severity'). Frontend SystemLog type declares 'severity'. LogList.tsx accesses log.severity which is always undefined from API responses — severity badges render empty, fatal row highlight never fires. Additionally the backend logs router only accepts query param 'level' (not 'severity') and has no 'node' query param — the frontend sends ?severity=error&node=scanner but these are silently ignored, returning unfiltered results."
    artifacts:
      - path: "backend/routers/logs.py"
        issue: "Query param is named 'level', not 'severity'. No 'node' query param exists. Frontend sends severity and node params that are both ignored."
      - path: "backend/schemas.py"
        issue: "LogEntryResponse.level (line 140) — field name does not match frontend SystemLog.severity"
      - path: "frontend/src/types/api.ts"
        issue: "SystemLog interface has severity: 'info'|'warning'|'error'|'fatal' but API returns level: str"
      - path: "frontend/src/components/logs/LogList.tsx"
        issue: "Accesses log.severity (always undefined from real API). Severity badge styling and fatal row bg-red-950/30 never activate."
    missing:
      - "Rename LogEntryResponse.level to severity in backend/schemas.py (and update logs.py query accordingly), OR add a computed property/alias"
      - "Add 'node' query param to GET /logs in backend/routers/logs.py with WHERE node_id = ? filter"
      - "Align frontend SystemLog.severity with whatever field name the backend settles on"
human_verification:
  - test: "LAN phone access"
    expected: "Navigating to http://<rpi4-ip>:5173 from a phone browser on the same Wi-Fi renders the dashboard UI correctly (sidebar, topbar, page content)"
    why_human: "vite.config.ts has host: '0.0.0.0' which is the necessary and sufficient configuration condition. Actual LAN reachability depends on network topology, firewall rules, and the Pi being online — cannot verify programmatically from this machine."
  - test: "WebSocket live indicator turns green"
    expected: "TopBar shows green pulsing dot and 'Live' text when the FastAPI Socket.IO server is running"
    why_human: "socket.ts is wired correctly to connect to '/socket.io'. Whether the indicator actually turns green requires a live server — cannot verify without running the backend."
---

# Phase 4: Web Dashboard Core Pages — Verification Report

**Phase Goal:** All 5 dashboard pages are functional, accessible from phone/computer on LAN, and connected to live data via WebSocket.
**Verified:** 2026-03-27
**Status:** gaps_found
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (from Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | All 5 pages render and show real data from the database | FAILED | GET /jobs missing; solve response has no .steps array; logs field name mismatch |
| 2 | WebSocket updates Dashboard and Execution Monitor in real time without page refresh | VERIFIED | useSocketEvent('job_state_update') in Dashboard.tsx invalidates queries; useSocketEvent('execution_progress') in ExecutionMonitor.tsx updates liveProgress state |
| 3 | Accessible from a phone browser on the same Wi-Fi network | HUMAN NEEDED | vite.config.ts has host: '0.0.0.0' and port 5173 — config is correct, runtime reachability needs human check |
| 4 | Start/Stop/Reset/Rescan buttons trigger correct control flag writes | PARTIAL | POST /jobs/{session_id}/control exists and writes to DB; Start uses POST /jobs/start correctly; Stop/Reset/Rescan are broken because sessionId is always null (GET /jobs missing) |

**Score:** 2/4 success criteria verified (Truth 2 fully verified; Truth 3 human-needed; Truths 1 and 4 failed due to backend gaps)

---

## Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `frontend/` Vite project | VERIFIED | Scaffolded with all required dependencies |
| `frontend/vite.config.ts` | VERIFIED | host: '0.0.0.0', port: 5173, /api and /socket.io proxy entries present |
| `frontend/components.json` | VERIFIED | shadcn initialized, style: default, baseColor: slate |
| `frontend/src/lib/socket.ts` | VERIFIED | Socket.IO singleton connecting to '/' with path '/socket.io', typed ServerToClientEvents |
| `frontend/src/hooks/useSocket.ts` | VERIFIED | useSocketEvent and useSocketStatus exported, correct cleanup pattern |
| `frontend/src/lib/api.ts` | PARTIAL | All functions exist and use correct axios instance; getSessions() calls /api/jobs which has no matching backend route |
| `frontend/src/App.tsx` | VERIFIED | createBrowserRouter with all 5 routes: /, /results, /execution, /review/:sessionId, /logs |
| `frontend/src/main.tsx` | VERIFIED | QueryClientProvider wraps app, ReactQueryDevtools included |
| `frontend/src/components/layout/AppShell.tsx` | VERIFIED | Outlet rendered, Sidebar and TopBar composed |
| `frontend/src/components/layout/Sidebar.tsx` | VERIFIED | All 5 nav items with correct routes |
| `frontend/src/components/layout/TopBar.tsx` | VERIFIED | useSocketStatus() wired, Live/Disconnected indicator present |
| `frontend/src/pages/Dashboard.tsx` | PARTIAL | getAllNodes, getSessions, useSocketEvent, useMutation all wired; data is empty because GET /jobs missing |
| `frontend/src/pages/SolveResults.tsx` | PARTIAL | useQuery with getSessions, refetchInterval: 10_000; data empty due to missing GET /jobs |
| `frontend/src/pages/ExecutionMonitor.tsx` | PARTIAL | useSocketEvent('execution_progress') wired; session data empty; move list empty due to .steps mismatch |
| `frontend/src/pages/SolutionReview.tsx` | PARTIAL | useParams, useQuery for getSolution wired; .steps always undefined from API |
| `frontend/src/pages/SystemLogs.tsx` | PARTIAL | useQuery with getLogs, refetchInterval: 5_000; severity/node filters silently ignored by backend |
| `frontend/src/components/dashboard/PipelineStepper.tsx` | VERIFIED | Accepts PipelineStatus prop, renders 5 stages |
| `frontend/src/components/dashboard/NodeHealthCard.tsx` | VERIFIED | Renders online/offline badge, last_heartbeat timestamp |
| `frontend/src/components/dashboard/ControlButtons.tsx` | VERIFIED | All 4 buttons present; Start/Stop (AlertDialog) /Reset (AlertDialog) /Rescan; onAction wired |
| `frontend/src/components/results/SessionTable.tsx` | VERIFIED | 6-column table, row click navigates to /review/:id, empty state text |
| `frontend/src/components/review/MoveList.tsx` | VERIFIED | ScrollArea, numbered steps, active highlight bg-blue-600/20 |
| `frontend/src/components/review/StepNavigator.tsx` | VERIFIED | Prev/Play/Next buttons with step counter |
| `frontend/src/components/execution/ProgressHeader.tsx` | VERIFIED | Progress bar with pct value, current/total badge |
| `frontend/src/components/execution/MoveProgressList.tsx` | VERIFIED | Active step highlighted bg-blue-600/20 |
| `frontend/src/components/logs/LogList.tsx` | PARTIAL | Renders rows but accesses log.severity (always undefined from API — field is log.level in backend response) |
| `frontend/src/components/logs/SeverityFilter.tsx` | PARTIAL | ToggleGroup and Select rendered; severity/node values sent as wrong query param names |
| `backend/routers/jobs.py` | PARTIAL | POST /jobs/start, GET /jobs/{session_id}, POST /jobs/{session_id}/control all present; GET /jobs list endpoint MISSING |
| `backend/routers/solve.py` | PARTIAL | GET /solve/{session_id} exists but returns solution_string not steps array |
| `backend/routers/logs.py` | PARTIAL | GET /logs exists; uses query param 'level' not 'severity'; no 'node' param |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| Dashboard.tsx | GET /jobs (list) | getSessions() → api.get('/jobs') | NOT WIRED | GET /jobs route does not exist in backend — will 404 |
| Dashboard.tsx | POST /jobs/start | startSolve() → api.post('/jobs/start') | WIRED | Route exists, writes to DB via crud.create_solve_session |
| Dashboard.tsx | POST /jobs/{id}/control | postControlFlag() → api.post('/jobs/${sessionId}/control') | BROKEN | Route exists but sessionId is always null (depends on missing GET /jobs) |
| Dashboard.tsx | Socket.IO job_state_update | useSocketEvent('job_state_update') | WIRED | Event handler invalidates ['sessions'] and ['nodes'] queries |
| ExecutionMonitor.tsx | Socket.IO execution_progress | useSocketEvent('execution_progress') | WIRED | setLiveProgress called on each event |
| SolveResults.tsx | GET /jobs (list) | getSessions() → api.get('/jobs') | NOT WIRED | Same missing endpoint |
| SolutionReview.tsx | GET /solve/{sessionId} | getSolution() → api.get('/solve/${sessionId}') | PARTIAL | Route exists but response missing .steps array |
| SystemLogs.tsx | GET /logs | getLogs(severity, node) → api.get('/logs', {params:{severity,node}}) | PARTIAL | Route exists; severity param ignored (backend uses 'level'); node param absent in backend |
| TopBar.tsx | Socket.IO connect/disconnect | useSocketStatus() → socket events | WIRED | connect/disconnect handlers update state correctly |

---

## Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|-------------------|--------|
| Dashboard.tsx | sessions (for status, sessionId) | getSessions() → GET /jobs | No — route missing | DISCONNECTED |
| Dashboard.tsx | nodes | getAllNodes() → GET /nodes/status | Yes — DB query exists in nodes.py | FLOWING |
| SolveResults.tsx | sessions | getSessions() → GET /jobs | No — route missing | DISCONNECTED |
| ExecutionMonitor.tsx | sessions (for activeSession) | getSessions() → GET /jobs | No — route missing | DISCONNECTED |
| ExecutionMonitor.tsx | solution.steps | getSolution() → GET /solve/{id} | No — .steps not in response | HOLLOW_PROP |
| SolutionReview.tsx | solution.steps | getSolution() → GET /solve/{id} | No — response has solution_string not steps array | HOLLOW_PROP |
| SystemLogs.tsx | logs[].severity | getLogs() → GET /logs | No — field is 'level' in response, not 'severity' | HOLLOW_PROP |

---

## Behavioral Spot-Checks

Step 7b: SKIPPED — frontend requires a running dev server and backend to test HTTP/WebSocket behavior; all relevant checks are already captured in key link verification above.

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| GUI-01 | 04-01 | Dashboard page — pipeline stage, node health, active job status | PARTIAL | Components exist and are wired; renders empty because GET /jobs is missing |
| GUI-02 | 04-02 | Solve Results page — history table | PARTIAL | SessionTable component complete; data source (GET /jobs) missing |
| GUI-03 | 04-03 | Execution Monitor — live motor progress | PARTIAL | Socket.IO subscription wired; session/step data disconnected |
| GUI-04 | 04-02 | Solution Review — step-by-step move sequence | PARTIAL | MoveList, StepNavigator exist; .steps always empty (API shape mismatch) |
| GUI-05 | 04-03 | System Logs — filtered by severity/node | PARTIAL | Page renders; severity field name wrong; node filter absent in backend |
| GUI-07 | 04-01 | Accessible from phone on LAN | HUMAN NEEDED | vite.config.ts host: '0.0.0.0' is correct configuration |
| GUI-08 | 04-01 | Start/Stop/Reset/Rescan actions | PARTIAL | All 4 buttons exist; Stop/Reset/Rescan broken due to null sessionId from missing GET /jobs |

**Orphaned requirements check:** GUI-06 (3D cube model) is mapped to Phase 5 — correctly not addressed here.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| frontend/src/pages/ExecutionMonitor.tsx | 22 | `(s: any)` type cast for session | Warning | Masks type errors; acceptable given missing list endpoint typing |
| frontend/src/pages/ExecutionMonitor.tsx | 37 | `(s: any)` type cast for solution steps | Warning | Masks the .steps shape mismatch at compile time |
| frontend/src/components/dashboard/ControlButtons.tsx | 22 | `sessionId: _sessionId` (underscore-prefixed unused) | Info | sessionId prop passed but not used in component body — all routing goes through onAction callback |
| backend/routers/logs.py | 7-8 | Comment acknowledges missing crud.get_logs() | Warning | Direct SQL in router is a design smell; not a blocker |

No TODO/FIXME/placeholder stubs found in the 5 page files. All pages are fully implemented (not stub returns). The gaps are API contract mismatches, not missing UI code.

---

## Human Verification Required

### 1. LAN Phone Access

**Test:** Connect a phone to the same Wi-Fi as the RPi4. Start the dev server with `cd frontend && npm run dev`. Navigate to `http://<rpi4-ip>:5173` in the phone browser.
**Expected:** The dark dashboard UI renders — sidebar visible on tablet/desktop, topbar visible on all sizes, page content loads.
**Why human:** vite.config.ts has `host: '0.0.0.0'` which exposes the dev server on all interfaces. Actual reachability depends on network topology and whether port 5173 is open in the Pi's firewall — cannot verify programmatically from this machine.

### 2. WebSocket Live Indicator

**Test:** Start the FastAPI backend (`uvicorn backend.main:fastapi_app --port 8000`) and the Vite dev server. Load the dashboard in a browser.
**Expected:** TopBar shows a green pulsing dot with "Live" text within 2 seconds of page load.
**Why human:** Socket.IO connection depends on both server being live and the /socket.io proxy working end-to-end. Cannot simulate without running services.

---

## Gaps Summary

Three distinct backend/contract issues block goal achievement:

**Gap 1 — Missing `GET /jobs` list endpoint (BLOCKER for GUI-01, GUI-02, GUI-03, GUI-08)**
The frontend calls `getSessions()` → `GET /api/jobs` on Dashboard, SolveResults, and ExecutionMonitor. The backend `jobs.py` only has `GET /jobs/{session_id}` and `GET /jobs/{session_id}/control`. A plain `GET /jobs` returns 404. Without this, session data never loads: pipeline status always shows 'idle', node health grid works but active session card never appears, SolveResults table always shows "No sessions yet", and ExecutionMonitor always shows "No active solve". Control buttons Start works in isolation but Stop/Reset/Rescan all fire against `null` sessionId.

**Gap 2 — `GET /solve/{session_id}` returns wrong response shape for Solution Review and Execution Monitor (BLOCKER for GUI-03, GUI-04)**
`SolveResultResponse` contains `solution_string: str | None` (a raw move string). The frontend expects `solution.steps: SolutionStep[]` — an array of `{step_index, move_notation}` objects. This array is never present in the response, so `solution?.steps ?? []` is always `[]`. Both MoveList (SolutionReview) and MoveProgressList (ExecutionMonitor) render empty. The DB schema has a `solution_steps` table and `get_solution_steps_by_solution()` CRUD exists — the endpoint just needs to include them.

**Gap 3 — Logs field name mismatch and missing filters (PARTIAL break for GUI-05)**
Backend returns `level: str` but frontend reads `log.severity` (always `undefined`). Severity-based badge styling and the `bg-red-950/30` fatal highlight never fire. The severity filter sends `?severity=error` but the backend query param is `?level=...` — the filter is silently ignored. There is also no `node` query param in the backend, so node filtering does not work at all. The page renders and shows log entries (timestamp, node_id, message display correctly), but filtering and severity styling are broken.

All three gaps are backend-side fixes requiring 1-3 new/modified routes. The frontend UI code is complete, well-structured, and correct given the intended API contract.

---

_Verified: 2026-03-27_
_Verifier: Claude (gsd-verifier)_
