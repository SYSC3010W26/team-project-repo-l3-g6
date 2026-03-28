# PI³ Demo Day Troubleshooting

## Symptom: old frontend still showing

**Cause:** stale Vite process or browser cache.

**Fix:**
1. Check active frontend servers:
   ```bash
   lsof -i :4173
   lsof -i :5173
   ```
2. Kill stale PIDs.
3. Restart frontend on `4173`.
4. Hard refresh browser (`Cmd+Shift+R`).

---

## Symptom: cube shows only 1-2 colors / stripe-like pattern

**Cause:** no valid cube-state payload (54 stickers) arriving yet.

**Fix:**
1. Verify scanner/simulation feed is posting cube state.
2. Verify backend endpoint receives and stores state.
3. Check React Query data for cube/session payload shape.

---

## Symptom: Solution Review page says session not found / buttons useless

**Cause:** no solved session with steps in DB, or backend unreachable.

**Fix:**
1. Confirm `/results` has sessions.
2. Open a known `sessionId` route from results click-through.
3. Verify solution-step feed has run and persisted.

---

## Symptom: logs page empty

**Cause:** no incoming logs, wrong filters, or backend connectivity issue.

**Fix:**
1. Set severity = all, node = all.
2. Confirm simulation/hardware is emitting logs.
3. Confirm React Query `logs` query status and last update time.

---

## Symptom: UI loads but controls/state never change

**Cause:** frontend up, backend/simulation down or disconnected.

**Fix:**
1. Check backend terminal for request activity.
2. Check React Query statuses (`success` vs `error`).
3. Restart simulation feeders.

---

## React Query Devtools: how to use in real time

Use this panel as your "is data alive?" meter:

- `status: success` => endpoint responding.
- `status: error` => API/network problem.
- `updatedAt` moving forward => polling is alive.
- data object changing while simulation runs => end-to-end flow is functioning.

If queries are healthy but UI still wrong, issue is likely rendering/state mapping. If queries are failing, issue is backend/network first.
