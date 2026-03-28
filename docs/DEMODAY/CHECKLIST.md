# PI³ Demo Day Checklist

## Preflight (before audience)

- [ ] Backend starts without crash loop
- [ ] Frontend starts on expected port (`4173`)
- [ ] UI shows **PI³** branding in top bar and sidebar
- [ ] React Query devtools visible in lower-left
- [ ] Simulation/hardware feed running
- [ ] Dashboard shows node/session data updates
- [ ] At least one session exists for Results/Review demo
- [ ] Logs page has fresh entries

## Live demo checkpoints

### Dashboard (`/`)
- [ ] Pipeline/status visible
- [ ] Node health visible
- [ ] Cube panel visible (state updates if feed active)
- [ ] Control buttons visibly state-gated

### Execution Monitor (`/execution`)
- [ ] Progress % visible
- [ ] Move list visible
- [ ] Current move indicator updates during run

### Solve Results (`/results`)
- [ ] Session cards visible
- [ ] Session click navigates to review page

### Solution Review (`/review/:sessionId`)
- [ ] Step navigation buttons are clickable and readable
- [ ] Move list tracks selected step

### System Logs (`/logs`)
- [ ] Terminal-style list visible
- [ ] Severity filter changes output
- [ ] Node filter changes output

## Recovery quick checks (if something looks wrong)

- [ ] Is backend up?
- [ ] Are React Query keys showing `success`?
- [ ] Is `updatedAt` moving on polling queries?
- [ ] Are simulation scripts still running?
- [ ] Did browser cache get hard-refreshed?
