---
phase: 04
slug: web-dashboard-core-pages
status: draft
shadcn_initialized: false
preset: none
created: 2026-03-26
---

# Phase 04 — UI Design Contract: Web Dashboard (Core Pages)

> Visual and interaction contract for the Pi³ Rubik's Cube Solver Web Dashboard.
> Stack: React + Tailwind CSS + shadcn/ui + TanStack Query + React Router + Socket.IO client.

> **⚠ Stitch Note:** The user has designs in Stitch. The plan executor MUST use the Stitch MCP to retrieve those designs and use them as the primary visual reference. This spec serves as a fallback/supplement if Stitch is unavailable.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | shadcn/ui (official registry) |
| Preset | dark (system dark mode enforced) |
| Component library | Radix UI (via shadcn) |
| Icon library | lucide-react |
| Font | Inter (Google Fonts — sans-serif, loaded via `@fontsource/inter`) |
| Accent library | Magic UI / Aceternity UI (optional — use for premium animations only) |

### Theme Anchor

Dark industrial theme — slate-950 background, slate-900 card surfaces.
Accent colors reference Rubik's cube faces:

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-bg` | `#020617` (slate-950) | Page background |
| `--color-surface` | `#0f172a` (slate-900) | Cards, panels |
| `--color-border` | `#1e293b` (slate-800) | Dividers, card outlines |
| `--color-text-primary` | `#f8fafc` (slate-50) | Headings, primary text |
| `--color-text-muted` | `#94a3b8` (slate-400) | Labels, secondary text |
| `--color-accent-blue` | `#3b82f6` (blue-500) | Primary CTA buttons, active nav |
| `--color-success` | `#22c55e` (green-500) | Node online status, done state |
| `--color-warning` | `#f59e0b` (amber-500) | Scanning/Solving pipeline states |
| `--color-destructive` | `#ef4444` (red-500) | Error state, Stop button, Fatal logs |
| `--color-muted-text` | `#64748b` (slate-500) | Offline status, empty state |

---

## Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Icon gaps, badge padding |
| sm | 8px | Compact element spacing |
| md | 16px | Default card padding, form field gaps |
| lg | 24px | Section padding |
| xl | 32px | Layout gaps between sections |
| 2xl | 48px | Page top/bottom padding |
| 3xl | 64px | Hero area or full-page gap |

Exceptions: none

---

## Typography

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body | 14px | 400 | 1.5 |
| Label | 12px | 500 | 1.4 |
| Heading (h3/section) | 18px | 600 | 1.3 |
| Page title (h1) | 24px | 700 | 1.2 |
| Display (stat number) | 36px | 700 | 1.0 |
| Code / move notation | 13px (monospace) | 500 | 1.4 |

Font stack: `Inter, ui-sans-serif, system-ui, sans-serif`

---

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `#020617` (slate-950) | Page background |
| Secondary (30%) | `#0f172a` (slate-900) | Cards, sidebar, nav |
| Accent (10%) | `#3b82f6` (blue-500) | Active nav item, primary CTA, real-time pulse ring |
| Destructive | `#ef4444` (red-500) | Stop button, Error badge, Fatal log row highlight |

Accent reserved for: active navigation link underline, Start Solve button, WebSocket live indicator pulse, progress bar fill.

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Primary CTA | "Start Solve" |
| Stop action | "Stop" |
| Reset action | "Reset" |
| Rescan action | "Rescan" |
| Empty state (Solve Results) | "No solve sessions yet" / "Start a solve to see results here." |
| Empty state (System Logs) | "No log entries" / "Events will appear here once a solve runs." |
| Empty state (Execution Monitor) | "No active solve" / "Start a solve to track motor progress." |
| Error state (node offline) | "[Node Name] is offline" / "Check the Pi connection and refresh." |
| Error state (API failure) | "Failed to load data" / "Retry or check the server." |
| Solving pipeline stages | Idle → Scanning → Solving → Executing → Done / Error |
| Node status labels | "Online" / "Offline" |
| Destructive confirmation (Stop) | "Stop: This will halt the current solve sequence." |
| Destructive confirmation (Reset) | "Reset: This will clear the current session and return to Idle." |

---

## Layout Architecture

