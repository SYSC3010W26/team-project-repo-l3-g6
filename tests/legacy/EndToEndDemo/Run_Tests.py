"""
============================================================
SYSC 3010 - End-to-End Demo: Test Runner
Author: Luke Grundy
============================================================
"""
import threading
import time
import server_db

def start_db():
    """Starts the server database in a separate thread."""
    threading.Thread(target=server_db.start_server, daemon=True).start()

def wait_for_nodes(expected): 
    """ensures all nodes are cconnected before starting tests"""
    print("[TEST] Waiting for nodes...")
    while True:
        if all(node in server_db.clients for node in expected):
            print("[TEST] All nodes connected")
            return
        time.sleep(1)

def run_demo():
    """Runs through the general flow of the final system, does not test all edge cases (crash handling, etc)"""
    
    wait_for_nodes(["SCANNER", "SOLVER", "MOTOR"])

    # test scanner, final system will request a second scan from another pi to cover all angles, not implemented here for simplicity.
    print("[TEST] Running SCAN test")
    server_db.send_command("SCANNER", "SCAN")

    time.sleep(2)

    # test solver, final system will pull cube state from database, not implemented here for simplicity.
    print("[TEST] Running SOLVE test")
    server_db.send_command("SOLVER", "SOLVE", "CUBE_STATE_123")

    time.sleep(2)

    # test motor, final system will pull moves from database, not implemented here for simplicity.
    print("[TEST] Running EXECUTE test")
    server_db.send_command("MOTOR", "EXECUTE", "R U R' U'")

    time.sleep(2)

    # test crash, mostly used to demonstrate heartbeat timers and end the Pi stubs.
    print("[TEST] Running CRASH test")
    server_db.send_command("SOLVER", "CRASH")
    server_db.send_command("SCANNER", "CRASH")
    server_db.send_command("MOTOR", "CRASH")

    server_db.send_command("SOLVER", "SOLVE", "CUBE_STATE_123")  # should not get response as solver is "crashed"

    time.sleep(8) # wait for heartbeat timeouts

    print("[TEST] Demo complete")

def main():
    start_db()
    time.sleep(1)
    run_demo()

if __name__ == "__main__":
    main()


"""
python3 Scanner_Pi_Stub.py &
python3 Solver_Pi_Stub.py &
python3 Motor_Pi_Stub.py &
"""