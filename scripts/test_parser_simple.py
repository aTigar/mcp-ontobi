#!/usr/bin/env python3
"""Simple test to verify frontmatter parsing without full dependencies."""

import re
import sys
from pathlib import Path

def extract_frontmatter(file_path):
    """Extract YAML frontmatter from markdown file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for frontmatter
    if not content.startswith('---'):
        return None
    
    # Extract frontmatter
    parts = content.split('---', 2)
    if len(parts) < 3:
        return None
    
    return parts[1].strip()

def parse_skos_field(line):
    """Parse a SKOS field line."""
    match = re.match(r'skos:(\w+):\s*(.+)', line)
    if match:
        field_name = match.group(1)
        value = match.group(2).strip()
        return field_name, value
    return None, None

def extract_wikilinks(text):
    """Extract wikilinks from text."""
    pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
    return re.findall(pattern, text)

def test_vault(vault_path):
    """Test extraction from vault."""
    vault = Path(vault_path).expanduser()
    
    if not vault.exists():
        print(f"❌ Vault not found: {vault}")
        return
    
    print("=" * 70)
    print("Obsidian Ontology MCP Server - Simple Parser Test")
    print("=" * 70)
    print(f"\n📁 Vault: {vault}")
    
    # Find all markdown files
    md_files = list(vault.rglob("*.md"))
    print(f"📄 Total markdown files: {len(md_files)}")
    
    # Parse files
    concepts = []
    for md_file in md_files:
        # Skip hidden files
        if any(part.startswith('.') for part in md_file.parts):
            continue
        
        frontmatter = extract_frontmatter(md_file)
        if not frontmatter:
            continue
        
        # Check for skos:prefLabel
        has_pref_label = False
        pref_label = None
        broader = []
        definition = None
        
        for line in frontmatter.split('\n'):
            field, value = parse_skos_field(line)
            if field == 'prefLabel':
                has_pref_label = True
                pref_label = value
            elif field == 'definition':
                definition = value
            elif field == 'broader':
                # Extract wikilinks from value
                broader = extract_wikilinks(value)
        
        if has_pref_label:
            concepts.append({
                'file': md_file.name,
                'label': pref_label,
                'definition': definition[:80] + '...' if definition and len(definition) > 80 else definition,
                'broader': broader
            })
    
    print(f"✅ Found {len(concepts)} SKOS concepts\n")
    
    # Show first 10 concepts
    print("📋 Sample Concepts:")
    print("-" * 70)
    for i, concept in enumerate(concepts[:10], 1):
        print(f"\n{i}. {concept['label']}")
        print(f"   File: {concept['file']}")
        if concept['definition']:
            print(f"   Definition: {concept['definition']}")
        if concept['broader']:
            print(f"   Broader: {', '.join(concept['broader'])}")
    
    if len(concepts) > 10:
        print(f"\n... and {len(concepts) - 10} more concepts")
    
    print("\n" + "=" * 70)
    print("✅ Parser test completed!")
    print("=" * 70)
    print("\n📝 Next steps:")
    print("   1. Install dependencies: pip install -e \".[dev]\"")
    print("   2. Run full test: python scripts/test_extraction.py")
    print("   3. Start MCP server: python scripts/run_mcp_server.py")

if __name__ == "__main__":
    vault_path = "~/projects/academic"
    test_vault(vault_path)
