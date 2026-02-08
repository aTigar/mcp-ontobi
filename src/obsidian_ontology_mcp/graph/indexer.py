"""Multi-index system for fast concept lookups."""

import logging
from typing import Dict, List, Optional, Set

import networkx as nx

logger = logging.getLogger(__name__)


class GraphIndexer:
    """Builds and maintains indexes for fast concept lookups."""

    def __init__(self, graph: nx.DiGraph) -> None:
        """
        Initialize indexer.

        Args:
            graph: NetworkX graph to index
        """
        self.graph = graph
        self.logger = logging.getLogger(__name__)

        # Indexes
        self.label_index: Dict[str, str] = {}  # label -> concept_id
        self.alt_label_index: Dict[str, str] = {}  # alt_label -> concept_id
        self.notation_index: Dict[str, str] = {}  # notation -> concept_id
        self.relation_index: Dict[str, Dict[str, List[str]]] = {}  # relation_type -> {concept_id -> [related_ids]}

        self._build_indexes()

    def _build_indexes(self) -> None:
        """Build all indexes from graph."""
        self.logger.info("Building indexes...")

        for node_id, node_data in self.graph.nodes(data=True):
            # Label index (lowercase for case-insensitive search)
            pref_label = node_data.get("prefLabel", "")
            if pref_label:
                self.label_index[pref_label.lower()] = node_id

            # Alt label index
            alt_labels = node_data.get("altLabel", [])
            for alt_label in alt_labels:
                if alt_label:
                    self.alt_label_index[alt_label.lower()] = node_id

            # Notation index
            notation = node_data.get("notation")
            if notation:
                self.notation_index[notation] = node_id

        # Relation index
        self._build_relation_index()

        self.logger.info(
            f"Indexes built: {len(self.label_index)} labels, "
            f"{len(self.alt_label_index)} alt labels, "
            f"{len(self.notation_index)} notations"
        )

    def _build_relation_index(self) -> None:
        """Build relation index for fast relation lookups."""
        self.relation_index = {
            "broader": {},
            "narrower": {},
            "related": {},
            "prerequisite": {},
        }

        for source, target, edge_data in self.graph.edges(data=True):
            relation_type = edge_data.get("relation_type")
            if relation_type in self.relation_index:
                if source not in self.relation_index[relation_type]:
                    self.relation_index[relation_type][source] = []
                self.relation_index[relation_type][source].append(target)

    def find_by_label(self, label: str) -> Optional[str]:
        """
        Find concept ID by preferred label.

        Args:
            label: Preferred label (case-insensitive)

        Returns:
            Concept ID or None
        """
        return self.label_index.get(label.lower())

    def find_by_alt_label(self, alt_label: str) -> Optional[str]:
        """
        Find concept ID by alternative label.

        Args:
            alt_label: Alternative label (case-insensitive)

        Returns:
            Concept ID or None
        """
        return self.alt_label_index.get(alt_label.lower())

    def find_by_notation(self, notation: str) -> Optional[str]:
        """
        Find concept ID by notation code.

        Args:
            notation: Notation code

        Returns:
            Concept ID or None
        """
        return self.notation_index.get(notation)

    def get_related_concepts(
        self, concept_id: str, relation_type: str
    ) -> List[str]:
        """
        Get related concepts by relation type.

        Args:
            concept_id: Source concept ID
            relation_type: Type of relation (broader, narrower, related, prerequisite)

        Returns:
            List of related concept IDs
        """
        if relation_type not in self.relation_index:
            return []

        return self.relation_index[relation_type].get(concept_id, [])

    def search_by_text(self, query: str, limit: int = 10) -> List[str]:
        """
        Search concepts by text in labels and definitions.

        Args:
            query: Search query (case-insensitive)
            limit: Maximum number of results

        Returns:
            List of matching concept IDs
        """
        query_lower = query.lower()
        matches: List[tuple[str, int]] = []  # (concept_id, score)

        for node_id, node_data in self.graph.nodes(data=True):
            score = 0

            # Check preferred label
            pref_label = node_data.get("prefLabel", "").lower()
            if query_lower in pref_label:
                score += 10
                if pref_label == query_lower:
                    score += 20  # Exact match bonus

            # Check alt labels
            alt_labels = node_data.get("altLabel", [])
            for alt_label in alt_labels:
                if query_lower in alt_label.lower():
                    score += 5

            # Check definition
            definition = node_data.get("definition", "")
            if definition and query_lower in definition.lower():
                score += 3

            if score > 0:
                matches.append((node_id, score))

        # Sort by score (descending) and return top results
        matches.sort(key=lambda x: x[1], reverse=True)
        return [concept_id for concept_id, _ in matches[:limit]]

    def rebuild_indexes(self) -> None:
        """Rebuild all indexes (call after graph updates)."""
        self.label_index.clear()
        self.alt_label_index.clear()
        self.notation_index.clear()
        self.relation_index.clear()
        self._build_indexes()
