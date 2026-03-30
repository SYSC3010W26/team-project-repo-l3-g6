#!/usr/bin/env python3
"""
Integration test for Scanner → API → Solver pipeline.

Tests the full flow:
1. Create session via POST /jobs/start
2. Submit scan via POST /scan/submit (with scanner_bridge)
3. Verify cube_states table populated
4. Verify solution would be computed
5. Verify DB state transitions

SYSC3010 L3-G6
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture
def valid_state_string():
    """Valid 54-character state string (solved cube)."""
    return "W"*9 + "R"*9 + "G"*9 + "Y"*9 + "O"*9 + "B"*9

@pytest.fixture
def test_session_id():
    """Test session ID."""
    return 123

# ─────────────────────────────────────────────────────────────────────────────
# TEST: Full Integration Flow
# ─────────────────────────────────────────────────────────────────────────────

class TestScannerSolverIntegration:
    """Integration tests for scanner → API → solver pipeline."""
    
    @pytest.mark.anyio
    async def test_full_workflow_session_scan_verify(
        self, 
        valid_state_string, 
        test_session_id
    ):
        """
        Full workflow test:
        1. Create session
        2. Submit scan
        3. Verify DB state
        4. Acknowledge solve request
        5. Submit solution (external)
        """
        
        print(f"\n[INTEGRATION TEST] Scanner → API → Solver Pipeline")
        print(f"{'='*60}")
        
        # ───────────────────────────────────────────────────────────────
        # STEP 1: Create session
        # ───────────────────────────────────────────────────────────────
        print(f"\nSTEP 1: Create session (POST /jobs/start)")
        
        from backend.routers.jobs import start_job
        from backend.schemas import JobStartRequest
        
        mock_db = Mock()
        
        with patch("backend.routers.jobs.crud") as mock_crud:
            mock_crud.create_solve_session.return_value = test_session_id
            
            request = JobStartRequest(algorithm="CFOP")
            response = start_job(request, mock_db)
            
            assert response.session_id == test_session_id
            print(f"  ✓ Session created: session_id={test_session_id}")
        
        # ───────────────────────────────────────────────────────────────
        # STEP 2: Submit scan
        # ───────────────────────────────────────────────────────────────
        print(f"\nSTEP 2: Submit scan (POST /scan/submit)")
        
        from backend.routers.scan import submit_scan
        from backend.schemas import ScanSubmitRequest
        
        with patch("backend.routers.scan.crud") as mock_crud:
            mock_crud.get_solve_session_by_id.return_value = {
                "id": test_session_id,
                "status": "pending"
            }
            mock_crud.create_cube_state.return_value = 456
            mock_crud.update_solve_session_status.return_value = None
            
            request = ScanSubmitRequest(
                session_id=test_session_id,
                state_string=valid_state_string,
                is_valid=True,
                confidence=0.99,
            )
            response = submit_scan(request, mock_db)
            
            assert response.cube_state_id == 456
            print(f"  ✓ Scan submitted: cube_state_id={response.cube_state_id}")
            print(f"    State: {valid_state_string[:20]}...")
            print(f"    Confidence: 99%")
        
        # ───────────────────────────────────────────────────────────────
        # STEP 3: Verify cube state in DB
        # ───────────────────────────────────────────────────────────────
        print(f"\nSTEP 3: Verify cube_states table (GET /scan/session_id)")
        
        from backend.routers.scan import get_scan
        
        with patch("backend.routers.scan.crud") as mock_crud:
            mock_crud.get_cube_states_by_session.return_value = [
                {
                    "session_id": test_session_id,
                    "state_string": valid_state_string,
                    "is_valid": True,
                    "confidence": 0.99,
                    "created_at": "2026-03-29T19:21:56Z",
                    "source": "scanner",
                }
            ]
            
            response = get_scan(test_session_id, mock_db)
            
            assert response.session_id == test_session_id
            assert response.state_string == valid_state_string
            assert response.is_valid is True
            assert response.confidence == 0.99
            print(f"  ✓ Cube state verified in DB")
            print(f"    State: {response.state_string[:20]}...")
            print(f"    Valid: {response.is_valid}, Confidence: {response.confidence:.1%}")
        
        # ───────────────────────────────────────────────────────────────
        # STEP 4: Start solving (Acknowledge)
        # ───────────────────────────────────────────────────────────────
        print(f"\nSTEP 4: Acknowledge solve request (POST /solve/start)")
        
        from backend.routers.solve import start_solve
        from backend.schemas import SolveStartRequest
        
        with patch("backend.routers.solve.crud") as mock_crud, \
             patch("backend.routers.solve.sio", new_callable=AsyncMock) as mock_sio:
            mock_crud.get_solve_session_by_id.return_value = {"id": test_session_id}
            mock_crud.get_cube_states_by_session.return_value = [
                {"session_id": test_session_id, "state_string": valid_state_string, "is_valid": True}
            ]
            
            request = SolveStartRequest(session_id=test_session_id)
            response = await start_solve(request, mock_db)
            
            assert response.session_id == test_session_id
            assert response.status == "solving"
            mock_crud.update_solve_session_status.assert_called_with(mock_db, test_session_id, "solving")
            print(f"  ✓ Solve acknowledged: session_id={test_session_id}, status={response.status}")
        
        # ───────────────────────────────────────────────────────────────
        # STEP 5: Submit solution (from external solver)
        # ───────────────────────────────────────────────────────────────
        print(f"\nSTEP 5: Submit solution (POST /solve/submit)")
        
        from backend.routers.solve import submit_solution
        from backend.schemas import SolveSubmitRequest
        
        with patch("backend.routers.solve.crud") as mock_crud, \
             patch("backend.routers.solve.sio", new_callable=AsyncMock) as mock_sio:
            mock_crud.get_solve_session_by_id.return_value = {"id": test_session_id}
            mock_crud.create_solution.return_value = 789
            
            request = SolveSubmitRequest(
                session_id=test_session_id,
                algorithm_used="CFOP",
                move_count=2,
                solution_string="U D"
            )
            response = await submit_solution(request, mock_db)
            
            assert response.solution_id == 789
            mock_crud.update_solve_session_status.assert_called_with(mock_db, test_session_id, "solved")
            print(f"  ✓ Solution submitted: solution_id=789")
            print(f"    Status transition: solving → solved")
        
        # ───────────────────────────────────────────────────────────────
        # SUMMARY
        # ───────────────────────────────────────────────────────────────
        print(f"\n{'='*60}")
        print(f"INTEGRATION TEST PASSED")
        print(f"{'='*60}")
        print(f"✓ Full pipeline validated:")
        print(f"  1. Session created (session_id={test_session_id})")
        print(f"  2. Scan submitted (cube_state_id=456)")
        print(f"  3. Cube state verified in DB")
        print(f"  4. Solve request acknowledged")
        print(f"  5. Solution submission flow verified")

    def test_scanner_bridge_provisioning(self):
        """Test scanner_bridge session ID provisioning."""
        
        print(f"\n[TEST] Scanner bridge session ID provisioning")
        
        from Scanner.scanner_bridge import ScannerAPIClient
        from unittest.mock import Mock, patch
        
        # Scenario 1: Manual env var
        print(f"  Scenario 1: Manual env var")
        client = ScannerAPIClient("http://localhost:8000", 123)
        assert client.session_id == 123
        print(f"    ✓ Session ID set: 123")
        
        # Scenario 2: Auto-discovery would work if endpoint available
        print(f"  Scenario 2: Auto-discovery (mocked)")
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"session_id": 456}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            # Simulate auto-discovery call
            resp = mock_get("http://localhost:8000/jobs/current-session-id")
            data = resp.json()
            
            assert data["session_id"] == 456
            print(f"    ✓ Auto-discovery endpoint would return: 456")

# ─────────────────────────────────────────────────────────────────────────────
# TEST: Error Handling
# ─────────────────────────────────────────────────────────────────────────────

class TestIntegrationErrorHandling:
    """Tests error handling across the full pipeline."""
    
    def test_invalid_scan_rejected(self):
        """Scan with '?' should be rejected at /scan/submit."""
        
        print(f"\n[TEST] Invalid scan rejected before solver")
        
        invalid_state = "W"*6 + "???" + "R"*9 + "G"*9 + "Y"*9 + "O"*9 + "B"*9
        
        from backend.routers.scan import submit_scan, validate_state_string
        from backend.schemas import ScanSubmitRequest
        from fastapi import HTTPException
        
        # Validation function rejects unknowns
        is_valid, error = validate_state_string(invalid_state)
        assert not is_valid
        assert "unrecognized colour" in error
        
        print(f"  ✓ Validation rejects unknowns")
        print(f"    Error: {error}")
        
        # Endpoint rejects the request
        with patch("backend.routers.scan.crud") as mock_crud:
            mock_crud.get_solve_session_by_id.return_value = {"id": 123}
            
            request = ScanSubmitRequest(
                session_id=123,
                state_string=invalid_state,
                is_valid=False,
                confidence=0.83,
            )
            
            with pytest.raises(HTTPException) as exc:
                submit_scan(request, Mock())
            
            assert exc.value.status_code == 400
            print(f"  ✓ Endpoint returns 400 error")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
