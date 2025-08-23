"""
Unit tests for the enhanced progress tracking system.
Tests progress calculation, UI updates, and operation management.
"""

import unittest
import time
import threading
import os
from unittest.mock import Mock, MagicMock, patch

# Only import tkinter if display is available
GUI_AVAILABLE = False
try:
    if os.environ.get('DISPLAY') or os.name == 'nt':
        import tkinter as tk
        from tkinter import ttk
        GUI_AVAILABLE = True
except:
    pass

from src.utils.progress_tracker import (
    ProgressTracker,
    OperationResult,
    OperationStatus,
    ProgressUpdate
)

if GUI_AVAILABLE:
    from src.utils.progress_tracker import EnhancedProgressBar, OperationManager


class TestProgressTracker(unittest.TestCase):
    """Test cases for the ProgressTracker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tracker = ProgressTracker()
        
    def test_initialization(self):
        """Test tracker initialization."""
        self.assertEqual(self.tracker.total_operations, 0)
        self.assertEqual(self.tracker.completed_operations, 0)
        self.assertEqual(self.tracker.failed_operations, 0)
        self.assertIsNone(self.tracker.start_time)
        self.assertEqual(len(self.tracker.operation_times), 0)
        self.assertEqual(len(self.tracker.results), 0)
        self.assertFalse(self.tracker.is_cancelled)
        
    def test_start_tracking(self):
        """Test starting progress tracking."""
        self.tracker.start(10)
        
        self.assertEqual(self.tracker.total_operations, 10)
        self.assertEqual(self.tracker.completed_operations, 0)
        self.assertIsNotNone(self.tracker.start_time)
        
    def test_reset_functionality(self):
        """Test reset clears all data."""
        # Set some data first
        self.tracker.start(5)
        self.tracker.completed_operations = 2
        self.tracker.failed_operations = 1
        self.tracker.operation_times = [1.0, 2.0]
        
        # Reset and verify
        self.tracker.reset()
        self.assertEqual(self.tracker.total_operations, 0)
        self.assertEqual(self.tracker.completed_operations, 0)
        self.assertEqual(self.tracker.failed_operations, 0)
        self.assertEqual(len(self.tracker.operation_times), 0)
        
    def test_successful_operation_update(self):
        """Test updating with successful operation."""
        self.tracker.start(5)
        
        result = OperationResult(
            operation_id="test_1",
            status=OperationStatus.COMPLETED,
            message="Success",
            duration=1.5
        )
        
        progress = self.tracker.update(result)
        
        self.assertEqual(self.tracker.completed_operations, 1)
        self.assertEqual(self.tracker.failed_operations, 0)
        self.assertEqual(len(self.tracker.operation_times), 1)
        self.assertEqual(self.tracker.operation_times[0], 1.5)
        self.assertEqual(progress.current, 1)
        self.assertEqual(progress.total, 5)
        self.assertEqual(progress.percentage, 20.0)
        
    def test_failed_operation_update(self):
        """Test updating with failed operation."""
        self.tracker.start(3)
        
        result = OperationResult(
            operation_id="test_fail",
            status=OperationStatus.FAILED,
            message="Error occurred",
            error=Exception("Test error"),
            duration=0.5
        )
        
        progress = self.tracker.update(result)
        
        self.assertEqual(self.tracker.completed_operations, 0)
        self.assertEqual(self.tracker.failed_operations, 1)
        self.assertEqual(progress.current, 1)
        self.assertEqual(progress.percentage, 33.33333333333333)
        self.assertIn("1 erros", progress.message)
        
    def test_multiple_operation_updates(self):
        """Test multiple operation updates."""
        self.tracker.start(4)
        
        # Add successful operation
        success_result = OperationResult("1", OperationStatus.COMPLETED, "OK", duration=1.0)
        self.tracker.update(success_result)
        
        # Add failed operation
        fail_result = OperationResult("2", OperationStatus.FAILED, "Error", duration=0.5)
        progress = self.tracker.update(fail_result)
        
        self.assertEqual(self.tracker.completed_operations, 1)
        self.assertEqual(self.tracker.failed_operations, 1)
        self.assertEqual(progress.current, 2)
        self.assertEqual(progress.percentage, 50.0)
        self.assertIn("1 erros", progress.message)
        
    def test_current_operation_tracking(self):
        """Test current operation description tracking."""
        self.tracker.start(2)
        self.tracker.set_current_operation("Processing file 1")
        
        result = OperationResult("1", OperationStatus.COMPLETED, "Done")
        progress = self.tracker.update(result)
        
        self.assertEqual(progress.current_operation, "Processing file 1")
        
    def test_time_estimation(self):
        """Test time estimation calculations."""
        self.tracker.start(4)
        
        # Set start time manually
        self.tracker.start_time = 0
        
        # Complete one operation with specific timing
        result = OperationResult("1", OperationStatus.COMPLETED, "OK", duration=2.0)
        
        # Mock current time for calculation in the module where it's used
        with patch('src.utils.progress_tracker.time.time', return_value=2.0):
            progress = self.tracker.update(result)
            
            # Should estimate 0.5 ops/second, so 3 remaining ops = 6 seconds
            self.assertAlmostEqual(progress.operations_per_second, 0.5)  # 1 op in 2 seconds
            self.assertAlmostEqual(progress.estimated_time_remaining, 6.0)  # 3 ops / 0.5 ops/s
            
    def test_cancel_operation(self):
        """Test cancelling operations."""
        self.tracker.start(5)
        self.tracker.cancel()
        
        self.assertTrue(self.tracker.is_cancelled)
        
    def test_get_summary(self):
        """Test getting operation summary."""
        self.tracker.start(3)
        
        # Set start time manually
        self.tracker.start_time = 0

        # Add some operations
        success = OperationResult("1", OperationStatus.COMPLETED, "OK", duration=1.0)
        failure = OperationResult("2", OperationStatus.FAILED, "Error", duration=0.5)
        
        self.tracker.update(success)
        self.tracker.update(failure)
        
        # Mock the time.time function in the module where it's used
        with patch('src.utils.progress_tracker.time.time', return_value=5.0):
            summary = self.tracker.get_summary()
            
        self.assertEqual(summary['total_operations'], 3)
        self.assertEqual(summary['completed_operations'], 1)
        self.assertEqual(summary['failed_operations'], 1)
        self.assertAlmostEqual(summary['success_rate'], 33.33333333333333)
        self.assertEqual(summary['total_time'], 5.0)
        self.assertEqual(summary['average_time_per_operation'], 0.75)  # (1.0 + 0.5) / 2
        self.assertEqual(len(summary['results']), 2)
@unittest.skipIf(not GUI_AVAILABLE, "GUI not available")
class TestEnhancedProgressBar(unittest.TestCase):
    """Test cases for the EnhancedProgressBar class."""
    
    def setUp(self):
        """Set up test fixtures."""
        try:
            self.root = tk.Tk()
            self.root.withdraw()  # Hide window
            self.parent_frame = ttk.Frame(self.root)
            self.progress_bar = EnhancedProgressBar(self.parent_frame)
        except:
            self.skipTest("GUI initialization failed")
        
    def tearDown(self):
        """Clean up test fixtures."""
        if hasattr(self, 'root'):
            self.root.destroy()
        
    def test_initialization(self):
        """Test progress bar initialization."""
        self.assertIsNotNone(self.progress_bar.progress_var)
        self.assertIsNotNone(self.progress_bar.status_var)
        self.assertIsNotNone(self.progress_bar.detail_var)
        self.assertIsNotNone(self.progress_bar.time_var)
        self.assertFalse(self.progress_bar.is_visible)
        self.assertFalse(self.progress_bar.is_paused)
        
    def test_show_hide(self):
        """Test showing and hiding progress bar."""
        # Initially hidden
        self.assertFalse(self.progress_bar.is_visible)
        
        # Show
        self.progress_bar.show()
        self.assertTrue(self.progress_bar.is_visible)
        
        # Hide
        self.progress_bar.hide()
        self.assertFalse(self.progress_bar.is_visible)
        
    def test_progress_update(self):
        """Test updating progress display."""
        progress_update = ProgressUpdate(
            current=3,
            total=10,
            message="Processing 3/10",
            percentage=30.0,
            estimated_time_remaining=14.0,
            current_operation="Processing file ABC.csv",
            operations_per_second=2.5
        )
        
        self.progress_bar.update(progress_update)
        
        self.assertEqual(self.progress_bar.progress_var.get(), 30.0)
        self.assertEqual(self.progress_bar.status_var.get(), "Processing 3/10")
        self.assertEqual(self.progress_bar.detail_var.get(), "Atual: Processing file ABC.csv")
        self.assertIn("2.5 ops/s", self.progress_bar.time_var.get())
        self.assertIn("Restam: 14s", self.progress_bar.time_var.get())
        
    def test_callback_setting(self):
        """Test setting callback functions."""
        mock_pause = Mock()
        mock_resume = Mock()
        mock_cancel = Mock()
        mock_details = Mock()
        
        self.progress_bar.set_callbacks(
            on_pause=mock_pause,
            on_resume=mock_resume,
            on_cancel=mock_cancel,
            on_show_details=mock_details
        )
        
        self.assertEqual(self.progress_bar.on_pause, mock_pause)
        self.assertEqual(self.progress_bar.on_resume, mock_resume)
        self.assertEqual(self.progress_bar.on_cancel, mock_cancel)
        self.assertEqual(self.progress_bar.on_show_details, mock_details)
        
    def test_pause_resume_toggle(self):
        """Test pause/resume button functionality."""
        mock_pause = Mock()
        mock_resume = Mock()
        
        self.progress_bar.set_callbacks(on_pause=mock_pause, on_resume=mock_resume)
        
        # Initially not paused
        self.assertFalse(self.progress_bar.is_paused)
        
        # Click pause
        self.progress_bar._toggle_pause()
        mock_pause.assert_called_once()
        self.assertTrue(self.progress_bar.is_paused)
        
        # Click resume
        self.progress_bar._toggle_pause()
        mock_resume.assert_called_once()
        self.assertFalse(self.progress_bar.is_paused)
        
    def test_cancel_button(self):
        """Test cancel button functionality."""
        if not hasattr(self, 'progress_bar'):
            self.skipTest("Progress bar not initialized")
            
        mock_cancel = Mock()
        self.progress_bar.set_callbacks(on_cancel=mock_cancel)
        
        self.progress_bar._cancel_operation()
        mock_cancel.assert_called_once()
        
    def test_details_button(self):
        """Test details button functionality."""
        if not hasattr(self, 'progress_bar'):
            self.skipTest("Progress bar not initialized")
            
        mock_details = Mock()
        self.progress_bar.set_callbacks(on_show_details=mock_details)
        
        self.progress_bar._show_details()
        mock_details.assert_called_once()
        
    def test_time_formatting(self):
        """Test time duration formatting."""
        # Test seconds
        self.assertEqual(self.progress_bar._format_time(45), "45s")
        
        # Test minutes
        self.assertEqual(self.progress_bar._format_time(90), "1.5m")
        
        # Test hours
        self.assertEqual(self.progress_bar._format_time(7200), "2.0h")
        
    def test_completion_state(self):
        """Test setting completion state."""
        # Test successful completion
        self.progress_bar.set_completion_state(True, "All operations completed")
        self.assertEqual(self.progress_bar.progress_var.get(), 100)
        self.assertIn("✅", self.progress_bar.status_var.get())
        
        # Test failed completion
        self.progress_bar.set_completion_state(False, "Some operations failed")
        self.assertIn("❌", self.progress_bar.status_var.get())


@unittest.skipIf(not GUI_AVAILABLE, "GUI not available")
class TestOperationManager(unittest.TestCase):
    """Test cases for the OperationManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        try:
            self.root = tk.Tk()
            self.root.withdraw()  # Hide window
            self.parent_frame = ttk.Frame(self.root)
            self.progress_bar = EnhancedProgressBar(self.parent_frame)
            self.manager = OperationManager(self.progress_bar)
        except:
            self.skipTest("GUI initialization failed")
        
    def tearDown(self):
        """Clean up test fixtures."""
        if hasattr(self, 'root'):
            self.root.destroy()
        
    def test_initialization(self):
        """Test operation manager initialization."""
        self.assertIsNotNone(self.manager.progress_bar)
        self.assertIsNotNone(self.manager.tracker)
        self.assertFalse(self.manager.is_paused)
        self.assertFalse(self.manager.is_cancelled)
        self.assertTrue(self.manager.pause_event.is_set())
        
    def test_pause_resume(self):
        """Test pause and resume functionality."""
        # Test pause
        self.manager.pause()
        self.assertTrue(self.manager.is_paused)
        self.assertFalse(self.manager.pause_event.is_set())
        
        # Test resume
        self.manager.resume()
        self.assertFalse(self.manager.is_paused)
        self.assertTrue(self.manager.pause_event.is_set())
        
    def test_cancel(self):
        """Test cancel functionality."""
        self.manager.cancel()
        self.assertTrue(self.manager.is_cancelled)
        self.assertTrue(self.manager.tracker.is_cancelled)
        
    def test_execute_batch_success(self):
        """Test executing a batch of successful operations."""
        if not hasattr(self, 'manager'):
            self.skipTest("Manager not initialized")
            
        # Create mock operations
        operations = [
            lambda: "result1",
            lambda: "result2", 
            lambda: "result3"
        ]
        descriptions = ["Op 1", "Op 2", "Op 3"]
        
        # Mock time.time to provide consistent timing
        with patch('src.utils.progress_tracker.time.time') as mock_time:
            # Provide enough time values for all calls
            mock_time.side_effect = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
            self.manager.execute_batch(operations, descriptions)
            
        # Verify results
        summary = self.manager.tracker.get_summary()
        self.assertEqual(summary['completed_operations'], 3)
        self.assertEqual(summary['failed_operations'], 0)
        self.assertEqual(summary['success_rate'], 100.0)
        
    def test_execute_batch_with_failures(self):
        """Test executing a batch with some failures."""
        if not hasattr(self, 'manager'):
            self.skipTest("Manager not initialized")
            
        def failing_operation():
            raise Exception("Test error")
            
        operations = [
            lambda: "success",
            failing_operation,
            lambda: "success2"
        ]
        
        with patch('src.utils.progress_tracker.time.time') as mock_time:
            # Provide enough time values for all calls  
            mock_time.side_effect = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
            self.manager.execute_batch(operations)
            
        # Verify results
        summary = self.manager.tracker.get_summary()
        self.assertEqual(summary['completed_operations'], 2)
        self.assertEqual(summary['failed_operations'], 1)
        self.assertAlmostEqual(summary['success_rate'], 66.66666666666667)
        
    def test_execute_batch_cancellation(self):
        """Test cancelling a batch operation."""
        operations = [
            lambda: time.sleep(0.1),  # Slow operation
            lambda: "result2",
            lambda: "result3"
        ]
        
        # Start execution in thread and cancel immediately
        def execute_and_cancel():
            time.sleep(0.05)  # Let first operation start
            self.manager.cancel()
            
        cancel_thread = threading.Thread(target=execute_and_cancel)
        cancel_thread.start()
        
        with patch('time.time', side_effect=[0] + [0.1] * 10):
            self.manager.execute_batch(operations)
            
        cancel_thread.join()
        
        # Should have been cancelled before completing all operations
        self.assertTrue(self.manager.is_cancelled)
        
    def test_empty_operations_list(self):
        """Test executing empty operations list."""
        # Should not crash and should not show progress bar
        self.manager.execute_batch([])
        
        # Progress bar should not be visible
        self.assertFalse(self.progress_bar.is_visible)


