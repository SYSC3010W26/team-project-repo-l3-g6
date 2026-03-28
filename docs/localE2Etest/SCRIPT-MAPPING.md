# Script Mapping (Local E2E)

This file maps concrete commands to scripts detected in this repository.

## Primary local E2E script

### `simulate_demo.py`

Purpose:
- API-driven simulation for frontend/backend demo flow
- emits heartbeats
- starts a job
- submits scan state
- transitions to solving/executing/done
- submits solution moves

Command:

```bash
python simulate_demo.py
```

Optional target override:

```bash
PI_SERVER_IP=<host> PI_SERVER_PORT=<port> python simulate_demo.py
```

## Legacy demo harness

### `EndToEndDemo/Run_Tests.py`

Purpose:
- legacy socket-style node-stub demo harness (separate from current FastAPI UI flow)

Command:

```bash
python EndToEndDemo/Run_Tests.py
```

Use only if you explicitly need the older stubbed network demo.

## Non-E2E helper

### `scripts/start-stitch-mcp.sh`

Purpose:
- starts Stitch MCP helper, not required for PI³ local E2E runtime.

## Recommended default for current frontend E2E

Use:
1. backend via uvicorn
2. frontend via Vite (`4173`)
3. `python simulate_demo.py`
