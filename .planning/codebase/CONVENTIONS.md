# Code Conventions

## Language & Runtime

- **Python 3.13** across all subsystems
- Async/await (`asyncio`) used in Motor Pi; synchronous in solver and demo nodes
- Virtual environment at `.venv/`; activate before development

## Code Style

### Naming

| Element | Convention | Example |
|---------|-----------|---------|
| Classes | PascalCase | `StateManager`, `AlgorithmSelector` |
| Functions (motor) | snake_case | `connect_to_server`, `wait_for_hardware` |
| Methods (solver) | camelCase | `loadState()`, `selectAlgorithm()`, `solve()` |
| Constants | UPPER_SNAKE_CASE | `NODE_ID`, `SERVER_URL`, `HEARTBEAT_INTERVAL` |
| Filenames (solver) | PascalCase with underscores | `Cube_State.py`, `CFOP_Algorithm.py` |
| Filenames (motor) | snake_case | `server_bridge.py`, `healthcheck.py` |
| Enum values | `"lower_with_underscores"` strings | `MotorState.WAITING_FOR_LIST` |

### File Headers

Every source file includes a comment block header:
```python
############################################
# MOTOR CONTROL SUBSYSTEM - Server Bridge
# Eric McFetridge SYSC3010:L3G6
############################################
```
or docstring:
```python
"""
SYSC3010 - Pi Cubed Rubik's Cube Solver
Solver Algorithm Pi - Top Level Solver Module
Group L3-G6
Author: Luke Grundy
"""
```

### Docstrings

Solver modules use one-liner docstrings on public methods:
```python
def loadState(self, stateString):
    """Load cube state from a 54-character string."""
```
Motor modules use inline comments instead of docstrings.

## Patterns

### State Machine Pattern (Motor Pi)

The motor Pi uses an explicit `MotorState` enum + `StateManager` class to track lifecycle:

```python
class MotorState(Enum):
    STARTUP = "startup"
    WAITING_FOR_LIST = "waiting_for_list"
    WAITING_FOR_START = "waiting_for_start"
    EXECUTING = "executing"

class StateManager:
    async def transition(self, new_state):
        self.state = new_state
        await sio.emit('node_state_update', {...})
```

State guards are checked before acting on socket events:
```python
@sio.on('load_moves')
async def on_load(data):
    if manager.state == MotorState.WAITING_FOR_LIST:
        ...
```

### Strategy Pattern (Solver)

Algorithm selection is delegated to `AlgorithmSelector`:
```python
self.selector = AlgorithmSelector(self.cube.state, "CFOP")
self.algorithm = self.selector.get_algorithm()
```

### Base Node Pattern (EndToEndDemo)

TCP nodes subclass `Base_Node.Node` and override `handle_command()`:
```python
class Node:
    def register(self): ...
    def heartbeat_loop(self): ...
    def listen(self): ...
    def handle_command(self, command, data): pass  # override in subclass
    def respond(self, data): ...
```

### Environment Configuration

All runtime config is loaded from `.env` via `python-dotenv`:
```python
from dotenv import load_dotenv
load_dotenv()
NODE_ID = os.getenv("NODE_ID")
SERVER_URL = os.getenv("SERVER_URL")
```

## Error Handling

- **Solver**: raises `ValueError` for invalid cube state length; raises `Exception` if no algorithm selected
- **Motor main**: exits with `sys.exit(1)` on hardware health check failure
- **EndToEndDemo**: breaks listen loop on empty recv (`if not data: break`); no explicit exception handling on socket errors
- **Colour detection**: returns `"?"` for unclassified pixels (soft failure)
- **General**: minimal try/except usage; most error paths are guard clauses rather than exception handling

## Message Protocol

### Socket.IO (production motor Pi)
JSON objects with `node_id` field:
```python
{'node_id': NODE_ID, 'state': 'executing'}
{'node_id': NODE_ID, 'success': True, 'move_count': 12}
```

### TCP/JSON (EndToEndDemo)
```python
{"type": "REGISTER", "node": "SCANNER"}
{"type": "HEARTBEAT", "node": "MOTOR"}
{"type": "COMMAND", "command": "SCAN", "data": None}
{"type": "RESPONSE", "node": "SOLVER", "data": {...}}
```

## Import Style

Standard library imports before third-party:
```python
import os
import asyncio
import socketio
from dotenv import load_dotenv
from actuator import execute_move_sequence
```

Local imports use bare module names (no relative imports), relying on `sys.path` or working directory.
