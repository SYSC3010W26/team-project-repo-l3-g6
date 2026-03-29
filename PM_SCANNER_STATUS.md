# PM Report: Basil's Scanner Pi Status

**Date:** 2026-03-29  
**Status:** ⚠️ INCOMPLETE — Not blocking production but needs work

---

## What Exists ✅

1. **Colour Detection Tests** (UnitTests/Scanner/)
   - `test_colour_detection.py` — Tests colour classification algorithm
   - `test_camera.py` — Basic camera tests
   - Colour ranges defined for all 6 cube faces (W, Y, R, O, B, G)
   - ~1800 lines of test code

2. **Backend Integration** (backend/routers/scan.py)
   - POST /scan/submit endpoint — accepts cube state from scanner
   - GET /scan/{session_id} — retrieves scan results
   - Database persistence (cube_states table)
   - All CRUD operations working

3. **E2E Demo Stub** (EndToEndDemo/Scanner_Pi_Stub.py)
   - Simulates scanner for testing
   - Returns dummy cube state

---

## What's MISSING ❌

**NO actual production Scanner Pi code exists:**
- ❌ No `scannerctl/` directory (unlike motorctl/ and solver/)
- ❌ No camera capture implementation
- ❌ No face scanning pipeline
- ❌ No state validation logic
- ❌ No integration with actual Pi camera
- ❌ No tests for production code (only unit tests)
- ❌ No heartbeat/health check for scanner node

---

## Requirements Status

From PROJECT.md:
```
[ ] **Scanner integration** — Full camera capture pipeline connected to DB: 
    scan both faces, validate cube state, write to `cube_states` table 
    with confidence flag
```

**Status:** ⏳ NOT STARTED — Basil has only tests, no implementation

---

## What Needs to Be Done

### Critical (Blocking Production)
1. **Create scannerctl/ directory structure** (mirroring motorctl/)
   ```
   scannerctl/
   ├── src/
   │   ├── __init__.py
   │   ├── main.py (scanner startup)
   │   ├── camera.py (capture from Pi camera)
   │   ├── colour_detection.py (classify pixels)
   │   ├── cube_scanner.py (scan all 6 faces)
   │   ├── server_bridge.py (HTTP POST to backend)
   │   └── heartbeat.py (emit to backend)
   ├── tests/
   │   ├── test_camera.py (move from UnitTests)
   │   └── test_colour_detection.py (move from UnitTests)
   └── SCANNER.md (implementation guide)
   ```

2. **Implement camera.py** — Capture frames from Pi camera
   ```python
   # Pseudocode
   import cv2
   cap = cv2.VideoCapture(0)  # or CSI camera
   ret, frame = cap.read()
   # Return frame or None on error
   ```

3. **Implement cube_scanner.py** — Scan and validate all 6 faces
   ```python
   # Pseudocode
   def scan_all_faces():
       faces = {}
       for face in ['U', 'R', 'F', 'D', 'L', 'B']:
           frame = capture_face(face)
           state = classify_colours(frame)
           faces[face] = state
       
       cube_state = assemble_54_char_string(faces)
       is_valid = validate_cube_state(cube_state)
       return cube_state, is_valid, confidence
   ```

4. **Integrate with backend** — POST to /scan/submit
   ```python
   # Call backend API
   response = requests.post(
       'http://backend-pi:8000/scan/submit',
       json={
           'session_id': session_id,
           'state_string': cube_state,
           'is_valid': is_valid,
           'confidence': 0.95
       }
   )
   ```

### Important (Nice to Have)
- Heartbeat emission to /nodes/heartbeat
- Error handling for camera not available
- Retry logic for failed scans
- Lighting/quality diagnostics
- Verification re-scan after motor execution

---

## Estimate

| Task | Estimate | Notes |
|------|----------|-------|
| Camera capture | 1-2 hours | Depends on Pi camera setup |
| Face scanning logic | 2-3 hours | Iterate over faces, validate |
| Backend integration | 0.5 hours | Use existing /scan/submit |
| Testing & tuning | 2-3 hours | Lighting, accuracy, edge cases |
| **TOTAL** | **5-8 hours** | |

---

## Current Blocker Status

**Does this block M004 production release?** ⚠️ **PARTIALLY**

- ✅ Backend API ready to accept scans
- ✅ Database schema ready
- ✅ Colour detection algorithm ready
- ❌ No actual camera code to provide scans
- ⚠️ Can use mock data for testing (simulator works)

**Workaround for now:**
- Use `simulate_demo.py` which has a mock scanner
- For hardware testing, connect Pi camera and implement scannerctl/

---

## Recommendation for PM

### Option A: Complete M004 without Scanner
✅ **Current approach:**
- Motor control ✅ DONE
- Solver integration ✅ DONE
- Backend ready ✅ DONE
- Web dashboard ✅ DONE
- Database ✅ DONE
- Scanner Pi: Can test with simulator, implement hardware after

**Pros:**
- Release software now, hardware validation can happen in parallel
- Basil has clear implementation spec from backend
- No blockers to other subsystems

**Cons:**
- Physical robot can't scan without scanner code

### Option B: Hold M004 for Scanner Implementation
❌ **Wait for Basil:**
- Basil implements scannerctl/ (5-8 hours)
- Run full hardware test together
- Then release

**Pros:**
- Everything done at once
- One end-to-end validation

**Cons:**
- Delays release of motor + solver + backend work
- Other subsystems waiting

---

## Status Summary for Basil

**What to do:**
1. Create `scannerctl/src/` directory structure
2. Implement camera capture (`camera.py`)
3. Implement face scanner (`cube_scanner.py`)
4. Integrate with POST /scan/submit
5. Add heartbeat emission
6. Run tests and tune

**Reference implementations:**
- `motorctl/src/main.py` — startup pattern
- `motorctl/src/server_bridge.py` — heartbeat pattern
- `UnitTests/Scanner/test_colour_detection.py` — colour logic (already written!)
- `backend/routers/scan.py` — API contract

**Timeline:** 5-8 hours for full implementation

---

## PM Action Items

- [ ] Decide: Complete M004 now (with simulated scanner) or wait for Basil
- [ ] Notify Basil of his implementation spec
- [ ] Assign him the 5-8 hour implementation
- [ ] Schedule hardware integration testing with camera present

---

*PM Report: Scanner Pi Status*  
*Generated: 2026-03-29*  
*Owner: Basil Thotapilly (Scanner Pi)*
