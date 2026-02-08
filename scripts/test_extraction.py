#!/usr/bin/env python
"""Test script to verify extraction and graph building."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from obsidian_ontology_mcp.config import settings
from obsidian_ontology_mcp.extraction.skos_extractor import SKOSExtractor
from obsidian_ontology_mcp.graph.builder import KnowledgeGraphBuilder
from obsidian_ontology_mcp.graph.indexer import GraphIndexer
from obsidian_ontology_mcp.graph.query import GraphQueryEngine


def main() -> None:
    """Test extraction and graph operations."""
    print("=" * 60)
    print("Obsidian Ontology MCP Server - Test Script")
    print("=" * 60)

    # Test 1: Extract concepts
    print(f"\n1. Extracting concepts from: {settings.vault_path}")
    extractor = SKOSExtractor(settings.vault_path)
    concepts = extractor.extract_all_concepts()
    print(f"   ✓ Found {len(concepts)} concepts")

    if concepts:
        print("\n   Concepts:")
        for concept in concepts:
            print(f"   - {concept.pref_label} ({concept.concept_id})")

    # Test 2: Build graph
    print("\n2. Building knowledge graph...")
    builder = KnowledgeGraphBuilder()
    graph = builder.build_graph(concepts)
    print(f"   ✓ Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

    # Test 3: Build indexes
    print("\n3. Building indexes...")
    indexer = GraphIndexer(graph)
    print(f"   ✓ Indexed {len(indexer.label_index)} labels")

    # Test 4: Query engine
    print("\n4. Testing query engine...")
    query_engine = GraphQueryEngine(graph, indexer)

    # Test search
    print("\n   a) Search for 'machine learning':")
    results = query_engine.search_concepts("machine learning", limit=5)
    print(f"      Found {results['count']} results")
    for result in results['results']:
        print(f"      - {result['prefLabel']}")

    # Test get concept
    print("\n   b) Get concept 'regression':")
    concept = query_engine.get_concept("regression")
    if concept:
        print(f"      ✓ {concept['prefLabel']}")
        print(f"        Definition: {concept.get('definition', 'N/A')}")
        print(f"        Broader: {concept.get('broader', [])}")
        print(f"        Narrower: {concept.get('narrower', [])}")

    # Test context expansion
    print("\n   c) Expand context for 'regression' (depth=2):")
    context = query_engine.expand_context("regression", max_depth=2, include_content=False)
    if "error" not in context:
        print(f"      ✓ Focus: {context['focus_concept']['prefLabel']}")
        print(f"        Direct relations:")
        for rel_type, concepts in context['direct_relations'].items():
            if concepts:
                print(f"          {rel_type}: {[c['prefLabel'] for c in concepts]}")

    # Test path finding
    print("\n   d) Find path from 'regression' to 'machine_learning':")
    path_result = query_engine.get_concept_path("regression", "machine_learning")
    if path_result and path_result.get("path"):
        print(f"      ✓ Path length: {path_result['length']}")
        print(f"        Path: {' → '.join([c['prefLabel'] for c in path_result['path']])}")

    # Test statistics
    print("\n5. Graph statistics:")
    stats = query_engine.get_statistics()
    print(f"   Total concepts: {stats['total_concepts']}")
    print(f"   Total relations: {stats['total_relations']}")

    print("\n" + "=" * 60)
    print("✓ All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
