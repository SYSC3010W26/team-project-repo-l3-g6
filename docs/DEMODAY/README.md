# PI³ Demo Day Guide

This folder is the operator-facing guide for running the PI³ demo reliably on presentation day.

## Contents

- `RUNBOOK.md` — exact launch order and go-live sequence
- `CHECKLIST.md` — quick preflight + live demo checklist
- `TROUBLESHOOTING.md` — rapid failure diagnosis and recovery
- `ROUTES-AND-STATES.md` — what each page should show during the demo

## Core Rule

Bring systems up in this order:

1. Backend API
2. Frontend UI
3. Simulation/event feeders (if hardware is unavailable)

Do **not** start with frontend first and assume backend catches up. Many "UI is broken" reports are startup-order artifacts.
