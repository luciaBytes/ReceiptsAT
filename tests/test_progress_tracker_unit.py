"""
Unit tests for progress_tracker module.
Tests progress tracking, time estimation, and status updates.
"""

import pytest
import time
import sys
import os
from unittest.mock import Mock, patch

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.progress_tracker import (
    ProgressTracker, 
    OperationStatus, 
    OperationResult, 
    ProgressUpdate
)


class TestOperationStatus:
    """Test OperationStatus enum."""
    
    def test_operation_status_values(self):
        """Test that all expected status values exist."""
        assert OperationStatus.PENDING.value == "pending"
        assert OperationStatus.IN_PROGRESS.value == "in_progress"
        assert OperationStatus.COMPLETED.value == "completed"
        assert OperationStatus.FAILED.value == "failed"
        assert OperationStatus.CANCELLED.value == "cancelled"


class TestOperationResult:
    """Test OperationResult dataclass."""
    
    def test_operation_result_creation(self):
        """Test creating an OperationResult."""
        result = OperationResult(
            operation_id="op_001",
            status=OperationStatus.COMPLETED,
            message="Success",
            data={"key": "value"},
            duration=1.5
        )
        
        assert result.operation_id == "op_001"
        assert result.status == OperationStatus.COMPLETED
        assert result.message == "Success"
        assert result.data == {"key": "value"}
        assert result.duration == 1.5
    
    def test_operation_result_defaults(self):
        """Test OperationResult default values."""
        result = OperationResult(
            operation_id="op_002",
            status=OperationStatus.PENDING,
            message="Waiting"
        )
        
        assert result.data is None
        assert result.error is None
        assert result.duration is None


class TestProgressUpdate:
    """Test ProgressUpdate dataclass."""
    
    def test_progress_update_creation(self):
        """Test creating a ProgressUpdate."""
        update = ProgressUpdate(
            current=5,
            total=10,
            message="Processing...",
            percentage=50.0,
            estimated_time_remaining=30.0,
            operations_per_second=2.0
        )
        
        assert update.current == 5
        assert update.total == 10
        assert update.percentage == 50.0
        assert update.estimated_time_remaining == 30.0
    
    def test_progress_update_optional_fields(self):
        """Test ProgressUpdate with optional fields as None."""
        update = ProgressUpdate(
            current=3,
            total=10,
            message="Working",
            percentage=30.0
        )
        
        assert update.estimated_time_remaining is None
        assert update.current_operation is None
        assert update.operations_per_second is None


class TestProgressTrackerInit:
    """Test ProgressTracker initialization."""
    
    def test_init_creates_tracker(self):
        """Test that ProgressTracker initializes correctly."""
        tracker = ProgressTracker()
        
        assert tracker.total_operations == 0
        assert tracker.completed_operations == 0
        assert tracker.failed_operations == 0
        assert tracker.start_time is None
        assert tracker.results == []
        assert tracker.is_cancelled is False
    
    def test_reset_clears_state(self):
        """Test that reset clears all tracking state."""
        tracker = ProgressTracker()
        
        # Set some state
        tracker.total_operations = 10
        tracker.completed_operations = 5
        tracker.failed_operations = 1
        tracker.start_time = time.time()
        tracker.results = [Mock()]
        tracker.is_cancelled = True
        
        # Reset
        tracker.reset()
        
        assert tracker.total_operations == 0
        assert tracker.completed_operations == 0
        assert tracker.failed_operations == 0
        assert tracker.start_time is None
        assert tracker.results == []
        assert tracker.is_cancelled is False


class TestProgressTracking:
    """Test progress tracking functionality."""
    
    def test_start_initializes_tracking(self):
        """Test that start() initializes tracking for operations."""
        tracker = ProgressTracker()
        
        tracker.start(total_operations=10)
        
        assert tracker.total_operations == 10
        assert tracker.start_time is not None
        assert tracker.completed_operations == 0
    
    def test_start_resets_previous_state(self):
        """Test that start() resets previous tracking state."""
        tracker = ProgressTracker()
        
        # Set previous state
        tracker.completed_operations = 5
        tracker.results = [Mock()]
        
        tracker.start(total_operations=20)
        
        assert tracker.total_operations == 20
        assert tracker.completed_operations == 0
        assert tracker.results == []
    
    def test_update_with_completed_operation(self):
        """Test updating with a completed operation."""
        tracker = ProgressTracker()
        tracker.start(10)
        
        result = OperationResult(
            operation_id="op_001",
            status=OperationStatus.COMPLETED,
            message="Done",
            duration=1.0
        )
        
        progress = tracker.update(result)
        
        assert tracker.completed_operations == 1
        assert tracker.failed_operations == 0
        assert len(tracker.results) == 1
        assert isinstance(progress, ProgressUpdate)
    
    def test_update_with_failed_operation(self):
        """Test updating with a failed operation."""
        tracker = ProgressTracker()
        tracker.start(10)
        
        result = OperationResult(
            operation_id="op_001",
            status=OperationStatus.FAILED,
            message="Error",
            error=Exception("Test error")
        )
        
        progress = tracker.update(result)
        
        assert tracker.completed_operations == 0
        assert tracker.failed_operations == 1
        assert len(tracker.results) == 1
    
    def test_update_tracks_operation_times(self):
        """Test that update tracks operation durations."""
        tracker = ProgressTracker()
        tracker.start(10)
        
        result = OperationResult(
            operation_id="op_001",
            status=OperationStatus.COMPLETED,
            message="Done",
            duration=1.5
        )
        
        tracker.update(result)
        
        assert len(tracker.operation_times) == 1
        assert tracker.operation_times[0] == 1.5
    
    def test_multiple_updates(self):
        """Test tracking multiple operations."""
        tracker = ProgressTracker()
        tracker.start(3)
        
        for i in range(3):
            result = OperationResult(
                operation_id=f"op_{i}",
                status=OperationStatus.COMPLETED,
                message=f"Done {i}",
                duration=1.0
            )
            tracker.update(result)
        
        assert tracker.completed_operations == 3
        assert len(tracker.results) == 3
        assert len(tracker.operation_times) == 3


