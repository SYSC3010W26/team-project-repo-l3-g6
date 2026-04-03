#!/usr/bin/env python3
"""
Tests for backend/routers/scan.py validation and endpoints.

SYSC3010 L3-G6
"""

import pytest
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch

# Import modules under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.routers.scan import validate_state_string


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: validate_state_string
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateStateString:
    """Tests for state string validation function."""
    
    def test_valid_state_string(self):
        """Valid state string: 54 chars, all recognized colours."""
        # 6 faces × 9 stickers = 54 total, each face one colour
        state = "W"*9 + "R"*9 + "G"*9 + "Y"*9 + "O"*9 + "B"*9
        
        is_valid, error = validate_state_string(state)
        
        assert is_valid is True
        assert error == ""
    
    def test_valid_state_string_mixed_colours(self):
        """Valid state string with mixed colours (realistic)."""
        state = "WYRGOBWYRGOBWYRGOBWYRGOBWYRGOBWYRGOBWYRGOBWYRGOBWYRGOB"
        
        is_valid, error = validate_state_string(state)
        
        assert is_valid is True
        assert error == ""
    
    def test_invalid_state_string_with_unknowns(self):
        """Invalid: contains '?' (unrecognized colours)."""
        state = "W"*6 + "???" + "R"*9 + "G"*9 + "Y"*9 + "O"*9 + "B"*9
        
        is_valid, error = validate_state_string(state)
        
        assert is_valid is False
        assert "unrecognized colour" in error
        assert "3" in error  # Should mention count
    
    def test_invalid_state_string_single_unknown(self):
        """Invalid: single '?' in state string."""
        state = "W"*9 + "R"*9 + "G"*9 + "Y"*9 + "O"*9 + "B"*8 + "?"
        
        is_valid, error = validate_state_string(state)
        
        assert is_valid is False
        assert "unrecognized colour" in error
        assert "1" in error
    
    def test_invalid_state_string_wrong_length_short(self):
        """Invalid: state string too short (52 chars instead of 54)."""
        state = "W"*9 + "R"*9 + "G"*9 + "Y"*9 + "O"*9 + "B"*7  # 52 total
        
        is_valid, error = validate_state_string(state)
        
        assert is_valid is False
        assert "54 characters" in error
        assert "52" in error
    
    def test_invalid_state_string_wrong_length_long(self):
        """Invalid: state string too long (56 chars instead of 54)."""
        state = "W"*9 + "R"*9 + "G"*9 + "Y"*9 + "O"*9 + "B"*9 + "WR"  # 56 total
        
        is_valid, error = validate_state_string(state)
        
        assert is_valid is False
        assert "54 characters" in error
        assert "56" in error
    
    def test_invalid_state_string_invalid_colour(self):
        """Invalid: contains invalid colour letter."""
        state = "W"*9 + "R"*9 + "G"*9 + "Y"*9 + "O"*9 + "X"*9  # X is invalid
        
        is_valid, error = validate_state_string(state)
        
        assert is_valid is False
        assert "invalid colour" in error
        assert "X" in error
    
    def test_invalid_state_string_invalid_colours_multiple(self):
        """Invalid: multiple invalid colour letters."""
        state = "W"*9 + "R"*9 + "G"*9 + "Y"*9 + "O"*9 + "X"*5 + "Z"*4  # X, Z invalid
        
        is_valid, error = validate_state_string(state)
        
        assert is_valid is False
        assert "invalid colour" in error
        # Should mention invalid colours
        assert "X" in error or "Z" in error
    
    def test_invalid_state_string_empty(self):
        """Invalid: empty state string."""
        state = ""
        
        is_valid, error = validate_state_string(state)
        
        assert is_valid is False
        assert "cannot be empty" in error
    
    def test_valid_all_colour_combinations(self):
        """Verify all valid colours work individually."""
        valid_colours = ["W", "Y", "R", "O", "B", "G"]
        
        for colour in valid_colours:
            state = colour * 54  # 54 of same colour
            is_valid, error = validate_state_string(state)
            assert is_valid is True, f"Colour {colour} should be valid"

# ─────────────────────────────────────────────────────────────────────────────
# TESTS: POST /scan/submit endpoint (mocked)
# ─────────────────────────────────────────────────────────────────────────────

