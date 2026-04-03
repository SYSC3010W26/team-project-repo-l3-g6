#!/usr/bin/env python3
"""
Unit tests for scanner_bridge.py

Tests file loading, API client, retry logic, error handling.

SYSC3010 L3-G6
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import requests

# Import modules under test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from Scanner.scanner_bridge import ScanResult, ScannerAPIClient

# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_dir():
    """Temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def valid_scan_files(temp_dir):
    """Create valid cube_state.json and cube_string.txt in temp dir."""
    # Valid cube state: 6 faces × 9 squares = 54 total, each with unique colour
    cube_state = {
        "U": ["W", "W", "W", "W", "W", "W", "W", "W", "W"],
        "R": ["R", "R", "R", "R", "R", "R", "R", "R", "R"],
        "F": ["G", "G", "G", "G", "G", "G", "G", "G", "G"],
        "D": ["Y", "Y", "Y", "Y", "Y", "Y", "Y", "Y", "Y"],
        "L": ["O", "O", "O", "O", "O", "O", "O", "O", "O"],
        "B": ["B", "B", "B", "B", "B", "B", "B", "B", "B"],
    }
    
    state_string = "".join(["W"]*9 + ["R"]*9 + ["G"]*9 + ["Y"]*9 + ["O"]*9 + ["B"]*9)
    
    state_file = Path(temp_dir) / "cube_string.txt"
    json_file = Path(temp_dir) / "cube_state.json"
    
    state_file.write_text(state_string)
    json_file.write_text(json.dumps(cube_state, indent=2))
    
    return state_file, json_file, state_string, cube_state

@pytest.fixture
def invalid_scan_files_with_unknowns(temp_dir):
    """Create cube_state.json with '?' (unrecognized colours)."""
    cube_state = {
        "U": ["W", "W", "W", "W", "W", "W", "?", "?", "?"],  # 3 unknowns
        "R": ["R", "R", "R", "R", "R", "R", "R", "R", "R"],
        "F": ["G", "G", "G", "G", "G", "G", "G", "G", "G"],
        "D": ["Y", "Y", "Y", "Y", "Y", "Y", "Y", "Y", "Y"],
        "L": ["O", "O", "O", "O", "O", "O", "O", "O", "O"],
        "B": ["B", "B", "B", "B", "B", "B", "B", "B", "B"],
    }
    
    # State string also has '?' for the unknowns
    state_string = "W"*6 + "?"*3 + "R"*9 + "G"*9 + "Y"*9 + "O"*9 + "B"*9
    
    state_file = Path(temp_dir) / "cube_string.txt"
    json_file = Path(temp_dir) / "cube_state.json"
    
    state_file.write_text(state_string)
    json_file.write_text(json.dumps(cube_state, indent=2))
    
    return state_file, json_file, state_string, cube_state

# ─────────────────────────────────────────────────────────────────────────────
# TESTS: ScanResult
# ─────────────────────────────────────────────────────────────────────────────

class TestScanResult:
    """Tests for ScanResult data model."""
    
    def test_from_files_valid_scan(self, valid_scan_files):
        """Load a valid scan with no unknowns."""
        state_file, json_file, state_string, cube_state = valid_scan_files
        
        result = ScanResult.from_files(state_file, json_file)
        
        assert result is not None
        assert result.state_string == state_string
        assert result.cube_state == cube_state
        assert result.is_valid is True
        assert result.confidence == 1.0  # All 54 colours recognized
    
    def test_from_files_invalid_scan_with_unknowns(self, invalid_scan_files_with_unknowns):
        """Load a scan with unrecognized colours ('?')."""
        state_file, json_file, state_string, cube_state = invalid_scan_files_with_unknowns
        
        result = ScanResult.from_files(state_file, json_file)
        
        assert result is not None
        assert "?" in result.state_string
        assert result.is_valid is False  # Contains '?'
        assert result.confidence == 51.0 / 54  # 51 recognized, 3 unknown
    
    def test_from_files_wrong_length_state_string(self, temp_dir):
        """Reject state string with incorrect length."""
        state_file = Path(temp_dir) / "cube_string.txt"
        json_file = Path(temp_dir) / "cube_state.json"
        
        # Write wrong-length state string (52 chars instead of 54)
        state_file.write_text("W"*52)
        cube_state = {"U": ["W"]*9, "R": ["R"]*9, "F": ["G"]*9, 
                      "D": ["Y"]*9, "L": ["O"]*9, "B": ["B"]*9}
        json_file.write_text(json.dumps(cube_state))
        
        result = ScanResult.from_files(state_file, json_file)
        
        assert result is None
    
    def test_from_files_missing_file(self, temp_dir):
        """Handle missing file gracefully."""
        state_file = Path(temp_dir) / "cube_string.txt"
        json_file = Path(temp_dir) / "cube_state.json"
        
        # Only create state file, not json file
        state_file.write_text("W"*54)
        
        result = ScanResult.from_files(state_file, json_file)
        
        assert result is None
    
    def test_from_files_invalid_json(self, temp_dir):
        """Handle malformed JSON gracefully."""
        state_file = Path(temp_dir) / "cube_string.txt"
        json_file = Path(temp_dir) / "cube_state.json"
        
        state_file.write_text("W"*54)
        json_file.write_text("{invalid json")  # Malformed
        
        result = ScanResult.from_files(state_file, json_file)
        
        assert result is None

