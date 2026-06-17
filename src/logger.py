"""Structured logging module — provides consistent logging across all modules."""

import logging
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class StructuredFormatter(logging.Formatter):
    """JSON structured log formatter for production use."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "action"):
            log_entry["action"] = record.action
        if hasattr(record, "resource_type"):
            log_entry["resource_type"] = record.resource_type
        if hasattr(record, "resource_id"):
            log_entry["resource_id"] = record.resource_id
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms
        if hasattr(record, "error"):
            log_entry["error"] = str(record.error)
        
        # Add exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


class HumanReadableFormatter(logging.Formatter):
    """Human-readable formatter for development use."""
    
    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[35m", # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        reset = self.RESET
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level = f"{color}{record.levelname:8s}{reset}"
        logger_name = f"{record.name:20s}"
        message = record.getMessage()
        
        # Add extra fields if present
        extras = []
        if hasattr(record, "user_id"):
            extras.append(f"user={record.user_id}")
        if hasattr(record, "action"):
            extras.append(f"action={record.action}")
        if hasattr(record, "resource_type"):
            extras.append(f"type={record.resource_type}")
        if hasattr(record, "resource_id"):
            extras.append(f"id={record.resource_id}")
        if hasattr(record, "duration_ms"):
            extras.append(f"duration={record.duration_ms}ms")
        
        extra_str = f" [{', '.join(extras)}]" if extras else ""
        
        log_line = f"{timestamp} {level} {logger_name}: {message}{extra_str}"
        
        # Add exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_line += f"\n{self.formatException(record.exc_info)}"
        
        return log_line


def setup_logging(level: str = "INFO", structured: bool = False, log_file: str | None = None):
    """Configure logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        structured: If True, use JSON format; if False, use human-readable format
        log_file: Optional file path to write logs to
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if structured:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(HumanReadableFormatter())
    root_logger.addHandler(console_handler)
    
    # File handler (always structured for log files)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger instance."""
    return logging.getLogger(name)


class OperationLogger:
    """Context manager for logging operations with timing."""
    
    def __init__(self, logger: logging.Logger, operation: str, 
                 user_id: str | None = None, resource_type: str | None = None,
                 resource_id: Any = None):
        self.logger = logger
        self.operation = operation
        self.user_id = user_id
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        extra = self._build_extra()
        self.logger.info(f"Starting {self.operation}", extra=extra)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (datetime.now() - self.start_time).total_seconds() * 1000
        extra = self._build_extra()
        extra["duration_ms"] = round(duration_ms, 2)
        
        if exc_type is not None:
            extra["error"] = str(exc_val)
            self.logger.error(f"Failed {self.operation}: {exc_val}", extra=extra, exc_info=True)
        else:
            self.logger.info(f"Completed {self.operation}", extra=extra)
        
        return False  # Don't suppress exceptions
    
    def _build_extra(self) -> dict:
        extra = {}
        if self.user_id:
            extra["user_id"] = self.user_id
        if self.resource_type:
            extra["resource_type"] = self.resource_type
        if self.resource_id is not None:
            extra["resource_id"] = self.resource_id
        return extra
