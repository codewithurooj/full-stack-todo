"""Shared logging module with audit capability.

Provides structured logging for all AI-powered DevOps tools with
audit trail support for tracking operations.
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from rich.console import Console
from rich.logging import RichHandler


class AuditLogger:
    """Audit logger for tracking critical operations."""

    def __init__(self, tool_name: str, log_dir: Optional[Path] = None):
        """Initialize audit logger.

        Args:
            tool_name: Name of the tool
            log_dir: Directory for audit logs (default: ~/.{tool_name}/logs)
        """
        self.tool_name = tool_name
        self.log_dir = log_dir or (Path.home() / f".{tool_name}" / "logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.audit_file = self.log_dir / "audit.log"
        self.console = Console()

    def log_operation(
        self,
        operation: str,
        details: Dict[str, Any],
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """Log an operation to the audit trail.

        Args:
            operation: Name of the operation
            details: Additional details about the operation
            success: Whether the operation succeeded
            error: Error message if operation failed
        """
        timestamp = datetime.utcnow().isoformat()

        audit_entry = {
            'timestamp': timestamp,
            'tool': self.tool_name,
            'operation': operation,
            'success': success,
            'details': details,
        }

        if error:
            audit_entry['error'] = error

        # Write to audit log file
        with open(self.audit_file, 'a') as f:
            f.write(json.dumps(audit_entry) + '\n')

        # Also log to console in debug mode
        if not success and error:
            self.console.print(f"[red]Audit: {operation} failed - {error}[/red]")

    def get_recent_operations(self, limit: int = 100) -> list:
        """Get recent operations from audit log.

        Args:
            limit: Maximum number of operations to return

        Returns:
            List of recent audit entries
        """
        if not self.audit_file.exists():
            return []

        operations = []
        with open(self.audit_file, 'r') as f:
            for line in f:
                try:
                    operations.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        # Return most recent operations
        return operations[-limit:]


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[Path] = None,
    rich_output: bool = True
) -> logging.Logger:
    """Setup a logger with consistent formatting.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for file logging
        rich_output: Use rich formatting for console output

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler
    if rich_output:
        console_handler = RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_time=False,
            show_path=False
        )
    else:
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger
