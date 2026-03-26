# Phase 04: Web Dashboard (Core Pages) — Research

**Researched:** 2026-03-26
**Status:** Complete

---

## Research Scope

Answering: "What do I need to know to PLAN Phase 4 well?"

Phase goal: Build 5 React pages (Dashboard, Solve Results, Execution Monitor, Solution Review, System Logs) connected to the FastAPI backend via REST (TanStack Query) and WebSocket (Socket.IO client).

---

## 1. Project Scaffold: Vite + React + TypeScript + Tailwind + shadcn/ui

### Setup Commands (in order)

```bash
# 1. Scaffold with Vite
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install

# 2. Install Tailwind CSS v4 (latest as of 2025)
npm install tailwindcss @tailwindcss/vite
# Configure vite.config.ts to include tailwindcss() plugin
# In index.css: @import "tailwindcss";

# 3. Initialize shadcn/ui
npx shadcn@latest init
# Select: dark theme, slate base color, CSS variables
# This creates: components.json, src/components/ui/, src/lib/utils.ts
```

### Key Decisions

- **Vite** (not CRA) — faster dev server
- **TypeScript** throughout — backend API types can be inferred from Pydantic schemas
- **Tailwind v4** — new `@tailwindcss/vite` plugin, `@import "tailwindcss"` syntax (not `tailwind.config.js`)
- **shadcn/ui** — components copied into `src/components/ui/` (not installed as npm package)
- **`@fontsource/inter`** — self-hosted Inter font (no Google CDN dependency on LAN)

### File Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/               # shadcn copied components
│   │   ├── layout/           # AppShell, Sidebar, TopBar
│   │   └── [feature]/        # Page-specific components
│   ├── hooks/
│   │   ├── useSocket.ts      # Socket.IO singleton + events
│   │   └── useJobState.ts    # TanStack Query for job state
│   ├── lib/
│   │   ├── api.ts            # axios/fetch base client
│   │   └── utils.ts          # shadcn cn() utility
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── SolveResults.tsx
│   │   ├── ExecutionMonitor.tsx
│   │   ├── SolutionReview.tsx
│   │   └── SystemLogs.tsx
│   ├── types/
│   │   └── api.ts            # TypeScript types mirroring backend Pydantic schemas
│   ├── App.tsx               # React Router routes
│   └── main.tsx
├── index.html
├── vite.config.ts
└── tailwind.config.ts        # (v3 only — v4 uses vite plugin)
```

---

## 2. Socket.IO Client Integration (React)

### Pattern: Single Singleton + React Context

The backend uses `python-socketio` AsyncServer. The client uses `socket.io-client`.

```bash
npm install socket.io-client
```

**Critical: use a singleton socket** — do NOT call `io()` inside components. One reconnect loop for the whole app.

```typescript
// src/lib/socket.ts — singleton
import { io, Socket } from 'socket.io-client';

interface ServerToClientEvents {
  job_state_update: (data: JobStatePayload) => void;
  execution_progress: (data: ExecutionProgressPayload) => void;
}

const socket: Socket<ServerToClientEvents> = io(
  import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  {
    path: '/socket.io',           // default python-socketio path
    transports: ['websocket'],    // skip long-polling for lower latency
    autoConnect: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 2000,
  }
);

export default socket;
```

```typescript
// src/hooks/useSocket.ts — typed event subscriber
import { useEffect } from 'react';
import socket from '@/lib/socket';

export function useSocketEvent<K extends keyof ServerToClientEvents>(
  event: K,
  handler: ServerToClientEvents[K]
) {
  useEffect(() => {
    socket.on(event, handler);
    return () => { socket.off(event, handler); };
  }, [event, handler]);
}
```

### Connection Status Detection

```typescript
const [connected, setConnected] = useState(socket.connected);
useEffect(() => {
  socket.on('connect', () => setConnected(true));
  socket.on('disconnect', () => setConnected(false));
  return () => { socket.off('connect'); socket.off('disconnect'); };
}, []);
```

### Payload Types (from backend CONTEXT.md)

```typescript
interface JobStatePayload {
  session_id: string;
  status: 'idle' | 'scanning' | 'solving' | 'executing' | 'done' | 'error';
  node_status: Record<string, boolean>; // node_name → online
}

interface ExecutionProgressPayload {
  session_id: string;
  current_step: number;
  total_steps: number;
  move: string;       // e.g. "R U R' U'"
  pct_complete: number; // 0.0 – 1.0
}
```

---

## 3. TanStack Query v5 with FastAPI REST

```bash
npm install @tanstack/react-query @tanstack/react-query-devtools
```

### QueryClient Configuration

```typescript
// src/main.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5_000,       // 5s — data stays fresh
      retry: 2,
      refetchOnWindowFocus: true,
    },
  },
});
```

### Key Patterns

**Snapshot fetch** (initial data, invalidated on socket events):
```typescript
const { data: jobState } = useQuery({
  queryKey: ['job', sessionId],
  queryFn: () => fetch(`/jobs/${sessionId}`).then(r => r.json()),
  staleTime: 10_000,
});
```

**Polling** (for pages without WebSocket — e.g. Solve Results):
```typescript
const { data: sessions } = useQuery({
  queryKey: ['sessions'],
  queryFn: fetchAllSessions,
  refetchInterval: 5_000,   // poll every 5s
});
```

**Invalidate on Socket.IO event** (Dashboard + Execution Monitor):
```typescript
const queryClient = useQueryClient();
useSocketEvent('job_state_update', () => {
  queryClient.invalidateQueries({ queryKey: ['job'] });
  queryClient.invalidateQueries({ queryKey: ['nodes'] });
});
```

**Control flag mutation** (Start/Stop/Reset buttons):
```typescript
const { mutate: startSolve } = useMutation({
  mutationFn: (sessionId: string) =>
    fetch(`/jobs/${sessionId}/control`, {
      method: 'POST',
      body: JSON.stringify({ action: 'start' }),
    }),
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ['job'] }),
});
```

---

## 4. React Router v7 (SPA Mode)

React Router v7 released stable Nov 2024. Use `createBrowserRouter` + `<RouterProvider>`.

```bash
npm install react-router-dom
```

```typescript
// src/App.tsx
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import AppShell from '@/components/layout/AppShell';
import Dashboard from '@/pages/Dashboard';
import SolveResults from '@/pages/SolveResults';
import ExecutionMonitor from '@/pages/ExecutionMonitor';
import SolutionReview from '@/pages/SolutionReview';
import SystemLogs from '@/pages/SystemLogs';

const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,           // persistent sidebar + topbar
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'results', element: <SolveResults /> },
      { path: 'execution', element: <ExecutionMonitor /> },
      { path: 'review/:sessionId', element: <SolutionReview /> },
      { path: 'logs', element: <SystemLogs /> },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
```

AppShell renders `<Outlet />` where page content goes.

---

## 5. Backend Integration Points

### API Base URL

Use Vite env variable:
```
VITE_API_URL=http://localhost:8000
```

For LAN access from phone: change to `VITE_API_URL=http://192.168.x.x:8000`

### CORS

Backend already allows all origins (`*`) per Phase 2 decisions (D-07 — Claude discretion).
No special headers needed in API calls.

### Key Endpoints (from Phase 2 CONTEXT.md)

| Action | Endpoint |
|--------|---------|
| Get job state | `GET /jobs/{session_id}` |
| Start solve | `POST /jobs/start` |
| Write control flag | `POST /jobs/{session_id}/control` |
| Get all nodes | `GET /nodes/status` |
| Get solution | `GET /solve/{session_id}` |
| Get system logs | `GET /logs?severity=error&node=scanner` |
| Get execution run | `GET /execute/{session_id}` |

---

## 6. Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Socket.IO version mismatch (python-socketio v5 ↔ socket.io-client v4) | Use `socket.io-client@^4` — compatible with python-socketio v5 AsyncServer |
| CORS on LAN (phone accessing Rpi4 IP) | FastAPI already configured with `allow_origins=["*"]` |
| Tailwind v4 breaking changes | Use `@tailwindcss/vite` plugin, not `tailwind.config.js` — shadcn CLI v0.9+ handles this |
| shadcn/ui components importing wrong paths | Run `npx shadcn@latest init` first — sets `components.json` correctly |
| Phone LAN access not working | Vite dev server must bind to `0.0.0.0`: `vite --host` |

---

## 7. Validation Architecture

### Test Strategy

- **Unit tests**: Vitest for hook logic (`useJobState`, `useSocket`)
- **Component tests**: React Testing Library for Dashboard, Logs (stubbed data)
- **E2E tests**: Playwright or manual browser testing (Planner's discretion)

### Acceptance Validation by Requirement

| Req ID | Validation Method |
|--------|------------------|
| GUI-01 | Dashboard page renders with real node/job data from `/nodes/status` + `/jobs` |
| GUI-02 | Solve Results page shows session history rows from `/solve/` |
| GUI-03 | Execution Monitor shows progress bar + move list from `/execute/` |
| GUI-04 | Solution Review page loads correct move sequence from `/solve/{id}` |
| GUI-05 | System Logs shows filtered rows from `/logs?severity=...` |
| GUI-07 | Access `http://192.168.x.x:5173` from phone browser on LAN |
| GUI-08 | Clicking Start/Stop/Reset/Rescan sends correct POST to `/jobs/{id}/control` |

---

## RESEARCH COMPLETE

Phase 4 research complete. Key findings:
- **Stack**: Vite + React-TS + Tailwind v4 + shadcn/ui + socket.io-client v4 + @tanstack/react-query v5 + react-router-dom v7
- **Socket.IO**: Singleton pattern with typed event interfaces; hybrid approach (snapshot fetch + socket invalidation)
- **Plan split**: 3 plans match ROADMAP.md — scaffold+Dashboard, Solve Results+Solution Review, Execution Monitor+System Logs
