#!/usr/bin/env python3
"""
Unit tests for the enhanced progress tracking system.
Tests progress calculation and operation management (non-GUI components only).
"""

import sys
import os
import unittest
import time
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.progress_tracker import (
    ProgressTracker,
    OperationResult,
    OperationStatus,
    ProgressUpdate
)


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
        self.assertFalse(self.tracker.is_cancelled)
        self.assertEqual(len(self.tracker.results), 0)
    
    def test_start_tracking(self):
        """Test starting progress tracking."""
        self.tracker.start(10)
        
        self.assertEqual(self.tracker.total_operations, 10)
        self.assertEqual(self.tracker.completed_operations, 0)
        self.assertEqual(self.tracker.failed_operations, 0)
        self.assertIsNotNone(self.tracker.start_time)
        self.assertFalse(self.tracker.is_cancelled)
    
    def test_successful_operation_update(self):
        """Test updating with successful operation."""
        with patch('time.time') as mock_time:
            mock_time.side_effect = [0.0, 1.0]  # start_time=0, update_time=1
            
            self.tracker.start(5)
            
            result = OperationResult("1", OperationStatus.COMPLETED, "Success")
            self.tracker.update(result)
            
            self.assertEqual(self.tracker.completed_operations, 1)
            self.assertEqual(self.tracker.failed_operations, 0)
            self.assertIn(result, self.tracker.results)
    
    def test_failed_operation_update(self):
        """Test updating with failed operation."""
        with patch('time.time') as mock_time:
            mock_time.side_effect = [0.0, 1.0]  # start_time=0, update_time=1
            
            self.tracker.start(5)
            
            result = OperationResult("1", OperationStatus.FAILED, "Error occurred")
            self.tracker.update(result)
            
            self.assertEqual(self.tracker.completed_operations, 0)
            self.assertEqual(self.tracker.failed_operations, 1)
            self.assertIn(result, self.tracker.results)
    
    def test_multiple_operation_updates(self):
        """Test multiple operation updates."""
        with patch('time.time') as mock_time:
            mock_time.side_effect = [0.0, 1.0, 2.0, 3.0]  # start + 3 updates
            
            self.tracker.start(5)
            
            # Add successful operation
            success = OperationResult("1", OperationStatus.COMPLETED, "Success")
            self.tracker.update(success)
            
            # Add failed operation
            failure = OperationResult("2", OperationStatus.FAILED, "Error")
            self.tracker.update(failure)
            
            # Add another successful operation
            success2 = OperationResult("3", OperationStatus.COMPLETED, "Success 2")
            self.tracker.update(success2)
            
            self.assertEqual(self.tracker.completed_operations, 2)
            self.assertEqual(self.tracker.failed_operations, 1)
            self.assertEqual(len(self.tracker.results), 3)


class TestProgressUpdate(unittest.TestCase):
    """Test cases for progress update creation."""
    
    def test_progress_update_creation(self):
        """Test creating progress updates."""
        # Test basic progress update
        update = ProgressUpdate(
            current=50,
            total=100,
            message="Processing...",
            percentage=50.0,
            current_operation="Working on item 5 of 10"
        )
        
        self.assertEqual(update.current, 50)
        self.assertEqual(update.total, 100)
        self.assertEqual(update.message, "Processing...")
        self.assertEqual(update.percentage, 50.0)
        self.assertEqual(update.current_operation, "Working on item 5 of 10")


class TestOperationResult(unittest.TestCase):
    """Test cases for operation result creation."""
    
    def test_successful_result(self):
        """Test creating successful operation result."""
        result = OperationResult(
            operation_id="test_success",
            status=OperationStatus.COMPLETED,
            message="Operation completed",
            data={"processed": 100},
            duration=1.5
        )
        
        self.assertEqual(result.operation_id, "test_success")
        self.assertEqual(result.status, OperationStatus.COMPLETED)
        self.assertEqual(result.message, "Operation completed")
        self.assertEqual(result.data, {"processed": 100})
        self.assertIsNone(result.error)
        self.assertEqual(result.duration, 1.5)

    def test_failed_result(self):
        """Test creating failed operation result."""
        error = Exception("Something went wrong")
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
    unittest.main(verbosity=2)
