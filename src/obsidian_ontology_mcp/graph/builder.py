"""Knowledge graph builder using NetworkX."""

import logging
from typing import Dict, List, Optional

import networkx as nx

from ..extraction.skos_extractor import SKOSConcept

logger = logging.getLogger(__name__)


class KnowledgeGraphBuilder:
    """Builds a directed graph from SKOS concepts."""

    def __init__(self) -> None:
        """Initialize graph builder."""
        self.graph = nx.DiGraph()
        self.logger = logging.getLogger(__name__)

    def build_graph(self, concepts: List[SKOSConcept]) -> nx.DiGraph:
        """
        Build knowledge graph from concepts.

        Args:
            concepts: List of SKOS concepts

        Returns:
            NetworkX DiGraph
        """
        self.logger.info(f"Building graph from {len(concepts)} concepts")

        # Add all nodes first
        for concept in concepts:
            self._add_concept_node(concept)

        # Add edges (relations)
        for concept in concepts:
            self._add_concept_relations(concept)

        self.logger.info(
            f"Graph built: {self.graph.number_of_nodes()} nodes, "
            f"{self.graph.number_of_edges()} edges"
        )

        return self.graph

    def _add_concept_node(self, concept: SKOSConcept) -> None:
        """
        Add concept as a node to the graph.

        Args:
            concept: SKOS concept
        """
        # Convert concept to dictionary for node attributes
        node_data = concept.to_dict()

        # Add node with all attributes
        self.graph.add_node(concept.concept_id, **node_data)

    def _add_concept_relations(self, concept: SKOSConcept) -> None:
        """
        Add concept relations as edges.

        Args:
            concept: SKOS concept
        """
        # Add broader relations
        for broader_id in concept.broader:
            if self.graph.has_node(broader_id):
                self.graph.add_edge(
                    concept.concept_id,
                    broader_id,
                    relation_type="broader",
                )
                # Add inverse narrower relation
                self.graph.add_edge(
                    broader_id,
                    concept.concept_id,
                    relation_type="narrower",
                )

        # Add narrower relations (if not already added via broader)
        for narrower_id in concept.narrower:
            if self.graph.has_node(narrower_id):
                if not self.graph.has_edge(concept.concept_id, narrower_id):
                    self.graph.add_edge(
                        concept.concept_id,
                        narrower_id,
                        relation_type="narrower",
                    )
                # Add inverse broader relation
                if not self.graph.has_edge(narrower_id, concept.concept_id):
                    self.graph.add_edge(
                        narrower_id,
                        concept.concept_id,
                        relation_type="broader",
                    )

        # Add related relations (bidirectional)
        for related_id in concept.related:
            if self.graph.has_node(related_id):
                self.graph.add_edge(
                    concept.concept_id,
                    related_id,
                    relation_type="related",
                )
                # Add inverse relation
                self.graph.add_edge(
                    related_id,
                    concept.concept_id,
                    relation_type="related",
                )

        # Add prerequisite relations
        for prereq_id in concept.prerequisite:
            if self.graph.has_node(prereq_id):
                self.graph.add_edge(
                    concept.concept_id,
                    prereq_id,
                    relation_type="prerequisite",
                )

    def update_concept(self, concept: SKOSConcept) -> None:
        """
        Update or add a single concept in the graph.

        Args:
            concept: SKOS concept
        """
        # Remove old edges if concept exists
        if self.graph.has_node(concept.concept_id):
            # Remove all edges involving this concept
            edges_to_remove = list(self.graph.in_edges(concept.concept_id)) + list(
                self.graph.out_edges(concept.concept_id)
            )
            self.graph.remove_edges_from(edges_to_remove)

        # Add/update node
        self._add_concept_node(concept)

        # Add new edges
        self._add_concept_relations(concept)

        self.logger.info(f"Updated concept: {concept.concept_id}")

    def remove_concept(self, concept_id: str) -> None:
        """
        Remove a concept from the graph.

        Args:
            concept_id: Concept ID to remove
        """
        if self.graph.has_node(concept_id):
            self.graph.remove_node(concept_id)
            self.logger.info(f"Removed concept: {concept_id}")

    def get_concept(self, concept_id: str) -> Optional[Dict]:
        """
        Get concept data by ID.

        Args:
            concept_id: Concept ID

        Returns:
            Concept data dictionary or None
        """
        if self.graph.has_node(concept_id):
            return dict(self.graph.nodes[concept_id])
        return None

    def get_statistics(self) -> Dict:
        """
        Get graph statistics.

        Returns:
            Dictionary with graph metrics
        """
        return {
            "total_concepts": self.graph.number_of_nodes(),
            "total_relations": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
            "is_connected": nx.is_weakly_connected(self.graph),
        }
