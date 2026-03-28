# Local E2E Assertions (PI³)

## A. Global shell assertions

- [ ] Top bar branding shows **PI³**
- [ ] Sidebar branding shows **PI³**
- [ ] No stale old branding text appears (e.g., Rubik's Solver)

## B. Data-flow assertions via React Query Devtools

Open lower-left React Query panel:

- [ ] `sessions` query reaches `success`
- [ ] `logs` query reaches `success`
- [ ] `solution:<sessionId>` reaches `success` when reviewing
- [ ] `updatedAt` changes over time while simulator runs
- [ ] query payload contents reflect simulated session and progress

## C. Dashboard (`/`)

- [ ] Session/pipeline region is populated
- [ ] Node health shows active heartbeat-driven state
- [ ] Cube region remains rendered
- [ ] Activity panel reflects current session behavior

## D. Execution Monitor (`/execution`)

- [ ] Progress block rendered
- [ ] Move sequence rendered
- [ ] Current step/progress updates during simulation
- [ ] Completion state appears when simulator transitions to done

## E. Solve Results (`/results`)

- [ ] At least one session card appears after simulation starts
- [ ] Session metadata is readable
- [ ] Card click navigates to corresponding review route

## F. Solution Review (`/review/:sessionId`)

- [ ] Session header renders
- [ ] Move list renders
- [ ] Navigation buttons are usable and advance/reverse step

## G. System Logs (`/logs`)

- [ ] Console shell renders
- [ ] Entry counters render
- [ ] Severity and node filters are interactive
- [ ] Log stream/empty state remains mounted and readable
