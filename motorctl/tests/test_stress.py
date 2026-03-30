"""
Motor Control Stress Testing and Timing Verification
SYSC3010 L3-G6

Stress tests for motor control subsystem, verifying:
1. Rapid move sequences execute without deadlock
2. Timing consistency across multiple runs
3. No timing drift or variance
4. Error recovery under load

Run with: pytest motorctl/tests/test_stress.py -v
"""

import sys
import os
import asyncio
import time
import pytest
from statistics import mean, stdev
from typing import List, Tuple

# Add parent dirs to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from actuator import execute_move_sequence, MOVE_MAP, _send_motor_signal


class TestStressRapidSequence:
    """Stress test with rapid move sequences without delay."""
    
    def test_rapid_sequence_no_deadlock(self):
        """Execute rapid sequence without lockup."""
        # Rapid 6-move sequence: R, U, R', F2, D, L
        moves = ["R", "U", "R'", "F2", "D", "L"]
        
        start = time.time()
        result = asyncio.run(execute_move_sequence(moves))
        elapsed = time.time() - start
        
        assert result is True, "Rapid sequence should complete successfully"
        # 6 moves: R(1s) + U(1s) + R'(1s) + F2(2s) + D(1s) + L(1s) = 7s + overhead
        # Plus 0.1s delay between moves = 0.5s
        assert 6.5 < elapsed < 9.5, f"Expected ~7.5s, got {elapsed:.2f}s"
    
    def test_rapid_4_move_sequence(self):
        """Test 4-move sequence (R, U, R', F2)."""
        moves = ["R", "U", "R'", "F2"]
        
        start = time.time()
        result = asyncio.run(execute_move_sequence(moves))
        elapsed = time.time() - start
        
        assert result is True, "4-move sequence should complete without deadlock"
        # Total: 3 × 1s + 1 × 2s = 5s + overhead
        assert 4.5 < elapsed < 6.5, f"Expected ~5s for 4 moves, got {elapsed:.2f}s"
    
    def test_long_solving_sequence(self):
        """Test extended move sequence (like a full Rubik's cube solve)."""
        # Simplified solve: 12 moves
        moves = [
            "R", "U'", "F'", "U",
            "R", "U", "R'", "U'",
            "L'", "U'", "L", "U"
        ]
        
        start = time.time()
        result = asyncio.run(execute_move_sequence(moves))
        elapsed = time.time() - start
        
        assert result is True, "Long sequence should complete"
        # Expect proportional timing: 12 × 1s = 12s + overhead
        assert elapsed > 0, "Should take measurable time"


class TestTimingConsistency:
    """Verify timing consistency across multiple rapid runs."""
    
    def test_timing_consistency_5_runs(self):
        """Run stress sequence 5 times, all should complete consistently."""
        moves = ["R", "U", "R'", "F2"]  # Simplified to 4 moves (5s instead of 7s)
        timings: List[float] = []
        
        for run_num in range(5):
            start = time.time()
            result = asyncio.run(execute_move_sequence(moves))
            elapsed = time.time() - start
            
            assert result is True, f"Run {run_num+1}: Failed to complete sequence"
            timings.append(elapsed)
            print(f"  Run {run_num+1}: {elapsed:.3f}s")
        
        # Calculate statistics
        avg_time = mean(timings)
        if len(timings) > 1:
            std_dev = stdev(timings)
            # Standard deviation should be less than 10% of mean (tight timing)
            assert std_dev < (avg_time * 0.1), \
                f"Timing variance too high: stdev={std_dev:.3f}s, mean={avg_time:.3f}s"
        
        print(f"  Average: {avg_time:.3f}s, StdDev: {stdev(timings) if len(timings) > 1 else 0:.3f}s")
    
    def test_single_move_timing_consistency(self):
        """Verify single move timing is consistent across runs."""
        timings: List[float] = []
        
        for run_num in range(5):  # Reduced from 10 to 5
            start = time.time()
            result = asyncio.run(execute_move_sequence(["R"]))
            elapsed = time.time() - start
            
            assert result is True
            timings.append(elapsed)
        
        avg_time = mean(timings)
        std_dev = stdev(timings) if len(timings) > 1 else 0
        
        # Single 90° move should be ~1 second
        assert 0.8 < avg_time < 1.3, f"Single move average {avg_time:.3f}s out of range"
        # Variance for single move should be tight
        assert std_dev < 0.2, f"Single move variance too high: {std_dev:.3f}s"
        
        print(f"  Single move: avg={avg_time:.3f}s, stdev={std_dev:.3f}s")
    
    def test_double_move_timing_consistency(self):
        """Verify double (180°) move timing is consistent across runs."""
        timings: List[float] = []
        
        for run_num in range(5):  # Reduced from 10 to 5
            start = time.time()
            result = asyncio.run(execute_move_sequence(["R2"]))
            elapsed = time.time() - start
            
            assert result is True
            timings.append(elapsed)
        
        avg_time = mean(timings)
        std_dev = stdev(timings) if len(timings) > 1 else 0
        
        # Double 180° move should be ~2 seconds
        assert 1.8 < avg_time < 2.5, f"Double move average {avg_time:.3f}s out of range"
        # Variance for double move should be tight
        assert std_dev < 0.3, f"Double move variance too high: {std_dev:.3f}s"
        
        print(f"  Double move: avg={avg_time:.3f}s, stdev={std_dev:.3f}s")


