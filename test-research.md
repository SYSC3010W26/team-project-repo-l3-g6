# S05 — Research

**Date:** 2026-03-30

## Summary

This slice is focused on hardening `start_node.sh` to ensure it gracefully handles backend unavailability and transient failures. Currently, `start_node.sh` performs a single, synchronous check for the central server using `curl` or `wget`. If the server is unreachable at startup, the script abruptly exits. Furthermore, the subprocesses for `scanner_bridge.py` and `solver_listener.py` are launched as fire-and-forget detached processes. If they crash due to fatal exceptions or transient network states, they are never restarted, and when the main node script is killed, they are left orphaned.

The core solution involves three targeted changes to `start_node.sh`. First, we will replace the `exit 1` in the initial server connectivity check with a resilient `while` loop that sleeps and retries until the server responds. Second, we will refactor the Python subprocess launch logic to execute within monitored daemon threads, ensuring that if a subsystem crashes, it automatically restarts after a 5-second backoff. Finally, we will register `SIGTERM` and `SIGINT` handlers in both the Bash trap and the Python script to cleanly terminate all child processes (including the camera stream and subsystems) during a manual shutdown.

## Recommendation

Implement resilient retry loops in both Bash (for initial connectivity) and Python (for subsystem process monitoring). 

The initial connection check is perfectly placed but too brittle; a `while ! curl ...` loop eliminates the race condition where node Pis boot faster than the database Pi. For the Python subsystems, placing the `subprocess.Popen` calls inside a `while True` loop within a thread provides naive but effective process supervision, ensuring nodes autonomously recover from unexpected crashes. A clean teardown mechanism is critical to prevent "address already in use" errors on subsequent runs.

## Implementation Landscape

### Key Files

- `start_node.sh` — The sole target for this slice. 
  - Change the `curl`/`wget` checks to retry loops instead of exiting.
  - Refactor the embedded Python script to track `Popen` objects in a list.
  - Wrap the `Popen` launch in a function with a `while True` loop (restarting on exit with a 5s delay).
  - Add `signal.signal` handlers in Python to `terminate()` child processes on shutdown.
  - Update the bash `cleanup()` function to explicitly `kill $CAMERA_PID` alongside `$NODE_PID`.

### Build Order

1. **Bash Connection Loop:** Replace the `curl` and `wget` `exit 1` logic with `while` loops. This is the simplest change and unblocks testing the node startup against an offline server.
2. **Bash Cleanup:** Add `kill $CAMERA_PID 2>/dev/null` to the `cleanup` function.
3. **Python Process Monitor:** Update the embedded Python script. Add the `run_subsystem` worker function, list tracking for processes, and signal handlers for clean teardown.

### Verification Approach

- **Server-down Startup:** Run `./start_node.sh` while the backend is offline. Verify it displays "Waiting for server..." and successfully connects and boots when `start_server.sh` is subsequently launched.
- **Mid-run Disconnect:** With the node running, kill the backend. Verify the heartbeat logs "Server unreachable - retrying...". Restart the backend and verify the heartbeat reconnects and logs silent successes (no warnings).
- **Process Supervision:** Manually `kill -9` the `scanner_bridge.py` or `solver_listener.py` PID. Verify `start_node.sh` logs the crash and restarts the process after 5 seconds.
- **Clean Teardown:** Press `Ctrl+C` to stop `start_node.sh`. Run `ps aux | grep python` and verify neither `scanner_bridge.py`, `solver_listener.py`, nor `stream_server.py` are left as orphaned processes.

## Common Pitfalls

- **Orphaned Subprocesses:** Python's daemon threads will exit immediately when the main thread ends, but they do *not* kill their active `subprocess.Popen` children. Explicit signal handling and `.terminate()` calls are strictly required.
- **Subshell PID Tracking:** The camera stream is launched with `&`. If we wrap it in a `while` loop subshell `( while true; do ... done ) &`, the PID assigned to `$!` will be the subshell, not the Python process. The bash `cleanup` trap might kill the subshell but leave the Python script running. Stick to a single unmonitored launch for the camera, or ensure the trap targets the entire process group.
