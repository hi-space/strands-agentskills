"""Agent Skills - Simple skill system for Strands Agents SDK

This package provides a clean implementation of Agent Skills for Strands SDK
following the AgentSkills.io specification.

Core Features:
    - Progressive Disclosure: Load metadata first, full content on activation
    - Simple Integration: Works seamlessly with Strands SDK
    - Standards Compliant: Follows AgentSkills.io specification

Core Components:
    - models: SkillProperties, SkillMetadata
    - parser: SKILL.md parsing (YAML frontmatter)
    - validator: Validation against AgentSkills.io spec
    - discovery: Skill directory scanning
    - tool: Strands tool integration
    - prompt: System prompt generation
    - errors: Exception hierarchy
"""

# Core models
from .models import SkillProperties

# Parser functions
from .parser import (
    find_skill_md,
    parse_frontmatter,
    read_metadata,
    read_instructions,
    read_resource,
    read_properties,  # Backward compatibility
)

# Validator functions
from .validator import validate, validate_metadata

# Discovery
from .discovery import discover_skills

# Prompt generation
from .prompt import generate_skills_prompt

# Tool
from .tool import create_skill_tool

# Errors
from .errors import (
    SkillError,
    ParseError,
    ValidationError,
    SkillNotFoundError,
    SkillActivationError,
)

__version__ = "1.0.0"

__all__ = [
    # Models
    "SkillProperties",
    # Parser (Progressive Disclosure)
    "find_skill_md",
    "parse_frontmatter",
    "read_metadata",  # Phase 1: Load metadata only
    "read_instructions",  # Phase 2: Load instructions
    "read_resource",  # Phase 3: Load resources
    "read_properties",  # Backward compatibility (alias for read_metadata)
    # Validator
    "validate",
    "validate_metadata",
    # Discovery
    "discover_skills",
    # Prompt
    "generate_skills_prompt",
    # Tool
    "create_skill_tool",
    # Errors
    "SkillError",
    "ParseError",
    "ValidationError",
    "SkillNotFoundError",
    "SkillActivationError",
]
