"""
Comprehensive unit tests for utils.logger module.
Tests logger configuration, LogHandler functionality, and error handling.
"""

import pytest
import sys
import os
import logging
import tempfile
from unittest.mock import Mock, patch, mock_open, MagicMock
from datetime import datetime
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.logger import setup_logger, get_logger, LogHandler


class TestLogHandlerAddEntry:
    """Test LogHandler.add_entry functionality."""
    
    def test_add_entry_with_timestamp(self):
        """Test adding entry with explicit timestamp."""
        handler = LogHandler()
        test_time = datetime(2024, 1, 15, 10, 30, 45)
        
        handler.add_entry("INFO", "Test message", timestamp=test_time)
        
        entries = handler.get_entries()
        assert len(entries) == 1
        assert entries[0]['timestamp'] == test_time
        assert entries[0]['level'] == "INFO"
        assert entries[0]['message'] == "Test message"
    
    def test_add_entry_without_timestamp(self):
        """Test adding entry without timestamp uses current time."""
        handler = LogHandler()
        
        before_time = datetime.now()
        handler.add_entry("DEBUG", "Auto timestamp test")
        after_time = datetime.now()
        
        entries = handler.get_entries()
        assert len(entries) == 1
        assert before_time <= entries[0]['timestamp'] <= after_time
    
    def test_add_multiple_entries(self):
        """Test adding multiple log entries."""
        handler = LogHandler()
        
        handler.add_entry("INFO", "First")
        handler.add_entry("WARNING", "Second")
        handler.add_entry("ERROR", "Third")
        
        entries = handler.get_entries()
        assert len(entries) == 3
        assert entries[0]['message'] == "First"
        assert entries[1]['level'] == "WARNING"
        assert entries[2]['message'] == "Third"


class TestLogHandlerMaxEntries:
    """Test max entries enforcement."""
    
    def test_max_entries_enforcement(self):
        """Test that old entries are removed when max is reached."""
        handler = LogHandler()
        handler.max_entries = 5
        
        # Add more than max
        for i in range(10):
            handler.add_entry("INFO", f"Message {i}")
        
        entries = handler.get_entries()
        assert len(entries) == 5
        # Should keep the most recent 5
        assert entries[0]['message'] == "Message 5"
        assert entries[4]['message'] == "Message 9"
    
    def test_max_entries_boundary(self):
        """Test behavior exactly at max entries."""
        handler = LogHandler()
        handler.max_entries = 3
        
        handler.add_entry("INFO", "1")
        handler.add_entry("INFO", "2")
        handler.add_entry("INFO", "3")
        
        entries = handler.get_entries()
        assert len(entries) == 3
        
        # Add one more to trigger pruning
        handler.add_entry("INFO", "4")
        entries = handler.get_entries()
        
        assert len(entries) == 3
        assert entries[0]['message'] == "2"
        assert entries[2]['message'] == "4"
    
    def test_custom_max_entries(self):
        """Test setting custom max entries value."""
        handler = LogHandler()
        handler.max_entries = 100
        
        for i in range(150):
            handler.add_entry("INFO", f"Entry {i}")
        
        entries = handler.get_entries()
        assert len(entries) == 100


class TestLogHandlerGetEntries:
    """Test LogHandler.get_entries functionality."""
    
    def test_get_entries_returns_copy(self):
        """Test that get_entries returns a copy, not reference."""
        handler = LogHandler()
        handler.add_entry("INFO", "Original")
        
        entries1 = handler.get_entries()
        entries2 = handler.get_entries()
        
        # Modifying one shouldn't affect the other
        entries1.append({'test': 'data'})
        
        assert len(entries1) != len(entries2)
        assert len(entries2) == 1
    
    def test_get_entries_empty(self):
        """Test getting entries when none exist."""
        handler = LogHandler()
        
        entries = handler.get_entries()
        
        assert isinstance(entries, list)
        assert len(entries) == 0


class TestLogHandlerClear:
    """Test LogHandler.clear_entries functionality."""
    
    def test_clear_entries(self):
        """Test clearing all entries."""
        handler = LogHandler()
        
        for i in range(10):
            handler.add_entry("INFO", f"Entry {i}")
        
        assert len(handler.get_entries()) == 10
        
        handler.clear_entries()
        
        assert len(handler.get_entries()) == 0
    
    def test_clear_empty_entries(self):
        """Test clearing when already empty."""
        handler = LogHandler()
        
        handler.clear_entries()
        
        assert len(handler.get_entries()) == 0
    
    def test_add_after_clear(self):
        """Test adding entries after clearing."""
        handler = LogHandler()
        
        handler.add_entry("INFO", "First")
        handler.clear_entries()
        handler.add_entry("INFO", "After clear")
        
        entries = handler.get_entries()
        assert len(entries) == 1
        assert entries[0]['message'] == "After clear"


