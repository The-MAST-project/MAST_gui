"""
Custom logging handler for MAST_gui that creates daily directories.
"""
import logging
import os
from datetime import datetime


class DailyDirectoryHandler(logging.Handler):
    """
    Custom handler that writes logs to /var/log/mast/<yyyy-mm-dd>/ui.log
    Creates a new directory each day at midnight UTC.
    """
    
    def __init__(self, base_dir='/var/log/mast', filename='ui.log', level=logging.NOTSET):
        super().__init__(level)
        self.base_dir = base_dir
        self.filename = filename
        self.current_date = None
        self.current_handler = None
        self._ensure_handler()
    
    def _ensure_handler(self):
        """
        Ensure we have a handler for today's date.
        Creates directory if needed and opens file handler.
        """
        today = datetime.utcnow().date()
        
        if self.current_date != today:
            # Close old handler if exists
            if self.current_handler:
                self.current_handler.close()
            
            # Create new directory for today
            date_dir = os.path.join(self.base_dir, today.strftime('%Y-%m-%d'))
            os.makedirs(date_dir, exist_ok=True)
            
            # Create new file handler
            log_path = os.path.join(date_dir, self.filename)
            self.current_handler = logging.FileHandler(log_path, encoding='utf-8')
            self.current_handler.setFormatter(self.formatter)
            
            self.current_date = today
    
    def emit(self, record):
        """
        Emit a log record, ensuring we're writing to the correct day's file.
        """
        try:
            self._ensure_handler()
            if self.current_handler:
                self.current_handler.emit(record)
        except Exception:
            self.handleError(record)
    
    def close(self):
        """
        Close the current handler.
        """
        if self.current_handler:
            self.current_handler.close()
        super().close()