# ─────────────────────────────────────────────────────────────────────────────
# TESTS: ScannerAPIClient
# ─────────────────────────────────────────────────────────────────────────────

class TestScannerAPIClient:
    """Tests for HTTP client."""
    
    def test_post_scan_success(self, valid_scan_files):
        """Successfully POST scan to API."""
        state_file, json_file, state_string, cube_state = valid_scan_files
        result = ScanResult.from_files(state_file, json_file)
        
        client = ScannerAPIClient("http://localhost:8000", 123)
        
        # Mock requests.post to return success
        with patch("requests.post") as mock_post:
            mock_post.return_value.json.return_value = {"cube_state_id": 456}
            mock_post.return_value.raise_for_status = Mock()
            
            success, cube_state_id = client.post_scan(result)
            
            assert success is True
            assert cube_state_id == 456
            
            # Verify POST was called with correct endpoint and payload
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == "http://localhost:8000/scan/submit"
            assert call_args[1]["json"]["session_id"] == 123
            assert call_args[1]["json"]["state_string"] == state_string
            assert call_args[1]["json"]["is_valid"] is True
            assert call_args[1]["timeout"] == 5.0
    
    def test_post_scan_404_not_found(self, valid_scan_files):
        """Session not found (404) — don't retry."""
        state_file, json_file, _, _ = valid_scan_files
        result = ScanResult.from_files(state_file, json_file)
        
        client = ScannerAPIClient("http://localhost:8000", 999)  # Invalid session
        
        with patch("requests.post") as mock_post:
            # Mock 404 response
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"detail": "Session 999 not found"}
            
            # Create a proper HTTPError with response attached
            http_error = requests.exceptions.HTTPError()
            http_error.response = mock_response
            mock_response.raise_for_status.side_effect = http_error
            mock_post.return_value = mock_response
            
            success, cube_state_id = client.post_scan(result)
            
            assert success is False
            assert cube_state_id is None
            assert mock_post.call_count == 1  # No retries on 404
    
    def test_post_scan_400_bad_request(self, invalid_scan_files_with_unknowns):
        """Bad request (400) with '?' in state string — don't retry."""
        state_file, json_file, _, _ = invalid_scan_files_with_unknowns
        result = ScanResult.from_files(state_file, json_file)
        
        client = ScannerAPIClient("http://localhost:8000", 123)
        
        with patch("requests.post") as mock_post:
            # Mock 400 response
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"detail": "state_string contains unrecognized colours"}
            
            # Create a proper HTTPError with response attached
            http_error = requests.exceptions.HTTPError()
            http_error.response = mock_response
            mock_response.raise_for_status.side_effect = http_error
            mock_post.return_value = mock_response
            
            success, cube_state_id = client.post_scan(result)
            
            assert success is False
            assert cube_state_id is None
            assert mock_post.call_count == 1  # No retries on 400
    
    def test_post_scan_500_server_error_retries(self, valid_scan_files):
        """Server error (500) — retry up to MAX_RETRIES times."""
        state_file, json_file, _, _ = valid_scan_files
        result = ScanResult.from_files(state_file, json_file)
        
        client = ScannerAPIClient("http://localhost:8000", 123)
        
        with patch("requests.post") as mock_post:
            # Mock 500 response
            mock_response = Mock()
            mock_response.status_code = 500
            
            # Create a proper HTTPError with response attached
            http_error = requests.exceptions.HTTPError()
            http_error.response = mock_response
            mock_response.raise_for_status.side_effect = http_error
            mock_post.return_value = mock_response
            
            with patch("time.sleep"):  # Don't actually sleep in tests
                success, cube_state_id = client.post_scan(result)
            
            assert success is False
            assert cube_state_id is None
            # Should have retried MAX_RETRIES (3) times
            assert mock_post.call_count == 3
    
    def test_post_scan_timeout_retries(self, valid_scan_files):
        """Timeout — retry up to MAX_RETRIES times."""
        state_file, json_file, _, _ = valid_scan_files
        result = ScanResult.from_files(state_file, json_file)
        
        client = ScannerAPIClient("http://localhost:8000", 123)
        
        with patch("requests.post") as mock_post:
            # Mock timeout exception
            mock_post.side_effect = requests.exceptions.Timeout()
            
            with patch("time.sleep"):  # Don't actually sleep in tests
                success, cube_state_id = client.post_scan(result)
            
            assert success is False
            assert cube_state_id is None
            assert mock_post.call_count == 3  # MAX_RETRIES
    
    def test_post_scan_retry_succeeds_on_second_attempt(self, valid_scan_files):
        """Retry logic: first attempt fails, second succeeds."""
        state_file, json_file, _, _ = valid_scan_files
        result = ScanResult.from_files(state_file, json_file)
        
        client = ScannerAPIClient("http://localhost:8000", 123)
        
        with patch("requests.post") as mock_post:
            # First call: timeout
            # Second call: success
            success_response = Mock()
            success_response.json.return_value = {"cube_state_id": 456}
            success_response.raise_for_status = Mock()
            
            mock_post.side_effect = [
                requests.exceptions.Timeout(),
                success_response
            ]
            
            with patch("time.sleep"):  # Don't actually sleep in tests
                success, cube_state_id = client.post_scan(result)
            
            assert success is True
            assert cube_state_id == 456
            assert mock_post.call_count == 2  # Tried twice