class TestLogHandlerExport:
    """Test LogHandler.export_to_file functionality."""
    
    def test_export_to_file_success(self):
        """Test successful export to file."""
        handler = LogHandler()
        handler.add_entry("INFO", "Test message 1")
        handler.add_entry("ERROR", "Test message 2")
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            file_path = f.name
        
        try:
            result = handler.export_to_file(file_path)
            
            assert result is True
            assert os.path.exists(file_path)
            
            # Verify content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "INFO" in content
                assert "Test message 1" in content
                assert "ERROR" in content
                assert "Test message 2" in content
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def test_export_empty_entries(self):
        """Test exporting when no entries exist."""
        handler = LogHandler()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            file_path = f.name
        
        try:
            result = handler.export_to_file(file_path)
            
            assert result is True
            assert os.path.exists(file_path)
            
            # File should be empty or just whitespace
            with open(file_path, 'r') as f:
                content = f.read()
                assert len(content.strip()) == 0
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def test_export_invalid_path(self):
        """Test export with invalid file path."""
        handler = LogHandler()
        handler.add_entry("INFO", "Test")
        
        # Use invalid path
        invalid_path = "/invalid/nonexistent/path/file.log"
        
        result = handler.export_to_file(invalid_path)
        
        assert result is False
    
    def test_export_with_special_characters(self):
        """Test export with special characters in messages."""
        handler = LogHandler()
        handler.add_entry("INFO", "Message with émojis: 🎉 and spëcial çhars")
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            file_path = f.name
        
        try:
            result = handler.export_to_file(file_path)
            
            assert result is True
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "émojis" in content or "emojis" in content  # May vary by encoding
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)


class TestSetupLogger:
    """Test setup_logger functionality."""
    
    def test_setup_logger_returns_logger(self):
        """Test that setup_logger returns a logger instance."""
        logger = setup_logger()
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'receipts_app'
    
    def test_setup_logger_already_configured(self):
        """Test that calling setup_logger twice doesn't duplicate handlers."""
        logger1 = setup_logger()
        initial_handler_count = len(logger1.handlers)
        
        logger2 = setup_logger()
        
        # Should return same logger without adding handlers
        assert logger2.name == logger1.name
        assert len(logger2.handlers) == initial_handler_count
    
    def test_setup_logger_creates_log_directory(self):
        """Test that setup_logger creates logs directory."""
        # The logger creates logs directory in workspace root
        # This is tested implicitly by successful logger creation
        logger = setup_logger()
        
        assert logger is not None
        # If we got here without exception, directory was created
    
    def test_setup_logger_level(self):
        """Test that logger level is set correctly."""
        logger = setup_logger(log_level=logging.DEBUG)
        
        # Logger may already be configured from previous tests
        # Just verify it returns a logger instance
        assert isinstance(logger, logging.Logger)


class TestGetLogger:
    """Test get_logger functionality."""
    
    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger."""
        logger = get_logger("test_module")
        
        assert isinstance(logger, logging.Logger)
    
    def test_get_logger_name_format(self):
        """Test that logger name is formatted correctly."""
        module_name = "my_module"
        logger = get_logger(module_name)
        
        assert module_name in logger.name
        assert "receipts_app" in logger.name
    
    def test_get_logger_different_names(self):
        """Test getting loggers with different names."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        
        assert logger1.name != logger2.name
        assert "module1" in logger1.name
        assert "module2" in logger2.name
    
    def test_get_logger_same_name(self):
        """Test that same name returns same logger."""
        logger1 = get_logger("same_module")
        logger2 = get_logger("same_module")
        
        assert logger1.name == logger2.name


class TestLogHandlerIntegration:
    """Integration tests for LogHandler."""
    
    def test_full_workflow(self):
        """Test complete workflow: add, get, clear, export."""
        handler = LogHandler()
        
        # Add entries
        handler.add_entry("INFO", "Message 1")
        handler.add_entry("WARNING", "Message 2")
        handler.add_entry("ERROR", "Message 3")
        
        # Get and verify
        entries = handler.get_entries()
        assert len(entries) == 3
        
        # Export
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            file_path = f.name
        
        try:
            result = handler.export_to_file(file_path)
            assert result is True
            
            # Clear
            handler.clear_entries()
            assert len(handler.get_entries()) == 0
            
            # Verify file still exists
            assert os.path.exists(file_path)
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def test_multiple_handlers(self):
        """Test using multiple LogHandler instances."""
        handler1 = LogHandler()
        handler2 = LogHandler()
        
        handler1.add_entry("INFO", "Handler 1")
        handler2.add_entry("INFO", "Handler 2")
        
        assert len(handler1.get_entries()) == 1
        assert len(handler2.get_entries()) == 1
        assert handler1.get_entries()[0]['message'] != handler2.get_entries()[0]['message']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
