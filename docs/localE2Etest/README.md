# Local E2E Test Docs (PI³)

This folder is the canonical local end-to-end test guide.

## Contents

- `RUNBOOK.md` — exact local startup and execution order
- `ASSERTIONS.md` — page-by-page and data-flow assertions
- `DEBUGGING.md` — failure diagnosis flow
- `SCRIPT-MAPPING.md` — exact script command mapping in this repo

## Current script inventory

Detected scripts relevant to E2E/demo:

- `simulate_demo.py` (root)
- `EndToEndDemo/Run_Tests.py` (legacy socket-based demo harness)
- `scripts/start-stitch-mcp.sh` (not part of PI³ E2E runtime)

Use `simulate_demo.py` for the API-driven UI E2E flow.