### App Shell

- **Sidebar** (desktop): fixed left sidebar, 240px wide, collapsible on mobile to bottom nav bar.
- **Nav items**: Dashboard, Solve Results, Execution Monitor, Solution Review, System Logs.
- **Top bar**: App name "Pi³ Solver", WebSocket connection status indicator (green pulse = live, red = disconnected), current system status badge (pipeline stage).
- **Content area**: full remaining width, scrollable, max-width none (fills screen).
- **Mobile**: Sidebar collapses to tab bar at bottom. Content area spans full width. Touch-friendly tap targets (min 44px).

### Responsive Breakpoints

| Breakpoint | Behavior |
|-----------|---------|
| < 640px | Bottom tab nav, single-column content, stacked cards |
| 640–1024px | Collapsible left sidebar, 2-col grids |
| > 1024px | Fixed sidebar always visible, multi-column grids |

---

## Per-Page Specs

### Page 1: Dashboard (`/`)

**Purpose:** Real-time overview of pipeline state, node health, and control actions.

**Layout:**
- Top section: Pipeline stage indicator — horizontal stepper with 5 stages (Idle → Scanning → Solving → Executing → Done/Error). Active stage highlighted with accent color, Error state shows destructive color.
- Middle left (60%): Node Health Grid — 4 cards (Scanner Pi, Solver Pi, Motor Pi, Database Pi), each showing node name, online/offline badge, last heartbeat timestamp.
- Middle right (40%): Current Job Card — session ID, current status, cube state string if available, elapsed time.
- Bottom: Control Button Row — "Start Solve" (primary), "Stop" (destructive variant), "Reset" (outline), "Rescan" (outline). Buttons disabled based on current pipeline state.

**shadcn/ui Components:**
- `Card`, `Badge`, `Button`, `Separator`
- Pipeline stepper: custom component using `div` + Tailwind (no shadcn stepper available)
- Node health: `Card` + `Badge` (green/red)

**Real-time Behavior (Socket.IO):**
- Subscribes to `job_state_update` event → updates pipeline stage and node health immediately.
- WebSocket connected indicator pulses (uses `animate-pulse` Tailwind class) in top bar.
- On reconnect: TanStack Query re-fetches `/jobs/{id}` and `/nodes/status` snapshot.

**States:**
- Loading: Skeleton placeholders for all cards.
- No active job (Idle): "No active solve. Press Start Solve to begin." below control buttons.
- Error state: Pipeline stage shows "Error" in destructive red; error message displayed inline.

---

### Page 2: Solve Results (`/results`)

**Purpose:** History of all past solve sessions.

**Layout:**
- Page title: "Solve History"
- Filter/Sort bar: Date range picker (shadcn `DatePickerWithRange`), sort by (move count / solve time).
- Data table: columns — Session ID, Date, Algorithm, Move Count, Solve Time, Status badge.
- Row click → navigates to `/review/:sessionId` (Solution Review page).

**shadcn/ui Components:**
- `DataTable` (TanStack Table via shadcn recipe), `Badge`, `Button`, `Input` (search)

**Data Source:** `GET /solve/{session_id}` per session; list from `GET /jobs` history.

**States:**
- Loading: Table skeleton (5 placeholder rows).
- Empty: "No solve sessions yet" with a CTA button linking to Dashboard.
- Error: Inline error banner with retry button.

---

### Page 3: Execution Monitor (`/execution`)

**Purpose:** Live progress of the current motor execution.

**Layout:**
- Header: Session ID + status badge.
- Progress bar: `shadcn Progress` component showing `pct_complete` from WebSocket.
- Live move list: scrollable list of all moves; current move highlighted with accent blue; completed moves shown with muted text + checkmark icon.
- Stats row: Current step / Total steps, Estimated remaining time (calculated from average step time).

**shadcn/ui Components:**
- `Progress`, `ScrollArea`, `Badge`, `Card`

**Real-time Behavior (Socket.IO):**
- Subscribes to `execution_progress` event → updates current step, pct_complete, and move highlight in real time without full re-render.

**States:**
- Loading: Skeleton for progress bar and move list.
- No active execution (not Executing state): "No active solve. Go to Dashboard to start one." with link.
- Execution complete: Progress shows 100%, all moves checked, "Execution complete" banner.
- Error during execution: Error banner above move list.

