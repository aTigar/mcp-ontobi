"""Graph query engine for context expansion and search."""

import logging
from collections import deque
from typing import Dict, List, Optional, Set

import networkx as nx

from .indexer import GraphIndexer

logger = logging.getLogger(__name__)


class GraphQueryEngine:
    """Query engine for knowledge graph operations."""

    def __init__(self, graph: nx.DiGraph, indexer: GraphIndexer) -> None:
        """
        Initialize query engine.

        Args:
            graph: NetworkX graph
            indexer: Graph indexer for fast lookups
        """
        self.graph = graph
        self.indexer = indexer
        self.logger = logging.getLogger(__name__)

    def get_concept(self, concept_id: str) -> Optional[Dict]:
        """
        Get concept by ID.

        Args:
            concept_id: Concept ID

        Returns:
            Concept data or None
        """
        if self.graph.has_node(concept_id):
            return dict(self.graph.nodes[concept_id])
        return None

    def expand_context(
        self,
        concept_id: str,
        relation_types: Optional[List[str]] = None,
        max_depth: int = 2,
        include_content: bool = True,
    ) -> Dict:
        """
        Expand context around a concept via graph traversal.

        Args:
            concept_id: Starting concept ID
            relation_types: Types of relations to follow (default: all)
            max_depth: Maximum traversal depth
            include_content: Include note content in results

        Returns:
            Dictionary with focus concept and related concepts
        """
        if relation_types is None:
            relation_types = ["broader", "narrower", "related"]

        # Get focus concept
        focus_concept = self.get_concept(concept_id)
        if not focus_concept:
            return {"error": f"Concept '{concept_id}' not found"}

        # BFS traversal to gather related concepts
        visited: Set[str] = {concept_id}
        direct_relations: Dict[str, List[Dict]] = {rt: [] for rt in relation_types}
        transitive_relations: Dict[str, List[Dict]] = {rt: [] for rt in relation_types}
        context_notes: List[Dict] = []

        # Queue: (current_id, depth, relation_type)
        queue: deque = deque([(concept_id, 0, None)])

        while queue:
            current_id, depth, from_relation = queue.popleft()

            if depth >= max_depth:
                continue

            # Explore each relation type
            for relation_type in relation_types:
                related_ids = self.indexer.get_related_concepts(current_id, relation_type)

                for related_id in related_ids:
                    if related_id not in visited:
                        visited.add(related_id)

                        # Get related concept data
                        related_concept = self.get_concept(related_id)
                        if not related_concept:
                            continue

                        # Build concept summary
                        concept_summary = {
                            "id": related_id,
                            "prefLabel": related_concept.get("prefLabel", ""),
                            "definition": related_concept.get("definition"),
                        }

                        # Categorize as direct or transitive
                        if depth == 0:
                            direct_relations[relation_type].append(concept_summary)
                        else:
                            transitive_relations[relation_type].append(concept_summary)

                        # Add to context notes if content requested
                        if include_content:
                            context_notes.append({
                                "id": related_id,
                                "label": related_concept.get("prefLabel", ""),
                                "content": related_concept.get("content", ""),
                                "file_path": related_concept.get("file_path", ""),
                            })

                        # Add to queue for further exploration
                        queue.append((related_id, depth + 1, relation_type))

        # Build response
        response = {
            "focus_concept": {
                "id": concept_id,
                "uri": focus_concept.get("uri", ""),
                "prefLabel": focus_concept.get("prefLabel", ""),
                "definition": focus_concept.get("definition"),
                "file_path": focus_concept.get("file_path", ""),
            },
            "direct_relations": direct_relations,
            "transitive_relations": transitive_relations,
        }

        if include_content:
            response["focus_concept"]["content"] = focus_concept.get("content", "")
            response["context_notes"] = context_notes

        return response

    def search_concepts(self, query: str, limit: int = 10) -> Dict:
        """
        Search concepts by text query.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            Dictionary with search results
        """
        # Use indexer for text search
        matching_ids = self.indexer.search_by_text(query, limit)

        results = []
        for concept_id in matching_ids:
            concept = self.get_concept(concept_id)
            if concept:
                results.append({
                    "id": concept_id,
                    "uri": concept.get("uri", ""),
                    "prefLabel": concept.get("prefLabel", ""),
                    "definition": concept.get("definition"),
                    "file_path": concept.get("file_path", ""),
                })

        return {
            "query": query,
            "count": len(results),
            "results": results,
        }

    def get_concept_path(
        self, from_concept: str, to_concept: str
    ) -> Optional[Dict]:
        """
        Find shortest path between two concepts.

        Args:
            from_concept: Source concept ID
            to_concept: Target concept ID

        Returns:
            Dictionary with path information or None
        """
        if not self.graph.has_node(from_concept):
            return {"error": f"Concept '{from_concept}' not found"}

        if not self.graph.has_node(to_concept):
            return {"error": f"Concept '{to_concept}' not found"}

        try:
            # Find shortest path (undirected)
            path = nx.shortest_path(
                self.graph.to_undirected(), from_concept, to_concept
            )

            # Build path with concept details
            path_concepts = []
            for concept_id in path:
                concept = self.get_concept(concept_id)
                if concept:
                    path_concepts.append({
                        "id": concept_id,
                        "prefLabel": concept.get("prefLabel", ""),
                    })

            return {
                "from": from_concept,
                "to": to_concept,
                "length": len(path) - 1,
                "path": path_concepts,
            }

        except nx.NetworkXNoPath:
            return {
                "from": from_concept,
                "to": to_concept,
                "path": None,
                "message": "No path found between concepts",
            }

    def get_statistics(self) -> Dict:
        """
        Get graph statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "total_concepts": self.graph.number_of_nodes(),
            "total_relations": self.graph.number_of_edges(),
        }
