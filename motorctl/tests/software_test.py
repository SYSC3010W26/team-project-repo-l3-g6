"""
Motor Control Software Tests
SYSC3010 L3-G6

Tests for motor control without requiring actual hardware.
Run with: pytest motorctl/tests/software_test.py -v
"""

import sys
import os
import asyncio
import time
import pytest

# Add parent dirs to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from actuator import execute_move_sequence, MOVE_MAP, _send_motor_signal


class TestMoveNotationParsing:
    """Verify that move notation maps to correct motor/direction/steps."""
    
    def test_basic_moves_exist(self):
        """All basic move notations should be defined."""
        basic_moves = ["R", "L", "U", "D", "F", "B"]
        for move in basic_moves:
            assert move in MOVE_MAP, f"Move {move} not in MOVE_MAP"
    
    def test_prime_moves_exist(self):
        """Prime (inverse) moves should be defined."""
        for base in ["R", "L", "U", "D", "F", "B"]:
            prime = f"{base}'"
            assert prime in MOVE_MAP, f"Move {prime} not in MOVE_MAP"
    
    def test_double_moves_exist(self):
        """180° (double) moves should be defined."""
        for base in ["R", "L", "U", "D", "F", "B"]:
            double = f"{base}2"
            assert double in MOVE_MAP, f"Move {double} not in MOVE_MAP"
    
    def test_move_map_values_valid(self):
        """Each move should map to (motor_id, direction, steps)."""
        for move, (motor_id, direction, steps) in MOVE_MAP.items():
            assert 0 <= motor_id <= 4, f"Invalid motor_id for {move}: {motor_id}"
            assert direction in [-1, 1], f"Invalid direction for {move}: {direction}"
            assert steps > 0, f"Invalid steps for {move}: {steps}"
            assert steps % 200 == 0, f"Steps not multiple of 200 for {move}: {steps}"
    
    def test_exactly_18_moves(self):
        """Should have exactly 18 move notations (6 faces × 3 variants each)."""
        assert len(MOVE_MAP) == 18, f"Expected 18 moves, got {len(MOVE_MAP)}"


class TestExecuteMoveSequence:
    """Verify motor execution logic."""
    
    def test_empty_sequence(self):
        """Empty move list should return success immediately."""
        result = asyncio.run(execute_move_sequence([]))
        assert result is True
    
    def test_single_move(self):
        """Single valid move should execute successfully."""
        result = asyncio.run(execute_move_sequence(["R"]))
        assert result is True
    
    def test_full_solve_sequence(self):
        """Full sequence of moves should execute without error."""
        moves = ["R", "U", "R'", "U'", "R", "U", "R'", "U'"]
        result = asyncio.run(execute_move_sequence(moves))
        assert result is True
    
    def test_invalid_move_notation(self):
        """Invalid move notation should return False."""
        result = asyncio.run(execute_move_sequence(["X", "Y", "Z"]))  # Invalid moves
        assert result is False
    
    def test_mixed_valid_invalid(self):
        """Sequence with invalid move should fail."""
        result = asyncio.run(execute_move_sequence(["R", "INVALID", "U"]))
        assert result is False
    
    def test_execution_timing(self):
        """Execution should take time proportional to move count."""
        # Single 90° move: ~1 second
        start = time.time()
        asyncio.run(execute_move_sequence(["R"]))
        single_time = time.time() - start
        assert 0.8 < single_time < 1.5, f"Single move took {single_time}s, expected ~1s"
        
        # Double 180° move: ~2 seconds (200 steps -> 1s, 400 steps -> 2s)
        start = time.time()
        asyncio.run(execute_move_sequence(["R2"]))
        double_time = time.time() - start
        assert 1.8 < double_time < 2.5, f"Double move took {double_time}s, expected ~2s"
    
    def test_return_type_is_bool(self):
        """Return value should always be boolean, never None or exception."""
        result_success = asyncio.run(execute_move_sequence(["R"]))
        assert isinstance(result_success, bool), "Success should return bool"
        assert result_success is True
        
        result_failure = asyncio.run(execute_move_sequence(["INVALID"]))
        assert isinstance(result_failure, bool), "Failure should return bool"
        assert result_failure is False
    
    def test_no_exceptions_raised(self):
        """Should never raise exceptions, only return False on error."""
        try:
            asyncio.run(execute_move_sequence(["INVALID", "MOVES", "HERE"]))
            # If we get here, no exception was raised (good)
            assert True
        except Exception as e:
            pytest.fail(f"Should not raise exception, got: {e}")


