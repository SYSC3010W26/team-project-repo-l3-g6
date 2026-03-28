# PI³ Routes and Expected Demo States

## `/` Dashboard

Expected:
- PI³ shell and branding
- Pipeline/session summary
- Node health cards
- Cube panel
- Action controls
- Activity/terminal panel

Offline fallback is acceptable if backend is intentionally down, but page should remain structured and readable.

## `/execution` Execution Monitor

Expected during active run:
- Progress percentage updates
- Current step index updates
- Move list with active step highlight

Expected with no active run:
- Clear "No active solve" state
- Navigation back to dashboard

## `/results` Solve Results

Expected:
- Session cards list
- Session metadata
- Card click opens review page

No-session fallback should remain mounted and informative.

## `/review/:sessionId` Solution Review

Expected:
- Session metadata
- Move list
- Step navigation controls usable

If session does not exist, fallback should show recovery navigation.

## `/logs` System Logs

Expected:
- Console header/counters
- Severity + node filters
- Monospaced log stream
- Empty/loading states that remain visible and explanatory