---

### Page 4: Solution Review (`/review/:sessionId`)

**Purpose:** Full move sequence review for a selected solve; step-by-step playback.

**Layout:**
- Header: Session ID, Algorithm used, Move count badge, Date.
- Move sequence: Scrollable numbered list of moves in move notation (e.g., R U R' U'). Monospace font.
- Step Navigator: Previous / Next buttons to highlight one move at a time; current move index shown.
- Playback controls: "Play All" button that auto-advances through moves at configurable speed (250ms default).
- Back button: returns to Solve Results.

**shadcn/ui Components:**
- `ScrollArea`, `Button`, `Badge`, `Separator`
- Move list item: custom component with index + notation + highlight state

**Data Source:** `GET /solve/{sessionId}` → solution steps array.

**States:**
- Loading: Skeleton for move list.
- Session not found: "Session not found." with back button.
- Empty moves: "No moves recorded for this session."

---

### Page 5: System Logs (`/logs`)

**Purpose:** Timestamped event log with severity filtering.

**Layout:**
- Filter row: Severity filter buttons (All / Info / Warning / Error / Fatal), Node filter dropdown (All / Scanner / Solver / Motor / Database).
- Log list: Virtualized scrollable list (use `ScrollArea`). Each entry: timestamp (compact), node badge, severity badge, message.
- Auto-scroll toggle: "Live" button (enabled by default) — auto-scrolls to bottom on new entries.
- Fatal log rows: highlighted with subtle destructive red background.

**shadcn/ui Components:**
- `ScrollArea`, `Badge`, `Button`, `Select` (node filter), `ToggleGroup` (severity filter)

**Data Source:** `GET /logs` with query params `?severity=error&node=scanner`.

**States:**
- Loading: Skeleton list.
- Empty: "No log entries yet."
- Fatal entry: Row background `bg-red-950/30` + `text-red-400` message color + `FATAL` badge variant.

---

## Third-Party Component Registry

| Registry | Components | Safety Gate |
|----------|-----------|-------------|
| shadcn/ui (official) | Card, Badge, Button, Progress, ScrollArea, DataTable, Select, ToggleGroup, Separator | Not required |
| Magic UI | `NumberTicker` (stat counters), `AnimatedBeam` (pipeline connector), `BorderBeam` (card accents) | Source review required before use |
| Aceternity UI | `BackgroundGradient` (node cards), `MovingBorderButton` (Start Solve CTA) | Source review required before use |

**Rule:** Magic UI / Aceternity UI components must be reviewed via `shadcn view <component>` or copied source-first. No CDN imports.

---

## Interaction Contracts

| Trigger | Behavior |
|---------|----------|
| WebSocket connects | Green pulse indicator in top bar; no toast |
| WebSocket disconnects | Amber pulse + "Disconnected" tooltip on indicator |
| job_state_update event | Pipeline stepper + node health update instantly (optimistic) |
| execution_progress event | Move list + progress bar update (no re-fetch) |
| Start Solve click | Button disabled immediately (optimistic); re-enables on error |
| Stop / Reset click | Confirmation dialog (`shadcn AlertDialog`) before API call |
| Rescan click | Disabled during Scanning state; triggers API call + toast feedback |
| API error (any) | `shadcn Toast` (destructive variant) with retry option |
| Navigation | React Router `<Link>` with no full-page reload; active route highlighted in sidebar |

---

## Responsive Contracts (Phone LAN Access)

- All 5 pages must be usable on a 390px viewport (iPhone 14 width).
- Control buttons on Dashboard: full-width stacked on mobile.
- DataTable on Solve Results: horizontally scrollable with column pinning on Session ID.
- Move list on Execution Monitor: full-width, larger tap targets (44px min height).
- Sidebar collapses to bottom navigation with icon + label tabs.
- Touch targets minimum 44×44px (WCAG 2.5.5).

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending

---

*Phase: 04-web-dashboard-core-pages*
*UI spec generated: 2026-03-26*
*Note: Cross-reference with Stitch designs via Stitch MCP before finalizing executor tasks.*
