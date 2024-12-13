import logging
from datetime import datetime
import os
from pathlib import Path

def setup_logging():
    """Configure logging for the application with daily rotating file handler"""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Generate timestamp for the log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"tafep_{timestamp}.log"
    
    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_formatter = logging.Formatter(
        "%(levelname)s - %(message)s"
    )
    
    # Set up file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)  # Less verbose for console
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    loggers = {
        'authenticator': logging.getLogger('authenticator'),
        'connection': logging.getLogger('connection'),
        'conversation': logging.getLogger('conversation'),
        'tts': logging.getLogger('tts'),
        'analyzer': logging.getLogger('analyzer'),
        'email': logging.getLogger('email')
    }
    
    # Set GRPC logger to ERROR level only
    logging.getLogger('grpc').setLevel(logging.ERROR)
    
    # Log initial startup message
    root_logger.info(f"Starting new session. Log file: {log_file}")
    root_logger.info("Logging system initialized")
    
    # Create log rotation if needed
    def cleanup_old_logs():
        """Keep only last 7 days of logs"""
        max_logs = 7
        log_files = sorted(log_dir.glob("tafep_*.log"), reverse=True)
        for log_file in log_files[max_logs:]:
            try:
                log_file.unlink()
                root_logger.info(f"Removed old log file: {log_file}")
            except Exception as e:
                root_logger.error(f"Failed to remove old log file {log_file}: {e}")
    
    # Run cleanup
    cleanup_old_logs()