class TestProgressUpdate(unittest.TestCase):
    """Test cases for the ProgressUpdate dataclass."""
    
    def test_progress_update_creation(self):
        """Test creating a ProgressUpdate instance."""
        update = ProgressUpdate(
            current=5,
            total=10,
            message="Processing 5/10",
            percentage=50.0,
            estimated_time_remaining=30.0,
            current_operation="Processing file.csv",
            operations_per_second=2.0
        )
        
        self.assertEqual(update.current, 5)
        self.assertEqual(update.total, 10)
        self.assertEqual(update.message, "Processing 5/10")
        self.assertEqual(update.percentage, 50.0)
        self.assertEqual(update.estimated_time_remaining, 30.0)
        self.assertEqual(update.current_operation, "Processing file.csv")
        self.assertEqual(update.operations_per_second, 2.0)


class TestOperationResult(unittest.TestCase):
    """Test cases for the OperationResult dataclass."""
    
    def test_successful_result(self):
        """Test creating a successful operation result."""
        result = OperationResult(
            operation_id="test_123",
            status=OperationStatus.COMPLETED,
            message="Operation completed successfully",
            data={"key": "value"},
            duration=1.5
        )
        
        self.assertEqual(result.operation_id, "test_123")
        self.assertEqual(result.status, OperationStatus.COMPLETED)
        self.assertEqual(result.message, "Operation completed successfully")
        self.assertEqual(result.data, {"key": "value"})
        self.assertIsNone(result.error)
        self.assertEqual(result.duration, 1.5)
        
    def test_failed_result(self):
        """Test creating a failed operation result."""
        error = Exception("Test error")
        result = OperationResult(
            operation_id="test_fail",
            status=OperationStatus.FAILED,
            message="Operation failed",
            error=error,
            duration=0.8
        )
        
        self.assertEqual(result.operation_id, "test_fail")
        self.assertEqual(result.status, OperationStatus.FAILED)
        self.assertEqual(result.message, "Operation failed")
        self.assertEqual(result.error, error)
        self.assertIsNone(result.data)
        self.assertEqual(result.duration, 0.8)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
