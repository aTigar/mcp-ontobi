"""SKOS concept extractor for Obsidian vaults."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .parser import ConceptMetadata, FrontmatterParser

logger = logging.getLogger(__name__)


@dataclass
class SKOSConcept:
    """Represents a SKOS concept extracted from an Obsidian note."""

    concept_id: str
    uri: str
    pref_label: str
    alt_labels: List[str] = field(default_factory=list)
    definition: Optional[str] = None
    notation: Optional[str] = None
    in_scheme: Optional[str] = None

    # Relations (concept IDs)
    broader: List[str] = field(default_factory=list)
    narrower: List[str] = field(default_factory=list)
    related: List[str] = field(default_factory=list)

    # Schema.org
    schema_type: Optional[str] = None
    about: List[str] = field(default_factory=list)
    teaches: List[str] = field(default_factory=list)
    educational_level: Optional[str] = None
    learning_resource_type: Optional[str] = None

    # Academic
    course: List[str] = field(default_factory=list)
    lecture_week: Optional[int] = None
    prerequisite: List[str] = field(default_factory=list)

    # File metadata
    file_path: Path = field(default_factory=Path)
    content: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary for graph storage."""
        return {
            "concept_id": self.concept_id,
            "uri": self.uri,
            "prefLabel": self.pref_label,
            "altLabel": self.alt_labels,
            "definition": self.definition,
            "notation": self.notation,
            "inScheme": self.in_scheme,
            "broader": self.broader,
            "narrower": self.narrower,
            "related": self.related,
            "schema": {
                "type": self.schema_type,
                "about": self.about,
                "teaches": self.teaches,
                "educationalLevel": self.educational_level,
                "learningResourceType": self.learning_resource_type,
            },
            "academic": {
                "course": self.course,
                "lectureWeek": self.lecture_week,
                "prerequisite": self.prerequisite,
            },
            "file_path": str(self.file_path),
            "content": self.content,
        }


class SKOSExtractor:
    """Extracts SKOS concepts from an Obsidian vault."""

    def __init__(self, vault_path: Path):
        """
        Initialize extractor.

        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = vault_path
        self.parser = FrontmatterParser()
        self.logger = logging.getLogger(__name__)

    def extract_all_concepts(self) -> List[SKOSConcept]:
        """
        Extract all SKOS concepts from the vault.

        Returns:
            List of SKOSConcept objects
        """
        concepts = []
        markdown_files = list(self.vault_path.rglob("*.md"))

        self.logger.info(f"Scanning {len(markdown_files)} markdown files in vault")

        for file_path in markdown_files:
            # Skip hidden files and directories
            if any(part.startswith(".") for part in file_path.parts):
                continue

            concept = self.extract_concept(file_path)
            if concept:
                concepts.append(concept)

        self.logger.info(f"Extracted {len(concepts)} SKOS concepts")
        return concepts

    def extract_concept(self, file_path: Path) -> Optional[SKOSConcept]:
        """
        Extract a single concept from a file.

        Args:
            file_path: Path to markdown file

        Returns:
            SKOSConcept or None if not a valid concept
        """
        metadata = self.parser.parse_file(file_path)
        if not metadata:
            return None

        # Generate concept ID from file name
        concept_id = self._generate_concept_id(file_path)

        # Generate URI
        uri = f"vault://concepts#{concept_id}"

        # Resolve wikilink relations to concept IDs
        broader_ids = [self._wikilink_to_concept_id(link) for link in metadata.broader]
        narrower_ids = [self._wikilink_to_concept_id(link) for link in metadata.narrower]
        related_ids = [self._wikilink_to_concept_id(link) for link in metadata.related]
        prerequisite_ids = [self._wikilink_to_concept_id(link) for link in metadata.prerequisite]

        concept = SKOSConcept(
            concept_id=concept_id,
            uri=uri,
            pref_label=metadata.pref_label,
            alt_labels=metadata.alt_label,
            definition=metadata.definition,
            notation=metadata.notation,
            in_scheme=metadata.in_scheme,
            broader=broader_ids,
            narrower=narrower_ids,
            related=related_ids,
            schema_type=metadata.schema_type,
            about=metadata.about,
            teaches=metadata.teaches,
            educational_level=metadata.educational_level,
            learning_resource_type=metadata.learning_resource_type,
            course=metadata.course,
            lecture_week=metadata.lecture_week,
            prerequisite=prerequisite_ids,
            file_path=file_path,
            content=metadata.content or "",
        )

        return concept

    def _generate_concept_id(self, file_path: Path) -> str:
        """
        Generate concept ID from file path.

        Args:
            file_path: Path to markdown file

        Returns:
            Concept ID (lowercase, underscores)
        """
        # Use file stem (name without extension)
        name = file_path.stem
        # Convert to lowercase and replace spaces with underscores
        concept_id = name.lower().replace(" ", "_").replace("-", "_")
        return concept_id

    def _wikilink_to_concept_id(self, wikilink: str) -> str:
        """
        Convert wikilink to concept ID.

        Args:
            wikilink: Note title from wikilink

        Returns:
            Concept ID
        """
        # Convert to lowercase and replace spaces with underscores
        return wikilink.lower().replace(" ", "_").replace("-", "_")