# ─────────────────────────────────────────────────────────────────────────────
# TESTS: Payload Construction
# ─────────────────────────────────────────────────────────────────────────────

class TestPayloadConstruction:
    """Tests for request payload construction."""
    
    def test_payload_includes_all_fields(self, valid_scan_files):
        """Verify all required fields are in POST payload."""
        state_file, json_file, state_string, _ = valid_scan_files
        result = ScanResult.from_files(state_file, json_file)
        
        with patch("requests.post") as mock_post:
            client = ScannerAPIClient("http://localhost:8000", 123)
            mock_post.return_value.json.return_value = {"cube_state_id": 456}
            mock_post.return_value.raise_for_status = Mock()
            
            client.post_scan(result)
            
            # Extract payload from call
            payload = mock_post.call_args[1]["json"]
            
            assert payload["session_id"] == 123
            assert payload["state_string"] == state_string
            assert payload["is_valid"] is True
            assert payload["confidence"] == 1.0
            assert len(payload) == 4  # Exactly these 4 fields
    
    def test_payload_confidence_calculated_correctly(self, invalid_scan_files_with_unknowns):
        """Verify confidence is calculated as recognized colours / total."""
        state_file, json_file, _, _ = invalid_scan_files_with_unknowns
        result = ScanResult.from_files(state_file, json_file)
        
        with patch("requests.post") as mock_post:
            client = ScannerAPIClient("http://localhost:8000", 123)
            mock_post.return_value.json.return_value = {"cube_state_id": 456}
            mock_post.return_value.raise_for_status = Mock()
            
            client.post_scan(result)
            
            payload = mock_post.call_args[1]["json"]
            # Should be 51 recognized / 54 total
            assert abs(payload["confidence"] - (51.0 / 54)) < 0.001

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
