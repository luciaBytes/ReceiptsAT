"""
Logger utility for the receipts application.
"""

import logging
import os
from datetime import datetime
from typing import Optional

def setup_logger(log_level: int = logging.INFO) -> logging.Logger:
    """
    Setup the main application logger.
    
    Args:
        log_level: Logging level
        
    Returns:
        Configured logger
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f'receipts_{timestamp}.log')
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger('receipts_app')
    logger.info(f"Logger initialized. Log file: {log_file}")
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name: Module name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f'receipts_app.{name}')

class LogHandler:
    """Custom log handler for the application."""
    
    def __init__(self):
        self.log_entries = []
        self.max_entries = 1000
    
    def add_entry(self, level: str, message: str, timestamp: Optional[datetime] = None):
        """Add a log entry."""
        if timestamp is None:
            timestamp = datetime.now()
        
        entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message
        }
        
        self.log_entries.append(entry)
        
        # Keep only the most recent entries
        if len(self.log_entries) > self.max_entries:
            self.log_entries = self.log_entries[-self.max_entries:]
    
    def get_entries(self) -> list:
        """Get all log entries."""
        return self.log_entries.copy()
    
    def clear_entries(self):
        """Clear all log entries."""
        self.log_entries.clear()
    
    def export_to_file(self, file_path: str) -> bool:
        """Export log entries to a file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for entry in self.log_entries:
                    f.write(f"{entry['timestamp'].isoformat()} - {entry['level']} - {entry['message']}\n")
            return True
        except Exception as e:
            logging.getLogger('receipts_app').error(f"Failed to export logs: {str(e)}")
            return False
