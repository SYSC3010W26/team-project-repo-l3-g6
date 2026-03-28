import sqlite3
from database.init_db import create_tables
from database.crud import create_solve_session, create_solution, get_solutions_by_session
from database.models import SolveSessionCreate, SolutionCreate

def reproduce():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    create_tables(conn)
    
    session_id = create_solve_session(conn, SolveSessionCreate(selected_algorithm="Kociemba", status="solving"))
    solution_id = create_solution(conn, SolutionCreate(session_id=session_id, algorithm_used="Kociemba", move_count=20, solution_string="U R L D"))
    
    rows = get_solutions_by_session(conn, session_id)
    latest = rows[-1]
    
    print(f"Type of latest: {type(latest)}")
    try:
        val = latest.get("solution_string")
        print(f"Value: {val}")
    except AttributeError as e:
        print(f"CAUGHT: {e}")

if __name__ == "__main__":
    reproduce()
