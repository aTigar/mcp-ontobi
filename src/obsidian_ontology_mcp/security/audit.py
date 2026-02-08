"""Audit logging for security events and API calls."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ..config import settings


class AuditLogger:
    """Structured audit logger for security events."""

    def __init__(self, log_file: Optional[Path] = None) -> None:
        """
        Initialize audit logger.

        Args:
            log_file: Path to audit log file
        """
        self.log_file = log_file or settings.audit_log_file
        self.logger = logging.getLogger("audit")

        # Configure file handler for audit log
        self._setup_file_handler()

    def _setup_file_handler(self) -> None:
        """Set up file handler for audit logging."""
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Create file handler
        handler = logging.FileHandler(self.log_file)
        handler.setLevel(logging.INFO)

        # JSON formatter
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)

        # Add handler to logger
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def _log_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """
        Log an audit event.

        Args:
            event_type: Type of event
            details: Event details
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details,
        }

        self.logger.info(json.dumps(event))

    def log_authentication(
        self,
        username: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Log authentication attempt.

        Args:
            username: Username
            success: Whether authentication succeeded
            ip_address: Client IP address
            user_agent: Client user agent
        """
        self._log_event(
            "authentication",
            {
                "username": username,
                "success": success,
                "ip_address": ip_address,
                "user_agent": user_agent,
            },
        )

    def log_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        username: Optional[str] = None,
        success: bool = True,
        execution_time_ms: Optional[float] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Log MCP tool execution.

        Args:
            tool_name: Name of tool
            arguments: Tool arguments
            username: Username (if authenticated)
            success: Whether execution succeeded
            execution_time_ms: Execution time in milliseconds
            error: Error message if failed
        """
        self._log_event(
            "tool_call",
            {
                "tool_name": tool_name,
                "arguments": arguments,
                "username": username,
                "success": success,
                "execution_time_ms": execution_time_ms,
                "error": error,
            },
        )

    def log_api_call(
        self,
        endpoint: str,
        method: str,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        status_code: int = 200,
        execution_time_ms: Optional[float] = None,
    ) -> None:
        """
        Log HTTP API call.

        Args:
            endpoint: API endpoint
            method: HTTP method
            username: Username (if authenticated)
            ip_address: Client IP address
            status_code: HTTP status code
            execution_time_ms: Execution time in milliseconds
        """
        self._log_event(
            "api_call",
            {
                "endpoint": endpoint,
                "method": method,
                "username": username,
                "ip_address": ip_address,
                "status_code": status_code,
                "execution_time_ms": execution_time_ms,
            },
        )

    def log_rate_limit_exceeded(
        self,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> None:
        """
        Log rate limit violation.

        Args:
            username: Username
            ip_address: Client IP address
            endpoint: API endpoint
        """
        self._log_event(
            "rate_limit_exceeded",
            {
                "username": username,
                "ip_address": ip_address,
                "endpoint": endpoint,
            },
        )

    def log_validation_error(
        self,
        error_type: str,
        details: str,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """
        Log input validation error.

        Args:
            error_type: Type of validation error
            details: Error details
            username: Username
            ip_address: Client IP address
        """
        self._log_event(
            "validation_error",
            {
                "error_type": error_type,
                "details": details,
                "username": username,
                "ip_address": ip_address,
            },
        )

    def log_security_event(
        self,
        event_type: str,
        severity: str,
        details: Dict[str, Any],
    ) -> None:
        """
        Log security event.

        Args:
            event_type: Type of security event
            severity: Severity level (low, medium, high, critical)
            details: Event details
        """
        self._log_event(
            "security_event",
            {
                "event_type": event_type,
                "severity": severity,
                **details,
            },
        )
