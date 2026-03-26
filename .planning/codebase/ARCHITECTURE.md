# Architecture

**Analysis Date:** 2026-03-24

## Pattern Overview

**Overall:** Distributed Microservices with Centralized Control Server

**Key Characteristics:**
- Four Raspberry Pi nodes (Control Server, Scanner, Solver, Motor) communicating via a central server
- Asynchronous request-response pattern with heartbeat monitoring
- Persistent state tracked in centralized SQLite/PostgreSQL database
- Pipeline architecture: Scanner → Solver → Motor execution
- Socket-based communication (both synchronous sockets in demo and SocketIO in production)

## Layers

**Control Server Layer (Saim Hashmi):**
- Purpose: Central hub for all system coordination, database management, GUI operations, and node orchestration
- Location: `database/` module + `EndToEndDemo/server_db.py`
- Contains: SQLite/PostgreSQL connection management, CRUD operations, Pydantic models, system state tracking
- Depends on: Socket communication, database drivers (sqlite3/psycopg2), dotenv for config
- Used by: All three edge nodes (Scanner, Solver, Motor), GUI frontend

**Scanner Node Layer (Basil Thotapilly):**
- Purpose: Optical cube recognition and state capture via camera modules
- Location: Implied in project structure; implementation in `EndToEndDemo/Scanner_Pi_Stub.py`
- Contains: Camera capture logic, face recognition algorithms, state serialization
- Depends on: Server communication layer, optical libraries (not shown in codebase)
- Used by: Control Server to get initial cube state

**Solver Node Layer (Luke Grundy):**
- Purpose: Algorithm-based cube solving using state permutations
- Location: `solver/` module
- Contains: Cube state representation, move algorithms (CFOP selector, permutation tables), solution generation
- Depends on: Cube state models, permutation tables, no external frameworks
- Used by: Control Server to generate move sequences

**Motor Control Layer (Eric McFetridge):**
- Purpose: Physical actuation via TMC2209 stepper drivers and SKR v1.4 control board
- Location: `motorctl/src/` module
- Contains: Hardware health checks, move sequence execution, SocketIO client bridge, state machine
- Depends on: Asyncio, SocketIO client, Klipper firmware (SKR v1.4), .env configuration
- Used by: Control Server sends move lists and execution commands

## Data Flow

**Solve Session Pipeline:**

1. **User Initiates Scan** (GUI → Server)
   - User presses "BEGIN SCAN" in GUI
   - Server sends SCAN command to Scanner node via socket

2. **Scanner Captures State** (Scanner → Server)
   - Scanner node receives SCAN command via `Base_Node.handle_command()`
   - Captures all 6 cube faces using camera modules
   - Generates 54-character cube state string
   - Responds with cube state back to server
   - Server stores scan results in `cube_states` and `scan_faces` tables

3. **Solver Generates Solution** (Server → Solver)
   - Server sends SOLVE command with cube state string to Solver node
   - Solver node parses state string using `Cube_State.string_to_cube()`
   - Loads state into Cube object via `Solver.loadState(stateString)`
   - Algorithm selector picks CFOP or alternative via `Algorithm_Selector`
   - Generates move sequence (e.g., "R U R' U'")
   - Returns solution string to server
   - Server stores solution in `solutions` and `solution_steps` tables

4. **Motor Executes Moves** (Server → Motor)
   - Server sends move list via `load_moves` event to Motor node
   - Motor node buffered moves in `StateManager.move_buffer`
   - Server sends `start_solve` signal
   - Motor node transitions through states: STARTUP → WAITING_FOR_LIST → WAITING_FOR_START → EXECUTING
   - Motor sends each move to SKR v1.4 control board
   - Control board interfaces with TMC2209 drivers for stepper motors
   - Each motor rotates at 24v 1.4A peak current
   - Motor node reports completion to server via `execution_complete` event
   - Server logs execution in `execution_runs` and `motor_execution_log` tables

5. **Post-Solve Verification** (Optional)
   - Scanner can re-scan solved cube to verify success
   - Results stored in `verification_results` table

**State Management:**
- Session state tracked in `solve_sessions` table (states: pending → scanning → solving → executing → completed/failed)
- Node health tracked in `node_status` table with heartbeat timestamps
- All events logged in `system_logs` for debugging and audit trail

## Key Abstractions

**Cube State Representation:**
- Purpose: Standardized 54-character string encoding cube configuration
- Examples: `solver/Cube_State.py`, `database/models.py` CubeState
- Pattern: 6 faces × 9 positions each = 54 facelets. Centers (indices 4,13,22,31,40,49) never change.
  - U: 0-8, R: 9-17, F: 18-26, D: 27-35, L: 36-44, B: 45-53