class TestScanSubmitEndpoint:
    """Tests for POST /scan/submit endpoint."""
    
    @pytest.fixture
    def mock_conn(self):
        """Mock database connection."""
        return Mock(spec=sqlite3.Connection)
    
    @pytest.fixture
    def valid_request_body(self):
        """Valid ScanSubmitRequest payload."""
        return {
            "session_id": 123,
            "state_string": "W"*9 + "R"*9 + "G"*9 + "Y"*9 + "O"*9 + "B"*9,
            "is_valid": True,
            "confidence": 1.0,
        }
    
    def test_submit_scan_valid(self, mock_conn, valid_request_body):
        """Successfully submit a valid scan."""
        from backend.routers.scan import submit_scan
        from backend.schemas import ScanSubmitRequest
        
        # Mock CRUD functions
        with patch("backend.routers.scan.crud") as mock_crud:
            # Mock session exists
            mock_crud.get_solve_session_by_id.return_value = {"id": 123, "status": "pending"}
            # Mock cube state creation
            mock_crud.create_cube_state.return_value = 456
            # Mock session update
            mock_crud.update_solve_session_status.return_value = None
            
            request = ScanSubmitRequest(**valid_request_body)
            response = submit_scan(request, mock_conn)
            
            assert response.cube_state_id == 456
            mock_crud.create_cube_state.assert_called_once()
            mock_crud.update_solve_session_status.assert_called_once_with(
                mock_conn, 123, "scanning"
            )
    
    def test_submit_scan_session_not_found(self, mock_conn, valid_request_body):
        """Reject scan if session doesn't exist (404)."""
        from backend.routers.scan import submit_scan
        from backend.schemas import ScanSubmitRequest
        from fastapi import HTTPException
        
        with patch("backend.routers.scan.crud") as mock_crud:
            # Session doesn't exist
            mock_crud.get_solve_session_by_id.return_value = None
            
            request = ScanSubmitRequest(**valid_request_body)
            
            with pytest.raises(HTTPException) as exc_info:
                submit_scan(request, mock_conn)
            
            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail
    
    def test_submit_scan_with_unknowns(self, mock_conn, valid_request_body):
        """Reject scan with '?' in state_string (400)."""
        from backend.routers.scan import submit_scan
        from backend.schemas import ScanSubmitRequest
        from fastapi import HTTPException
        
        # Invalid state string with unknowns
        valid_request_body["state_string"] = "W"*6 + "???" + "R"*9 + "G"*9 + "Y"*9 + "O"*9 + "B"*9
        
        with patch("backend.routers.scan.crud") as mock_crud:
            # Session exists
            mock_crud.get_solve_session_by_id.return_value = {"id": 123}
            
            request = ScanSubmitRequest(**valid_request_body)
            
            with pytest.raises(HTTPException) as exc_info:
                submit_scan(request, mock_conn)
            
            assert exc_info.value.status_code == 400
            assert "unrecognized colour" in exc_info.value.detail
    
    def test_submit_scan_invalid_colour(self, mock_conn, valid_request_body):
        """Reject scan with invalid colour letter (400)."""
        from backend.routers.scan import submit_scan
        from backend.schemas import ScanSubmitRequest
        from fastapi import HTTPException
        
        # Invalid: contains 'X' (invalid colour)
        valid_request_body["state_string"] = "W"*9 + "R"*9 + "G"*9 + "Y"*9 + "O"*9 + "X"*9
        
        with patch("backend.routers.scan.crud") as mock_crud:
            mock_crud.get_solve_session_by_id.return_value = {"id": 123}
            
            request = ScanSubmitRequest(**valid_request_body)
            
            with pytest.raises(HTTPException) as exc_info:
                submit_scan(request, mock_conn)
            
            assert exc_info.value.status_code == 400
            assert "invalid colour" in exc_info.value.detail
    
    def test_submit_scan_wrong_length(self, mock_conn, valid_request_body):
        """Reject scan with wrong state_string length (400)."""
        from backend.routers.scan import submit_scan
        from backend.schemas import ScanSubmitRequest
        from fastapi import HTTPException
        
        # Too short
        valid_request_body["state_string"] = "W"*52
        
        with patch("backend.routers.scan.crud") as mock_crud:
            mock_crud.get_solve_session_by_id.return_value = {"id": 123}
            
            request = ScanSubmitRequest(**valid_request_body)
            
            with pytest.raises(HTTPException) as exc_info:
                submit_scan(request, mock_conn)
            
            assert exc_info.value.status_code == 400
            assert "54 characters" in exc_info.value.detail

# ─────────────────────────────────────────────────────────────────────────────
# TESTS: Error message quality
# ─────────────────────────────────────────────────────────────────────────────

class TestErrorMessages:
    """Tests for user-friendly error messages."""
    
    def test_error_message_unknowns_readable(self):
        """Error message for unknowns is user-friendly."""
        state = "W"*6 + "?"*3 + "R"*9 + "G"*9 + "Y"*9 + "O"*9 + "B"*9
        is_valid, error = validate_state_string(state)
        
        assert not is_valid
        # Should tell user to retake scan
        assert "retake" in error.lower() or "unrecognized" in error.lower()
    
    def test_error_message_invalid_length_readable(self):
        """Error message for wrong length is specific."""
        state = "W"*52
        is_valid, error = validate_state_string(state)
        
        assert not is_valid
        assert "54" in error  # Mentions correct length
        assert "52" in error  # Mentions actual length
    
    def test_error_message_invalid_colour_specific(self):
        """Error message names invalid colour(s)."""
        state = "W"*9 + "R"*9 + "G"*9 + "Y"*9 + "O"*9 + "X"*9
        is_valid, error = validate_state_string(state)
        
        assert not is_valid
        assert "X" in error  # Mentions the invalid colour

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
