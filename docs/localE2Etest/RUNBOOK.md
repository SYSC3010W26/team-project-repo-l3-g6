# Local E2E Runbook (PI³)

## Scope

This runbook validates the current frontend + backend integration using local simulation.

## Prerequisites

- Python environment with backend dependencies installed
- Node/npm installed
- Repo root as working directory

## 1) Start backend API (Terminal A)

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Expected: backend responds at `http://localhost:8000/`.

## 2) Start frontend (Terminal B)

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 4173
```

Open: `http://localhost:4173`

## 3) Start local simulation feed (Terminal C)

```bash
python simulate_demo.py
```

Notes:
- Uses `PI_SERVER_IP` / `PI_SERVER_PORT` if provided.
- Default target: `http://localhost:8000`.
- Simulates nodes, scan submit, solve submit, execution progression, and done transition.

## 4) Run E2E verification sweep

Visit and verify:

- `/` Dashboard
- `/execution`
- `/results`
- `/review/<sessionId from results>`
- `/logs`

Use checks listed in `ASSERTIONS.md`.

## 5) Single-command launcher (manual sequence)

Because this stack uses multiple long-running processes, use this sequence in separate terminals:

```bash
# A
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# B
cd frontend && npm run dev -- --host 0.0.0.0 --port 4173

# C
python simulate_demo.py
```

## 6) Stop sequence

1. Stop simulator (Ctrl+C)
2. Stop frontend
3. Stop backend
