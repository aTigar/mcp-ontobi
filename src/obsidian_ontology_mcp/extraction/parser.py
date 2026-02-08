"""Frontmatter parser for extracting SKOS and Schema.org metadata."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import frontmatter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ConceptMetadata(BaseModel):
    """Pydantic model for concept metadata from frontmatter."""

    # SKOS Core Properties (supports both skos:prefLabel and prefLabel formats)
    pref_label: str = Field(..., alias="prefLabel")
    alt_label: List[str] = Field(default_factory=list, alias="altLabel")
    definition: Optional[str] = None
    notation: Optional[str] = None
    in_scheme: Optional[str] = Field(default=None, alias="inScheme")

    # SKOS Relations (wikilinks)
    broader: List[str] = Field(default_factory=list)
    narrower: List[str] = Field(default_factory=list)
    related: List[str] = Field(default_factory=list)

    # Schema.org Properties
    schema_type: Optional[str] = Field(default=None, alias="type")
    identifier: Optional[str] = None
    date_created: Optional[str] = Field(default=None, alias="dateCreated")
    about: List[str] = Field(default_factory=list)
    teaches: List[str] = Field(default_factory=list)
    educational_level: Optional[str] = Field(default=None, alias="educationalLevel")
    learning_resource_type: Optional[str] = Field(
        default=None, alias="learningResourceType"
    )

    # Additional Metadata
    aliases: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    course: List[str] = Field(default_factory=list)
    lecture_week: Optional[int] = Field(default=None, alias="lectureWeek")
    prerequisite: List[str] = Field(default_factory=list)

    # File Metadata
    file_path: Optional[Path] = None
    content: Optional[str] = None

    class Config:
        """Pydantic config."""

        populate_by_name = True


class FrontmatterParser:
    """Parser for extracting SKOS metadata from markdown frontmatter."""

    def __init__(self) -> None:
        """Initialize parser."""
        self.logger = logging.getLogger(__name__)

    def parse_file(self, file_path: Path) -> Optional[ConceptMetadata]:
        """
        Parse a markdown file and extract concept metadata.

        Args:
            file_path: Path to markdown file

        Returns:
            ConceptMetadata object or None if parsing fails
        """
        try:
            # Parse frontmatter
            with open(file_path, "r", encoding="utf-8") as f:
                post = frontmatter.load(f)

            # Normalize SKOS namespace (skos:prefLabel -> prefLabel)
            metadata_dict = self._normalize_skos_keys(dict(post.metadata))

            # Check if this is a concept (must have prefLabel or skos:prefLabel)
            if "prefLabel" not in metadata_dict:
                self.logger.debug(f"Skipping {file_path.name}: no prefLabel")
                return None

            # Normalize list fields
            for field in ["altLabel", "aliases", "broader", "narrower", "related", "about", "teaches", "course", "prerequisite", "tags"]:
                if field in metadata_dict:
                    value = metadata_dict[field]
                    if isinstance(value, str):
                        # Parse wikilinks or comma-separated values
                        metadata_dict[field] = self._parse_list_field(value)
                    elif isinstance(value, list):
                        # Process list items (may contain wikilinks in strings)
                        processed = []
                        for item in value:
                            if isinstance(item, str):
                                # Extract wikilinks from string items
                                links = self.extract_wikilinks(item)
                                if links:
                                    processed.extend(links)
                                else:
                                    processed.append(item)
                            else:
                                processed.append(str(item))
                        metadata_dict[field] = processed
                    elif value is not None:
                        metadata_dict[field] = [value]

            # Normalize Schema.org @type
            if "@type" in metadata_dict:
                metadata_dict["type"] = metadata_dict.pop("@type")

            # Add file metadata
            metadata_dict["file_path"] = file_path
            metadata_dict["content"] = post.content

            # Create and validate model
            concept = ConceptMetadata(**metadata_dict)
            return concept

        except Exception as e:
            self.logger.error(f"Error parsing {file_path}: {e}")
            return None

    def _normalize_skos_keys(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize SKOS namespace keys (skos:prefLabel -> prefLabel).

        Args:
            metadata: Raw metadata dictionary

        Returns:
            Normalized metadata dictionary
        """
        normalized = {}
        for key, value in metadata.items():
            # Remove skos: prefix
            if key.startswith("skos:"):
                normalized_key = key[5:]  # Remove "skos:"
                normalized[normalized_key] = value
            else:
                normalized[key] = value
        return normalized

    def _parse_list_field(self, value: str) -> List[str]:
        """
        Parse a list field that may contain wikilinks or comma-separated values.

        Args:
            value: String value to parse

        Returns:
            List of extracted values
        """
        import re

        # Extract wikilinks: [[Note Title]] or [[Note Title|Alias]]
        wikilink_pattern = r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]"
        wikilinks = re.findall(wikilink_pattern, value)

        if wikilinks:
            return [link.strip() for link in wikilinks]

        # Fallback: comma-separated values
        return [item.strip() for item in value.split(",") if item.strip()]

    def extract_wikilinks(self, text: str) -> List[str]:
        """
        Extract all wikilinks from text.

        Args:
            text: Text containing wikilinks

        Returns:
            List of linked note titles
        """
        import re

        pattern = r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]"
        return [match.strip() for match in re.findall(pattern, text)]
