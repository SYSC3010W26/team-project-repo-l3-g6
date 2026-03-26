# Phase 04: Web Dashboard (Core Pages) - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the 5-page frontend dashboard (Dashboard, Solve Results, Execution Monitor, Solution Review, System Logs) that connects to the FastAPI backend.
</domain>

<decisions>
## Implementation Decisions

### Framework Choice
- **D-01:** Use **React** as the frontend framework. Recommended choice for its ecosystem (specifically useful for 3D rendering with `react-three-fiber` in Phase 5).

### UI Styling
- **D-02:** Use **Tailwind CSS**. Leverage `shadcn/ui` components (or Magic UI / Aceternity UI) where helpful for complex or premium elements. This gives maximum flexibility while looking highly professional.

### Data Fetching
- **D-03:** Use **TanStack Query** (React Query) for all data fetching against the REST API. It handles caching, retries, and loading/error states out-of-the-box.

### Layout Architecture
- **D-04:** Use **React Router** for a multi-page layout architecture. Each of the 5 views will have its own URL route for clean separation and bookmarkability.

### the agent's Discretion
- Project setup tools (e.g., Vite) – Vite is recommended for a standard SPA.
- Component file structure and Shadcn UI installation method.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — Phase 4 requirements: GUI-01 through GUI-05, and GUI-07, GUI-08.
- `.planning/codebase/STACK.md` — To ensure alignment with any backend assumptions.

### External Tools & Design References
- **Stitch MVP**: The user has designs built in Stitch. Downstream planner/executor **MUST** use the **Stitch MCP** server (if available/configured) to access and reference exactly what the user designed.
- **Claude Skills**: The user mentioned having frontend skills under `~/.claude/` (potentially `~/.claude/skills/`). Downstream agents should check there for specific React/Tailwind guidelines if applicable.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None specifically for frontend yet (new codebase).

### Integration Points
- Backend runs on `http://localhost:8000` (FastAPI).
- WebSocket connection (Socket.IO) needed for `job_state_update` and `execution_progress` events.
- Endpoints to fetch from are defined in Phase 2 backend (e.g., `/jobs/{id}`, `/scan/{id}`, `/logs`, etc.).
</code_context>

<specifics>
## Specific Ideas
- User specifically mentioned integrating `shadcn/ui` components, and potentially others like **Magic UI** or **Aceternity UI** for a premium feel. Do not hesitate to use these to enhance the visual design.
- Make sure to document the `Stitch MCP` usage prominently so the executor pulls the user's intended designs.
</specifics>

<deferred>
## Deferred Ideas
None.
</deferred>
