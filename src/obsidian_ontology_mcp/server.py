"""Main MCP server orchestration."""

import logging
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

from .config import settings
from .extraction.skos_extractor import SKOSExtractor
from .graph.builder import KnowledgeGraphBuilder
from .graph.indexer import GraphIndexer
from .graph.query import GraphQueryEngine
from .mcp.tools import MCPTools
from .security.audit import AuditLogger
from .security.validation import InputSanitizer

logger = logging.getLogger(__name__)


class OntologyMCPServer:
    """Main server class that orchestrates all components."""

    def __init__(self, vault_path: Optional[Path] = None) -> None:
        """
        Initialize server.

        Args:
            vault_path: Path to Obsidian vault (defaults to settings)
        """
        self.vault_path = vault_path or settings.vault_path
        self.logger = logging.getLogger(__name__)

        # Configure logging
        self._setup_logging()

        # Initialize components
        self.logger.info("Initializing Obsidian Ontology MCP Server...")

        # Security
        self.sanitizer = InputSanitizer()
        self.audit_logger = AuditLogger()

        # Extraction
        self.extractor = SKOSExtractor(self.vault_path)

        # Graph
        self.graph_builder = KnowledgeGraphBuilder()
        self.indexer: Optional[GraphIndexer] = None
        self.query_engine: Optional[GraphQueryEngine] = None

        # MCP
        self.mcp = FastMCP(settings.mcp_server_name)
        self.mcp_tools: Optional[MCPTools] = None

        # Build graph on initialization
        self._build_graph()

        # Register tools
        self._register_tools()

        self.logger.info("Server initialized successfully")

    def _setup_logging(self) -> None:
        """Configure logging."""
        logging.basicConfig(
            level=getattr(logging, settings.log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(settings.log_file),
                logging.StreamHandler(),
            ],
        )

    def _build_graph(self) -> None:
        """Extract concepts and build knowledge graph."""
        self.logger.info(f"Extracting concepts from vault: {self.vault_path}")

        # Extract all concepts
        concepts = self.extractor.extract_all_concepts()

        if not concepts:
            self.logger.warning("No concepts found in vault!")
            return

        # Build graph
        graph = self.graph_builder.build_graph(concepts)

        # Build indexes
        self.indexer = GraphIndexer(graph)

        # Create query engine
        self.query_engine = GraphQueryEngine(graph, self.indexer)

        self.logger.info(
            f"Graph ready: {graph.number_of_nodes()} concepts, "
            f"{graph.number_of_edges()} relations"
        )

    def _register_tools(self) -> None:
        """Register MCP tools."""
        if not self.query_engine:
            self.logger.error("Cannot register tools: query engine not initialized")
            return

        self.mcp_tools = MCPTools(
            self.query_engine,
            self.sanitizer,
            self.audit_logger,
        )

        self.mcp_tools.register_tools(self.mcp)
        self.logger.info("MCP tools registered")

    def run(self) -> None:
        """Run MCP server (STDIO mode)."""
        self.logger.info("Starting MCP server (STDIO mode)...")
        self.mcp.run()

    def get_app(self):
        """Get FastMCP app for programmatic use."""
        return self.mcp
