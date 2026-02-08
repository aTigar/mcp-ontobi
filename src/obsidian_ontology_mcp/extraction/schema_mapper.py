"""Schema.org mapping utilities for SKOS concepts."""

from typing import Dict, List, Optional


class SchemaMapper:
    """Maps SKOS concepts to Schema.org types and properties."""

    # Schema.org type mappings
    TYPE_MAPPINGS = {
        "EducationalMaterial": "https://schema.org/LearningResource",
        "Course": "https://schema.org/Course",
        "Article": "https://schema.org/Article",
        "Book": "https://schema.org/Book",
    }

    # Educational level mappings
    EDUCATIONAL_LEVELS = {
        "beginner": "https://schema.org/BeginnerLevel",
        "intermediate": "https://schema.org/IntermediateLevel",
        "advanced": "https://schema.org/AdvancedLevel",
        "graduate": "https://schema.org/GraduateLevel",
        "undergraduate": "https://schema.org/UndergraduateLevel",
    }

    @classmethod
    def map_type(cls, schema_type: Optional[str]) -> Optional[str]:
        """
        Map a schema type to its Schema.org URI.

        Args:
            schema_type: Type from frontmatter

        Returns:
            Schema.org URI or None
        """
        if not schema_type:
            return None
        return cls.TYPE_MAPPINGS.get(schema_type, f"https://schema.org/{schema_type}")

    @classmethod
    def map_educational_level(cls, level: Optional[str]) -> Optional[str]:
        """
        Map educational level to Schema.org URI.

        Args:
            level: Educational level from frontmatter

        Returns:
            Schema.org URI or None
        """
        if not level:
            return None
        return cls.EDUCATIONAL_LEVELS.get(level.lower(), level)

    @classmethod
    def enrich_concept_with_schema(cls, concept_dict: Dict) -> Dict:
        """
        Enrich concept dictionary with Schema.org URIs.

        Args:
            concept_dict: Concept dictionary

        Returns:
            Enriched dictionary with Schema.org URIs
        """
        if "schema" in concept_dict and concept_dict["schema"]:
            schema = concept_dict["schema"]

            # Map type
            if schema.get("type"):
                schema["typeUri"] = cls.map_type(schema["type"])

            # Map educational level
            if schema.get("educationalLevel"):
                schema["educationalLevelUri"] = cls.map_educational_level(
                    schema["educationalLevel"]
                )

        return concept_dict
