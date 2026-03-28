# PI³ End-to-End Demo Runbook

This runbook brings up the full PI³ experience (backend + frontend + simulation) so every page behaves like demo-day.

## Preconditions

- Run from repo root: `team-project-repo-l3-g6/`
- Node + npm installed
- Python environment for backend scripts available

## 1) Start backend API

Use your existing backend start command in terminal A.

Typical pattern (adjust to your project command):

```bash
# terminal A
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

If your project uses another entrypoint, use that instead.

## 2) Start frontend

In terminal B:

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 4173
```

Open `http://localhost:4173`.

## 3) Start simulation feeds

In terminal C (server-pi simulation):

```bash
# pick the script in scripts/ that emits session/scanner/solver/execution/log events
bash scripts/<server-sim-script>.sh
```

In terminal D (teammate-pi simulation, if applicable):

```bash
bash scripts/<teammate-sim-script>.sh
```

> Note: currently this repo only shows `scripts/start-stitch-mcp.sh` from automated scan. If your simulation scripts are untracked/local, run them from your local copies.

## 4) Verify each page in order

1. **Dashboard** (`/`)
   - pipeline stage changes over time
   - node health updates
   - cube state updates from scan feed
   - controls enabled/disabled by state
2. **Execution Monitor** (`/execution`)
   - current move index increments
   - completion % rises
   - move list highlights current step
3. **Solve Results** (`/results`)
   - sessions appear with solve metadata
   - opening a session routes to review
4. **Solution Review** (`/review/:sessionId`)
   - step navigation buttons work
   - move list follows current step
5. **System Logs** (`/logs`)
   - entries stream in
   - severity and node filters change results

## 5) Use React Query Devtools to confirm E2E health

Bottom-left devtools panel checks:

- query status should be `success` for `sessions`, `nodes`, `logs`, `solution:*` when backend is up
- `updatedAt` should move forward on polling/refetch
- if status is `error`, inspect endpoint/network and backend logs
- compare query data timestamps with incoming simulation events

## 6) Common failure modes

- Old frontend visible: hard refresh (`Cmd+Shift+R`) + ensure only one Vite server is running.
- 2-color cube: no valid 54-face cube payload arriving yet; verify scan simulation payload and API ingest.
- Review page empty/unusable: no completed sessions/solution steps in DB yet.
- Logs page empty: simulation not posting system logs or severity/node filters too narrow.

## 7) Demo-day quick start (minimal)

```bash
# A: backend
<your backend start command>

# B: frontend
cd frontend && npm run dev -- --host 0.0.0.0 --port 4173

# C/D: simulations
bash scripts/<server-sim-script>.sh
bash scripts/<teammate-sim-script>.sh
```

Then verify routes: `/`, `/execution`, `/results`, `/review/<known-session-id>`, `/logs`.