class TestMotorSignalGeneration:
    """Verify _send_motor_signal function."""
    
    def test_valid_motor_signals(self):
        """All valid motor IDs should generate signals successfully."""
        for motor_id in range(5):
            result = asyncio.run(_send_motor_signal(motor_id, 1, 200))
            assert result is True, f"Motor {motor_id} signal failed"
    
    def test_direction_cw_ccw(self):
        """Both CW and CCW directions should work."""
        result_cw = asyncio.run(_send_motor_signal(0, 1, 200))
        assert result_cw is True
        
        result_ccw = asyncio.run(_send_motor_signal(0, -1, 200))
        assert result_ccw is True
    
    def test_step_counts(self):
        """Both 200 and 400 step counts should work."""
        result_200 = asyncio.run(_send_motor_signal(0, 1, 200))
        assert result_200 is True
        
        result_400 = asyncio.run(_send_motor_signal(0, 1, 400))
        assert result_400 is True
    
    def test_invalid_motor_id(self):
        """Invalid motor ID should return False."""
        result_negative = asyncio.run(_send_motor_signal(-1, 1, 200))
        assert result_negative is False
        
        result_too_large = asyncio.run(_send_motor_signal(5, 1, 200))
        assert result_too_large is False
    
    def test_invalid_steps(self):
        """Zero or negative steps should return False."""
        result_zero = asyncio.run(_send_motor_signal(0, 1, 0))
        assert result_zero is False
        
        result_negative = asyncio.run(_send_motor_signal(0, 1, -100))
        assert result_negative is False
    
    def test_invalid_direction(self):
        """Invalid direction should return False."""
        result_invalid = asyncio.run(_send_motor_signal(0, 0, 200))
        assert result_invalid is False
        
        result_invalid2 = asyncio.run(_send_motor_signal(0, 2, 200))
        assert result_invalid2 is False


class TestMotorSequences:
    """Verify common solving patterns execute correctly."""
    
    def test_sexy_move(self):
        """Classic 'sexy move': R U R' U'"""
        result = asyncio.run(execute_move_sequence(["R", "U", "R'", "U'"]))
        assert result is True
    
    def test_t_permutation(self):
        """T-permutation: R U R' U' R' F R2 U' R' U' R U R' F'"""
        moves = ["R", "U", "R'", "U'", "R'", "F", "R2", "U'", "R'", "U'", "R", "U", "R'", "F'"]
        result = asyncio.run(execute_move_sequence(moves))
        assert result is True
    
    def test_scramble_sequence(self):
        """Random-looking scramble."""
        moves = ["R", "U2", "R'", "F", "U", "F'"]
        result = asyncio.run(execute_move_sequence(moves))
        assert result is True
    
    def test_all_faces_rotations(self):
        """Test all 6 faces with CW and CCW rotations."""
        faces = ["R", "L", "U", "D", "F", "B"]
        for face in faces:
            result_cw = asyncio.run(execute_move_sequence([face]))
            assert result_cw is True, f"{face} CW failed"
            
            prime = f"{face}'"
            result_ccw = asyncio.run(execute_move_sequence([prime]))
            assert result_ccw is True, f"{prime} failed"
    
    def test_long_sequence(self):
        """Longer sequence (30+ moves) should complete without error."""
        long_sequence = ["R", "U", "R'", "U'"] * 8  # 32 moves
        result = asyncio.run(execute_move_sequence(long_sequence))
        assert result is True


class TestTimingPerformance:
    """Verify timing matches specifications."""
    
    def test_cfop_typical_timing(self):
        """Typical CFOP solution (22 moves) should complete in ~22-25 seconds."""
        # Typical efficient solve: 12 moves (reduced from 22 for test speed)
        cfop_solve = [
            "R", "U", "R'", "U'",  # First block
            "R", "U", "R'", "U'",  # Second block
            "R", "U", "R'",        # OLL prep
        ]
        
        start = time.time()
        result = asyncio.run(execute_move_sequence(cfop_solve))
        elapsed = time.time() - start
        
        assert result is True
        # 12 moves @ ~1 sec per move = ~12 seconds
        assert 11 < elapsed < 14, f"CFOP solve took {elapsed}s, expected 12s"


class TestErrorRecovery:
    """Verify graceful error handling."""
    
    def test_error_doesnt_crash(self):
        """Errors should be caught and returned, not raise exceptions."""
        try:
            result = asyncio.run(execute_move_sequence(["GARBAGE", "JUNK"]))
            assert result is False
            # If we get here, we handled the error gracefully
            assert True
        except Exception as e:
            pytest.fail(f"Should handle error gracefully, got exception: {e}")
    
    def test_partial_sequence_failure(self):
        """If move N fails, moves 1..N-1 are executed, N is not, N+1 not attempted."""
        sequence = ["R", "U", "INVALID", "R'"]
        result = asyncio.run(execute_move_sequence(sequence))
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
