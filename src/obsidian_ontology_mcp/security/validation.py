"""Input validation and sanitization for security."""

import logging
import re
from typing import Any, Dict, List

from ..config import settings

logger = logging.getLogger(__name__)


class InputSanitizer:
    """Sanitizes and validates user inputs to prevent injection attacks."""

    # Patterns for detecting malicious input
    PROMPT_INJECTION_PATTERNS = [
        r"ignore\s+(previous|above|all)\s+instructions",
        r"disregard\s+(previous|above|all)",
        r"forget\s+(previous|above|all)",
        r"system\s*:\s*you\s+are",
        r"<\s*script",
        r"javascript\s*:",
        r"on(load|error|click)\s*=",
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.",
        r"~\/",
        r"\/etc\/",
        r"\/proc\/",
    ]

    def __init__(self) -> None:
        """Initialize sanitizer."""
        self.logger = logging.getLogger(__name__)
        self.compiled_patterns = {
            "prompt_injection": [
                re.compile(pattern, re.IGNORECASE)
                for pattern in self.PROMPT_INJECTION_PATTERNS
            ],
            "path_traversal": [
                re.compile(pattern, re.IGNORECASE)
                for pattern in self.PATH_TRAVERSAL_PATTERNS
            ],
        }

    def sanitize_query(self, query: str) -> str:
        """
        Sanitize a search query.

        Args:
            query: User query string

        Returns:
            Sanitized query

        Raises:
            ValueError: If query contains malicious patterns
        """
        # Check length
        if len(query) > settings.security.max_query_length:
            raise ValueError(
                f"Query too long (max {settings.security.max_query_length} characters)"
            )

        # Check for prompt injection
        for pattern in self.compiled_patterns["prompt_injection"]:
            if pattern.search(query):
                self.logger.warning(f"Prompt injection attempt detected: {query[:50]}")
                raise ValueError("Query contains potentially malicious content")

        # Strip HTML tags
        query = re.sub(r"<[^>]+>", "", query)

        # Trim whitespace
        query = query.strip()

        return query

    def sanitize_concept_id(self, concept_id: str) -> str:
        """
        Sanitize a concept ID.

        Args:
            concept_id: Concept identifier

        Returns:
            Sanitized concept ID

        Raises:
            ValueError: If concept ID is invalid
        """
        # Check for path traversal
        for pattern in self.compiled_patterns["path_traversal"]:
            if pattern.search(concept_id):
                self.logger.warning(f"Path traversal attempt: {concept_id}")
                raise ValueError("Invalid concept ID")

        # Allow only alphanumeric, underscore, hyphen
        if not re.match(r"^[a-zA-Z0-9_-]+$", concept_id):
            raise ValueError("Concept ID contains invalid characters")

        return concept_id.lower()

    def validate_depth(self, depth: int) -> int:
        """
        Validate context expansion depth.

        Args:
            depth: Requested depth

        Returns:
            Validated depth

        Raises:
            ValueError: If depth is invalid
        """
        if depth < 0:
            raise ValueError("Depth must be non-negative")

        if depth > settings.security.max_context_depth:
            self.logger.warning(f"Depth {depth} exceeds maximum, capping to {settings.security.max_context_depth}")
            depth = settings.security.max_context_depth

        return depth

    def validate_limit(self, limit: int) -> int:
        """
        Validate result limit.

        Args:
            limit: Requested limit

        Returns:
            Validated limit

        Raises:
            ValueError: If limit is invalid
        """
        if limit < 1:
            raise ValueError("Limit must be positive")

        if limit > settings.security.max_results_per_query:
            self.logger.warning(f"Limit {limit} exceeds maximum, capping to {settings.security.max_results_per_query}")
            limit = settings.security.max_results_per_query

        return limit

    def truncate_content(self, content: str) -> str:
        """
        Truncate content to maximum length.

        Args:
            content: Content string

        Returns:
            Truncated content
        """
        max_length = settings.security.max_concept_content_length

        if len(content) > max_length:
            self.logger.debug(f"Truncating content from {len(content)} to {max_length} characters")
            return content[:max_length] + "\n[... content truncated ...]"

        return content

    def sanitize_tool_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize MCP tool arguments.

        Args:
            arguments: Tool arguments dictionary

        Returns:
            Sanitized arguments

        Raises:
            ValueError: If arguments contain malicious content
        """
        sanitized = {}

        for key, value in arguments.items():
            if isinstance(value, str):
                # Sanitize string values
                if key in ["query", "concept_id", "from_concept", "to_concept"]:
                    if key == "query":
                        sanitized[key] = self.sanitize_query(value)
                    else:
                        sanitized[key] = self.sanitize_concept_id(value)
                else:
                    sanitized[key] = value

            elif isinstance(value, int):
                # Validate numeric values
                if key in ["max_depth", "depth"]:
                    sanitized[key] = self.validate_depth(value)
                elif key == "limit":
                    sanitized[key] = self.validate_limit(value)
                else:
                    sanitized[key] = value

            elif isinstance(value, list):
                # Sanitize list values
                sanitized[key] = [
                    self.sanitize_query(item) if isinstance(item, str) else item
                    for item in value
                ]

            else:
                sanitized[key] = value

        return sanitized
