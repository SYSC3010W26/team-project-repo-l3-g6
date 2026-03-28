# Local E2E Debugging (PI³)

## 1) Old UI persists

- hard refresh browser (`Cmd+Shift+R`)
- ensure only one Vite server exists:
  ```bash
  lsof -i :4173
  lsof -i :5173
  ```
- kill stale node/vite processes and restart frontend

## 2) Cube looks wrong (e.g., stripe / few colors)

- simulator may not have submitted a valid/complete cube state yet
- verify backend receives `/scan/submit`
- inspect Dashboard query data in React Query devtools

## 3) Review page not usable

- verify `/results` contains a session
- navigate via results card click to ensure valid session id
- confirm solution submit step completed in simulator output

## 4) Logs empty

- set filters to broadest (`all`)
- verify simulator/backend are emitting logs/events
- inspect `logs` query status and data in React Query panel

## 5) React Query interpretation

- `success` + moving `updatedAt` => live loop healthy
- `error` => backend/network endpoint issue first
- success but wrong UI => frontend rendering/state mapping issue

## 6) Backend unreachable from simulator

Set explicit target before running simulator:

```bash
PI_SERVER_IP=localhost PI_SERVER_PORT=8000 python simulate_demo.py
```
