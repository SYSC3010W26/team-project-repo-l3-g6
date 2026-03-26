# Testing

## Framework

- **pytest** — primary test framework
- **OpenCV + NumPy** — used in scanner colour detection tests for synthetic image generation
- No test runner configuration file (no `pytest.ini`, `setup.cfg`, or `pyproject.toml`)

## Test Structure

```
UnitTests/
└── Scanner/
    ├── test_camera.py           # Camera capture tests (content unknown — likely hardware-dependent)
    ├── test_colour_detection.py # Colour classification unit tests (7 tests)
    └── README.md

solver/
└── Test_Cube_Debug_Viewer.py   # Solver debug viewer tests (not pytest-named)

motorctl/tests/
├── hardware_test.py            # Hardware integration test (empty stub — 1 line)
└── software_test.py            # Software unit test (empty stub — 1 line)

EndToEndDemo/
└── Run_Tests.py                # Integration demo / smoke test (not pytest)
```

## Test Coverage by Subsystem

### Scanner (UnitTests/Scanner/)
Best-covered subsystem. Uses synthetic image generation to test without real hardware.

**`test_colour_detection.py`** — 7 pytest tests:
- `test_classify_white()` — white pixel classification
- `test_classify_yellow()` — yellow pixel classification
- `test_classify_red()` — red pixel classification
- `test_classify_orange()` — orange pixel classification
- `test_classify_blue()` — blue pixel classification
- `test_classify_green()` — green pixel classification
- `test_scan_face_matches_known_pattern()` — end-to-end: synthetic 300x300 face image → 9-char colour string

Pattern: `COLOUR_PIXELS` dict maps colour letters to known-good BGR values; `make_face_image()` builds synthetic test images.

Run with:
```bash
cd UnitTests/Scanner
pytest test_colour_detection.py -v
```

### Solver (solver/)
`Test_Cube_Debug_Viewer.py` exists but is not named `test_*.py`, so pytest won't auto-discover it. Manual inspection required to assess coverage.

### Motor Control (motorctl/tests/)
Both test files are **empty stubs** (1 line each). No tests exist for:
- State machine transitions
- Socket.IO event handlers (`on_load`, `on_start`)
- Hardware health check logic
- Heartbeat behavior

### Integration / End-to-End (EndToEndDemo/)
`Run_Tests.py` is a manual demo orchestrator, not a pytest suite. Tests the happy path flow (SCAN → SOLVE → EXECUTE) with TCP stub nodes. Includes crash simulation and heartbeat timeout verification. Run manually:
```bash
python3 Scanner_Pi_Stub.py &
python3 Solver_Pi_Stub.py &
python3 Motor_Pi_Stub.py &
python3 Run_Tests.py
```

### Database
No tests found for `database/crud.py`, `database/db.py`, or ORM models.

## Mocking Strategy

- **Scanner tests**: use synthetic images (no mocking library) — real OpenCV pipeline on fake data
- **EndToEndDemo**: uses stub Pi classes that subclass `Base_Node.Node` and fake hardware responses
- **Motor tests**: N/A (empty)

## Coverage Gaps

| Area | Status |
|------|--------|
| Colour classification | Covered |
| Face scan pipeline | Covered |
| Camera capture | Unknown (hardware-dependent) |
| Cube state model | Not tested via pytest |
| Solver algorithm (CFOP) | Not tested via pytest |
| Motor state machine | Not tested |
| Socket.IO event handlers | Not tested |
| Database CRUD | Not tested |
| Server/API endpoints | Not tested |
| Error paths (bad cube state, hw failure) | Not tested |
