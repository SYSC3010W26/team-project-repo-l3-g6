# PI³ Demo Day Runbook

## 0) Pre-demo setup

- Repo up to date on demo machine
- Power/network stable
- Known ports available:
  - backend: `8000` (typical)
  - frontend: `4173` (this project’s current convention)

## 1) Start backend (Terminal A)

Use your project’s backend start command.

Typical command:

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Expected: API boots cleanly, no import/runtime crash loop.

## 2) Start frontend (Terminal B)

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 4173
```

Open:
- Local: `http://localhost:4173`
- LAN device: `http://<server-pi-ip>:4173`

Expected branding and shell:
- top bar: **PI³**
- sidebar brand: **PI³**
- dark navy + purple/cyan accents

## 3) Start event feeds / simulation (Terminal C/D)

Use your team’s scripts under `scripts/`:

```bash
bash scripts/<server-sim-script>.sh
bash scripts/<teammate-sim-script>.sh
```

If those files are local-only and not committed, use your local paths.

## 4) Demo flow (page order)

1. Dashboard (`/`)
2. Execution Monitor (`/execution`)
3. Solve Results (`/results`)
4. Solution Review (`/review/<sessionId>`)
5. System Logs (`/logs`)

Keep React Query devtools open in bottom-left while demoing to prove live data activity.

## 5) Hard reset flow (if UI looks stale)

1. Stop frontend dev server
2. Confirm no old dev servers remain:
   ```bash
   lsof -i :4173
   lsof -i :5173
   ```
3. Kill stale node/vite PIDs
4. Restart frontend command from step 2
5. Browser hard refresh (`Cmd+Shift+R`)

## 6) End-of-demo shutdown

- Stop simulation scripts first
- Stop frontend
- Stop backend

This avoids noisy reconnect loops in logs while services disappear.
