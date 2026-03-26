# Codebase Structure

## Directory Layout

```
team-project-repo-l3-g6/
├── database/                    # SQLite database layer (server-side)
│   ├── __init__.py
│   ├── crud.py                  # CRUD operations
│   ├── db.py                    # DB connection / session management
│   ├── init_db.py               # Schema initialization
│   ├── models.py                # ORM models
│   └── schema.sql               # Raw SQL schema
│
├── solver/                      # Rubik's Cube solving algorithms (Solver Pi)
│   ├── Solver.py                # Top-level solver entrypoint
│   ├── Cube_State.py            # Cube state representation (54-char string)
│   ├── Cube_Algorithm.py        # Base algorithm interface
│   ├── Algorithm_Selector.py    # Strategy selector (e.g., CFOP)
│   ├── Permutation_Table.py     # Move permutation tables
│   ├── Cube_Debug_Viewer.py     # Debug visualizer
│   ├── Test_Cube_Debug_Viewer.py
│   └── CFOP/
│       ├── __init__.py
│       ├── CFOP_Algorithm.py    # CFOP method implementation
│       └── CFOP_Tables.py       # CFOP lookup tables
│
├── motorctl/                    # Motor control subsystem (Motor Pi)
│   ├── src/
│   │   ├── main.py              # Async entry point; health check + gather
│   │   ├── server_bridge.py     # Socket.IO client + state machine (primary)
│   │   ├── actuator.py          # Duplicate server_bridge (see CONCERNS.md)
│   │   ├── healthcheck.py       # Klipper/SKR hardware readiness check
│   │   ├── heartbeat.py         # Periodic heartbeat emitter
│   │   └── __init__.py
│   └── tests/
│       ├── hardware_test.py     # Hardware integration test (stub)
│       └── software_test.py     # Software unit test (stub)
│
├── EndToEndDemo/                # Integration demo (raw TCP sockets)
│   ├── Base_Node.py             # Base TCP node (register, heartbeat, listen)
│   ├── Motor_Pi_Stub.py         # Motor node stub
│   ├── Scanner_Pi_Stub.py       # Scanner node stub
│   ├── Solver_Pi_Stub.py        # Solver node stub
│   ├── server_db.py             # Demo TCP server + DB integration
│   └── Run_Tests.py             # Demo orchestrator / test runner
│
├── UnitTests/
│   └── Scanner/
│       ├── test_camera.py       # Camera capture tests
│       ├── test_colour_detection.py  # Colour classification tests (pytest)
│       └── README.md
│
├── docs/                        # Documentation
│   ├── README.md
│   ├── Sequence_diagram.puml    # PlantUML sequence diagram
│   ├── motor_control/README.md
│   ├── scanner/SCANNER.md
│   └── server/DATABASE.md
│
├── models/                      # 3D printable STL files for physical robot
│   ├── Base.stl
│   ├── cubeSolverFull.stl
│   ├── FaceTurner.stl
│   ├── HalfAssembled.stl
│   ├── Pillar.stl
│   └── TopCover.stl
│
├── screenshots/                 # Architecture diagrams / design images
│   ├── General_Sequence_Diagram.png
│   └── pi_cubed_design.png
│
├── WeeklyUpdates/               # Per-member weekly status reports (Weeks 3-10)
│
├── .venv/                       # Python virtual environment (Python 3.13)
├── requirements.txt             # Python dependencies
├── setup_dev.sh                 # Dev environment setup script
├── .env                         # Environment variables (NODE_ID, SERVER_URL)
├── rubiks_dev.db                # SQLite development database
└── README.md
```

## Key Locations

| Purpose | Path |
|---------|------|
| Motor Pi entry point | `motorctl/src/main.py` |
| Motor state machine | `motorctl/src/server_bridge.py` |
| Solver entry point | `solver/Solver.py` |
| Cube state model | `solver/Cube_State.py` |
| Algorithm selection | `solver/Algorithm_Selector.py` |
| CFOP implementation | `solver/CFOP/CFOP_Algorithm.py` |
| Database models | `database/models.py` |
| Database CRUD | `database/crud.py` |
| DB schema | `database/schema.sql` |
| Integration demo | `EndToEndDemo/Run_Tests.py` |
| Scanner colour tests | `UnitTests/Scanner/test_colour_detection.py` |
| Environment config | `.env` |
| Dependencies | `requirements.txt` |

## Naming Conventions

- **Python modules (solver/)**: PascalCase filenames (`Cube_State.py`, `Algorithm_Selector.py`)
- **Python modules (motorctl/)**: snake_case filenames (`server_bridge.py`, `healthcheck.py`)
- **Classes**: PascalCase (`StateManager`, `AlgorithmSelector`, `Cube`)
- **Functions/methods**: camelCase in solver (`loadState`, `selectAlgorithm`), snake_case in motor (`connect_to_server`)
- **Test files**: `test_*.py` (pytest-discoverable)
- **Demo stubs**: `*_Pi_Stub.py` (Pascal with suffix)
- **Constants**: UPPER_SNAKE_CASE (`NODE_ID`, `SERVER_URL`, `HEARTBEAT_INTERVAL`)

## Subsystem Boundaries

Each Pi subsystem (Scanner, Solver, Motor) is physically separate and communicates exclusively through the Control Server. There are no direct Pi-to-Pi connections. The `EndToEndDemo/` directory is a self-contained TCP-based prototype; the production Motor Pi uses Socket.IO via `motorctl/`.
