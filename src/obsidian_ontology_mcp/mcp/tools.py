"""MCP tool definitions for knowledge graph operations."""

import logging
import time
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from ..graph.query import GraphQueryEngine
from ..security.audit import AuditLogger
from ..security.validation import InputSanitizer

logger = logging.getLogger(__name__)


class MCPTools:
    """MCP tools for Obsidian ontology operations."""

    def __init__(
        self,
        query_engine: GraphQueryEngine,
        sanitizer: InputSanitizer,
        audit_logger: AuditLogger,
    ) -> None:
        """
        Initialize MCP tools.

        Args:
            query_engine: Graph query engine
            sanitizer: Input sanitizer
            audit_logger: Audit logger
        """
        self.query_engine = query_engine
        self.sanitizer = sanitizer
        self.audit_logger = audit_logger
        self.logger = logging.getLogger(__name__)

    def register_tools(self, mcp: FastMCP) -> None:
        """
        Register all tools with FastMCP server.

        Args:
            mcp: FastMCP server instance
        """

        @mcp.tool()
        def get_concept(
            concept_id: str,
            include_relations: bool = True,
        ) -> Dict[str, Any]:
            """
            Retrieve a SKOS concept by ID or preferred label.

            Args:
                concept_id: Concept identifier or preferred label
                include_relations: Include related concepts

            Returns:
                Concept data with optional relations
            """
            start_time = time.time()

            try:
                # Sanitize input
                concept_id = self.sanitizer.sanitize_concept_id(concept_id)

                # Get concept
                concept = self.query_engine.get_concept(concept_id)

                if not concept:
                    # Try finding by label
                    found_id = self.query_engine.indexer.find_by_label(concept_id)
                    if found_id:
                        concept = self.query_engine.get_concept(found_id)

                if not concept:
                    execution_time = (time.time() - start_time) * 1000
                    self.audit_logger.log_tool_call(
                        "get_concept",
                        {"concept_id": concept_id},
                        success=False,
                        execution_time_ms=execution_time,
                        error="Concept not found",
                    )
                    return {
                        "error": f"Concept '{concept_id}' not found",
                        "available_count": self.query_engine.graph.number_of_nodes(),
                    }

                # Truncate content
                if "content" in concept:
                    concept["content"] = self.sanitizer.truncate_content(
                        concept["content"]
                    )

                # Remove relations if not requested
                if not include_relations:
                    for rel in ["broader", "narrower", "related", "prerequisite"]:
                        concept.pop(rel, None)

                execution_time = (time.time() - start_time) * 1000
                self.audit_logger.log_tool_call(
                    "get_concept",
                    {"concept_id": concept_id, "include_relations": include_relations},
                    success=True,
                    execution_time_ms=execution_time,
                )

                return concept

            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                self.logger.error(f"Error in get_concept: {e}")
                self.audit_logger.log_tool_call(
                    "get_concept",
                    {"concept_id": concept_id},
                    success=False,
                    execution_time_ms=execution_time,
                    error=str(e),
                )
                return {"error": str(e)}

        @mcp.tool()
        def expand_context(
            concept_id: str,
            relation_types: Optional[List[str]] = None,
            max_depth: int = 2,
            include_content: bool = True,
        ) -> Dict[str, Any]:
            """
            Expand context around a concept for AI reasoning.

            This is the PRIMARY tool for gathering comprehensive context.
            It performs graph traversal to collect all related concepts.

            Args:
                concept_id: Starting concept identifier
                relation_types: Types of relations to follow (default: broader, narrower, related)
                max_depth: Maximum traversal depth (default: 2, max: 3)
                include_content: Include full note content (default: True)

            Returns:
                Focus concept with all related concepts and their content
            """
            start_time = time.time()

            try:
                # Sanitize inputs
                concept_id = self.sanitizer.sanitize_concept_id(concept_id)
                max_depth = self.sanitizer.validate_depth(max_depth)

                if relation_types is None:
                    relation_types = ["broader", "narrower", "related"]

                # Expand context
                result = self.query_engine.expand_context(
                    concept_id=concept_id,
                    relation_types=relation_types,
                    max_depth=max_depth,
                    include_content=include_content,
                )

                # Truncate content in results
                if include_content and "context_notes" in result:
                    for note in result["context_notes"]:
                        if "content" in note:
                            note["content"] = self.sanitizer.truncate_content(
                                note["content"]
                            )

                execution_time = (time.time() - start_time) * 1000
                self.audit_logger.log_tool_call(
                    "expand_context",
                    {
                        "concept_id": concept_id,
                        "max_depth": max_depth,
                        "include_content": include_content,
                    },
                    success=True,
                    execution_time_ms=execution_time,
                )

                return result

            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                self.logger.error(f"Error in expand_context: {e}")
                self.audit_logger.log_tool_call(
                    "expand_context",
                    {"concept_id": concept_id},
                    success=False,
                    execution_time_ms=execution_time,
                    error=str(e),
                )
                return {"error": str(e)}

        @mcp.tool()
        def search_concepts(
            query: str,
            limit: int = 10,
        ) -> Dict[str, Any]:
            """
            Search for concepts by label or definition.

            Args:
                query: Search query text
                limit: Maximum number of results (default: 10, max: 100)

            Returns:
                List of matching concepts
            """
            start_time = time.time()

            try:
                # Sanitize inputs
                query = self.sanitizer.sanitize_query(query)
                limit = self.sanitizer.validate_limit(limit)

                # Search
                result = self.query_engine.search_concepts(query, limit)

                execution_time = (time.time() - start_time) * 1000
                self.audit_logger.log_tool_call(
                    "search_concepts",
                    {"query": query, "limit": limit},
                    success=True,
                    execution_time_ms=execution_time,
                )

                return result

            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                self.logger.error(f"Error in search_concepts: {e}")
                self.audit_logger.log_tool_call(
                    "search_concepts",
                    {"query": query},
                    success=False,
                    execution_time_ms=execution_time,
                    error=str(e),
                )
                return {"error": str(e)}

        @mcp.tool()
        def get_concept_path(
            from_concept: str,
            to_concept: str,
        ) -> Dict[str, Any]:
            """
            Find shortest path between two concepts.

            Args:
                from_concept: Source concept ID
                to_concept: Target concept ID

            Returns:
                Path information with intermediate concepts
            """
            start_time = time.time()

            try:
                # Sanitize inputs
                from_concept = self.sanitizer.sanitize_concept_id(from_concept)
                to_concept = self.sanitizer.sanitize_concept_id(to_concept)

                # Find path
                result = self.query_engine.get_concept_path(from_concept, to_concept)

                execution_time = (time.time() - start_time) * 1000
                self.audit_logger.log_tool_call(
                    "get_concept_path",
                    {"from_concept": from_concept, "to_concept": to_concept},
                    success=True,
                    execution_time_ms=execution_time,
                )

                return result

            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                self.logger.error(f"Error in get_concept_path: {e}")
                self.audit_logger.log_tool_call(
                    "get_concept_path",
                    {"from_concept": from_concept, "to_concept": to_concept},
                    success=False,
                    execution_time_ms=execution_time,
                    error=str(e),
                )
                return {"error": str(e)}

        @mcp.tool()
        def get_statistics() -> Dict[str, Any]:
            """
            Get knowledge graph statistics.

            Returns:
                Graph metrics and server information
            """
            start_time = time.time()

            try:
                from ..config import settings

                stats = self.query_engine.get_statistics()
                stats["vault_path"] = str(settings.vault_path)
                stats["server_version"] = settings.mcp_server_version

                execution_time = (time.time() - start_time) * 1000
                self.audit_logger.log_tool_call(
                    "get_statistics",
                    {},
                    success=True,
                    execution_time_ms=execution_time,
                )

                return stats

            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                self.logger.error(f"Error in get_statistics: {e}")
                self.audit_logger.log_tool_call(
                    "get_statistics",
                    {},
                    success=False,
                    execution_time_ms=execution_time,
                    error=str(e),
                )
                return {"error": str(e)}