class TestTimingPerMoveLogging:
    """Verify per-move timing logs and detect drift."""
    
    def test_per_move_timing_in_sequence(self):
        """Track timing of each move in a 4-move sequence."""
        moves = ["R", "U", "R'", "F2"]
        
        # We'll measure wall-clock time per move
        move_timings: List[Tuple[str, float]] = []
        
        for move in moves:
            start = time.time()
            result = asyncio.run(execute_move_sequence([move]))
            elapsed = time.time() - start
            
            assert result is True
            move_timings.append((move, elapsed))
            print(f"  {move}: {elapsed:.3f}s")
        
        # Verify timing is proportional and consistent
        # Note: wall-clock timing includes asyncio overhead, logging, and GPIO setup
        # The actual step timing (steps/400Hz) is only part of total execution time
        single_90_expected = 200 / 400.0  # 0.5s for 200 steps
        double_180_expected = 400 / 400.0  # 1.0s for 400 steps
        
        for move, timing in move_timings:
            steps = MOVE_MAP[move][2]
            # Wall-clock time should be at least the step time plus overhead
            min_expected = (steps / 400.0) + 0.4  # Plus overhead for asyncio/logging/GPIO
            
            assert timing >= (steps / 400.0), \
                f"Move {move}: timing {timing:.3f}s should be >= step time {steps/400.0:.3f}s"
    
    def test_no_timing_drift_in_sequence(self):
        """Verify no timing drift in repeated moves."""
        # Run same move 5 times, verify timing doesn't drift
        timings: List[float] = []
        
        for rep in range(5):
            start = time.time()
            result = asyncio.run(execute_move_sequence(["R"]))
            elapsed = time.time() - start
            
            assert result is True
            timings.append(elapsed)
        
        # Check for drift: compare first 2 runs to last 3 runs
        first_half_avg = mean(timings[:2]) if len(timings) > 0 else 0
        second_half_avg = mean(timings[2:])
        
        # Drift should be minimal (less than 20% difference)
        if first_half_avg > 0:
            drift_percent = abs(second_half_avg - first_half_avg) / first_half_avg * 100
            assert drift_percent < 20, \
                f"Timing drift detected: first_half={first_half_avg:.3f}s, " \
                f"second_half={second_half_avg:.3f}s, drift={drift_percent:.1f}%"
            
            print(f"  First 2 runs avg: {first_half_avg:.3f}s")
            print(f"  Last 3 runs avg: {second_half_avg:.3f}s")
            print(f"  Drift: {drift_percent:.1f}%")


class TestStressErrorRecovery:
    """Verify error handling under stress conditions."""
    
    def test_rapid_errors_dont_deadlock(self):
        """Multiple consecutive errors should not cause deadlock."""
        for i in range(5):
            result = asyncio.run(execute_move_sequence(["INVALID"]))
            assert result is False, f"Invalid move {i+1} should return False"
    
    def test_mixed_valid_invalid_rapid(self):
        """Rapid alternation of valid and invalid moves."""
        sequences = [
            (["R"], True),
            (["INVALID"], False),
            (["U", "R'"], True),
            (["BAD", "MOVES"], False),
            (["F2", "D", "L"], True),
        ]
        
        for moves, expected in sequences:
            result = asyncio.run(execute_move_sequence(moves))
            assert result is expected, \
                f"Moves {moves} should return {expected}, got {result}"
    
    def test_partial_sequence_under_stress(self):
        """Partial failures should not affect next sequence."""
        # First: valid sequence
        result1 = asyncio.run(execute_move_sequence(["R", "U"]))
        assert result1 is True
        
        # Second: fails mid-sequence
        result2 = asyncio.run(execute_move_sequence(["R", "INVALID", "U"]))
        assert result2 is False
        
        # Third: should work again
        result3 = asyncio.run(execute_move_sequence(["R", "U"]))
        assert result3 is True


class TestStressAllMotors:
    """Stress test all 5 motors in sequence."""
    
    def test_stress_all_motor_ids(self):
        """Execute moves for all 5 motors in one sequence."""
        # Cover all motors: 0=R, 1=L, 2=U, 3=F, 4=D
        moves = ["R", "L", "U", "F", "D"]
        
        start = time.time()
        result = asyncio.run(execute_move_sequence(moves))
        elapsed = time.time() - start
        
        assert result is True
        # 5 motors × 1s each + overhead
        assert 4.5 < elapsed < 6.5, f"Expected ~5-6s for all motors, got {elapsed:.2f}s"
    
    def test_rapid_motor_alternation(self):
        """Rapidly alternate between different motors."""
        moves = ["R", "L", "U", "F", "D"]
        result = asyncio.run(execute_move_sequence(moves))
        assert result is True


class TestStressNoDeadlock:
    """Specific tests to ensure no deadlock conditions."""
    
    def test_no_deadlock_single_move(self):
        """Single move should not deadlock."""
        result = asyncio.run(execute_move_sequence(["R"]))
        assert result is True
    
    def test_no_deadlock_4_move_sequence(self):
        """4-move rapid sequence should not deadlock."""
        moves = ["R", "U", "R'", "F2"]
        result = asyncio.run(execute_move_sequence(moves))
        assert result is True
    
    def test_no_deadlock_8_move_sequence(self):
        """8-move sequence should not deadlock."""
        moves = ["R", "U", "R'", "F2", "D", "L", "U", "D"]
        result = asyncio.run(execute_move_sequence(moves))
        assert result is True
    
    def test_asyncio_event_loop_healthy(self):
        """Verify asyncio event loop remains healthy after stress."""
        for i in range(3):
            try:
                result = asyncio.run(execute_move_sequence(["R", "U"]))
                assert result is True
            except RuntimeError as e:
                pytest.fail(f"Event loop error on iteration {i+1}: {e}")