**Node Communication Protocol:**
- Purpose: Standardized JSON message format for inter-node and node-to-server communication
- Examples: `EndToEndDemo/Base_Node.py`, `motorctl/src/server_bridge.py`
- Pattern: All messages contain `type` field (REGISTER, HEARTBEAT, COMMAND, RESPONSE, load_moves, start_solve)
- Message routing: Server → Node via socket/SocketIO, Node → Server via socket.send()

**Solve Session State Machine:**
- Purpose: Track progress through scan-solve-execute pipeline
- Examples: `motorctl/src/server_bridge.py` MotorState enum
- Pattern: Each node has defined states; server orchestrates transitions and monitors timeouts

**CRUD Operations Layer:**
- Purpose: Abstraction over database for consistent data access
- Examples: `database/crud.py` (create_solve_session, update_solve_session_status, etc.)
- Pattern: All CRUD functions accept open sqlite3.Connection for transaction scope management

## Entry Points

**Demo/Test Server (Socket-based):**
- Location: `EndToEndDemo/server_db.py`
- Triggers: `python EndToEndDemo/server_db.py`
- Responsibilities: Listen for node connections on port 5000, dispatch REGISTER/HEARTBEAT/RESPONSE messages, monitor heartbeat timeouts
- Used for: Integration testing with socket-based node stubs

**Motor Control Node (AsyncIO/SocketIO-based):**
- Location: `motorctl/src/main.py`
- Triggers: `python motorctl/src/main.py`
- Responsibilities: Hardware health check via Klipper, connect to server via SocketIO, manage move buffering, execute motor commands
- Dependencies: NODE_ID, SERVER_URL from `.env`, Klipper firmware on SKR v1.4

**Database Initialization:**
- Location: `database/init_db.py`
- Triggers: `python database/init_db.py`
- Responsibilities: Create schema from `database/schema.sql`, seed default admin user
- Environment: DATABASE_URL env var (defaults to ./rubiks.db)

**Scanner Node Stub (Demo):**
- Location: `EndToEndDemo/Scanner_Pi_Stub.py`
- Triggers: `python EndToEndDemo/Scanner_Pi_Stub.py`
- Responsibilities: Connect to demo server, respond to SCAN commands with dummy state, support CRASH simulation

**Solver Node Stub (Demo):**
- Location: `EndToEndDemo/Solver_Pi_Stub.py`
- Triggers: `python EndToEndDemo/Solver_Pi_Stub.py`
- Responsibilities: Connect to demo server, respond to SOLVE commands with dummy moves, support CRASH simulation

## Error Handling

**Strategy:** Distributed error recovery with centralized monitoring

**Patterns:**
- **Heartbeat Timeout Detection:** Server monitors `node_status.last_heartbeat`. If node misses 5+ seconds of heartbeats, server marks node as DOWN and gracefully pauses operations (watchdog behavior)
- **Network Failure Recovery:** Socket-based nodes attempt reconnection on connection loss; SocketIO-based Motor node relies on SocketIO client reconnection semantics
- **Database Transaction Rollback:** All CRUD operations wrapped in `db_session()` context manager that commits on success, rolls back on exception
- **Hardware Health Check:** Motor node calls `wait_for_hardware()` before starting; fails hard if Klipper/SKR v1.4 not responding (prevents zombie states)
- **Validation:** Cube state validation via `Cube.is_solved()` check; move string parsing with exception on invalid moves

## Cross-Cutting Concerns

**Logging:**
- Centralized via `system_logs` table in database. Each node logs events with `level` (INFO/WARNING/ERROR), `event_type`, message, and optional metadata
- Demo nodes print to console with prefix (e.g., "[DB]", "[Scanner]")
- Motor control uses print statements (could be enhanced with logging module)

**Validation:**
- Pydantic v2 models in `database/models.py` validate all API payloads (UserCreate, CubeStateCreate, SolutionCreate, etc.)
- Cube state validation: length check (54 chars), face integrity check via `Cube.is_solved()`
- Move notation validation in `solver/Permutation_Table.py` MOVES dictionary

**Authentication:**
- User table tracks operators; `role` field controls access (e.g., "admin")
- No explicit authentication layer shown; assumes server-side access control checks user_id before operations
- Production may layer FastAPI dependency injection here

**Node Coordination:**
- Server-centric orchestration: All commands originate from server, all responses route through server
- Heartbeat-based liveness detection prevents phantom nodes from blocking operations
- State transitions in Motor node managed via StateManager to prevent command out-of-order errors

---

*Architecture analysis: 2026-03-24*