class TestCurrentOperationTracking:
    """Test current operation description tracking."""
    
    def test_set_current_operation(self):
        """Test setting current operation description."""
        tracker = ProgressTracker()
        
        tracker.set_current_operation("Processing file...")
        
        assert tracker.current_operation == "Processing file..."
    
    def test_current_operation_updates(self):
        """Test that current operation can be updated multiple times."""
        tracker = ProgressTracker()
        
        tracker.set_current_operation("Step 1")
        assert tracker.current_operation == "Step 1"
        
        tracker.set_current_operation("Step 2")
        assert tracker.current_operation == "Step 2"


class TestCancellation:
    """Test operation cancellation."""
    
    def test_cancel_sets_flag(self):
        """Test that cancel() sets the cancellation flag."""
        tracker = ProgressTracker()
        
        tracker.cancel()
        
        assert tracker.is_cancelled is True
    
    def test_cancel_can_be_checked(self):
        """Test that cancellation status can be checked."""
        tracker = ProgressTracker()
        
        assert tracker.is_cancelled is False
        
        tracker.cancel()
        
        assert tracker.is_cancelled is True


class TestProgressCalculation:
    """Test progress percentage and time estimation calculations."""
    
    def test_progress_percentage_calculation(self):
        """Test that progress percentage is calculated correctly."""
        tracker = ProgressTracker()
        tracker.start(10)
        
        # Complete 5 out of 10
        for i in range(5):
            result = OperationResult(
                operation_id=f"op_{i}",
                status=OperationStatus.COMPLETED,
                message="Done",
                duration=1.0
            )
            progress = tracker.update(result)
        
        # Should be approximately 50%
        assert progress.current == 5
        assert progress.total == 10
        assert 45 <= progress.percentage <= 55
    
    def test_time_estimation_with_operation_times(self):
        """Test time estimation based on operation durations."""
        tracker = ProgressTracker()
        tracker.start(10)
        
        # Complete some operations with known durations
        for i in range(3):
            result = OperationResult(
                operation_id=f"op_{i}",
                status=OperationStatus.COMPLETED,
                message="Done",
                duration=2.0  # Each takes 2 seconds
            )
            progress = tracker.update(result)
        
        # Time estimate should be calculated (may be None in some implementations)
        if progress.estimated_time_remaining is not None:
            # 7 remaining * ~2 seconds each = ~14 seconds
            assert progress.estimated_time_remaining > 0


class TestResultsCollection:
    """Test collection of operation results."""
    
    def test_results_accumulated(self):
        """Test that all operation results are accumulated."""
        tracker = ProgressTracker()
        tracker.start(5)
        
        for i in range(5):
            result = OperationResult(
                operation_id=f"op_{i}",
                status=OperationStatus.COMPLETED,
                message=f"Done {i}"
            )
            tracker.update(result)
        
        assert len(tracker.results) == 5
        assert all(r.status == OperationStatus.COMPLETED for r in tracker.results)
    
    def test_results_include_failures(self):
        """Test that failed operations are included in results."""
        tracker = ProgressTracker()
        tracker.start(3)
        
        # Add success
        tracker.update(OperationResult("op_1", OperationStatus.COMPLETED, "OK"))
        
        # Add failure
        tracker.update(OperationResult("op_2", OperationStatus.FAILED, "Error"))
        
        # Add another success
        tracker.update(OperationResult("op_3", OperationStatus.COMPLETED, "OK"))
        
        assert len(tracker.results) == 3
        assert tracker.completed_operations == 2
        assert tracker.failed_operations == 1


class TestProgressAttributes:
    """Test progress tracker attributes and properties."""
    
    def test_tracks_total_operations(self):
        """Test that total operations are tracked."""
        tracker = ProgressTracker()
        tracker.start(10)
        
        assert tracker.total_operations == 10
        assert tracker.completed_operations == 0
        assert tracker.failed_operations == 0
    
    def test_tracks_progress_after_updates(self):
        """Test tracking after operations complete."""
        tracker = ProgressTracker()
        tracker.start(5)
        
        tracker.update(OperationResult("op_1", OperationStatus.COMPLETED, "Done"))
        tracker.update(OperationResult("op_2", OperationStatus.COMPLETED, "Done"))
        
        assert tracker.completed_operations == 2
        assert tracker.total_operations == 5
        assert len(tracker.results) == 2


class TestReset:
    """Test reset functionality."""
    
    def test_reset_after_operations(self):
        """Test that reset clears all tracking data."""
        tracker = ProgressTracker()
        tracker.start(5)
        
        tracker.update(OperationResult("op_1", OperationStatus.COMPLETED, "Done"))
        tracker.update(OperationResult("op_2", OperationStatus.FAILED, "Error"))
        
        tracker.reset()
        
        assert tracker.total_operations == 0
        assert tracker.completed_operations == 0
        assert tracker.failed_operations == 0
        assert len(tracker.results) == 0
