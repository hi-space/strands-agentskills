"""Skill tools for Strands Agents

This module creates Strands tools for progressive disclosure of skills.
Supports both filesystem-based (recommended) and tool-based approaches.
"""

import logging
from pathlib import Path
from typing import List

from strands import tool

from .models import SkillProperties
from .errors import SkillNotFoundError, SkillActivationError

logger = logging.getLogger(__name__)


def create_skill_tool(skills: List[SkillProperties], skills_dir: str | Path):
    """Create a Strands tool for skill activation

    This factory function creates a tool that implements Progressive Disclosure:
    - Phase 1: Metadata in system prompt (already loaded)
    - Phase 2: Load full instructions when skill is invoked
    - Phase 3: LLM uses file_read to access resources as needed

    Args:
        skills: List of discovered skill properties
        skills_dir: Base directory containing skills

    Returns:
        A Strands tool function decorated with @tool

    Example:
        >>> from agentskills import discover_skills, create_skill_tool
        >>> from strands import Agent
        >>> from strands_tools import file_read
        >>>
        >>> skills = discover_skills("./skills")
        >>> skill_tool = create_skill_tool(skills, "./skills")
        >>>
        >>> agent = Agent(
        ...     tools=[skill_tool, file_read]
        ... )
    """
    skills_dir = Path(skills_dir).expanduser().resolve()

    # Create a lookup map for fast skill access
    skill_map = {skill.name: skill for skill in skills}

    @tool
    def skill(skill_name: str) -> str:
        """Load specialized skill instructions.

        Args:
            skill_name: Name of the skill (see system prompt for available skills)

        Returns:
            Full skill instructions with resource access information

        Example:
            skill(skill_name="web-research")
        """
        # Validate skill exists
        if skill_name not in skill_map:
            available = ", ".join(skill_map.keys())
            raise SkillNotFoundError(
                f"Skill '{skill_name}' not found. "
                f"Available skills: {available}"
            )

        skill_props = skill_map[skill_name]

        try:
            # Phase 2: Load instructions only (not frontmatter)
            from .parser import load_instructions

            instructions = load_instructions(skill_props.path)
            logger.info(f"Loaded skill: {skill_name}")

            # Build response with header and instructions
            header = (
                f"# Skill: {skill_props.name}\n\n"
                f"**Description:** {skill_props.description}\n\n"
                f"**Skill Directory:** `{skill_props.skill_dir}/`\n\n"
            )

            # Add allowed-tools reminder if specified
            if skill_props.allowed_tools:
                header += (
                    f"**IMPORTANT:** Only use these tools: `{skill_props.allowed_tools}`\n\n"
                )

            # Scan and list available resources
            skill_dir = Path(skill_props.skill_dir)
            resources = []
            for subdir in ["scripts", "references", "assets"]:
                resource_dir = skill_dir / subdir
                if resource_dir.exists() and resource_dir.is_dir():
                    for file_path in sorted(resource_dir.rglob("*")):
                        if file_path.is_file():
                            resources.append(str(file_path.absolute()))

            if resources:
                header += "**Available Resources:**\n"
                for resource in resources:
                    header += f"- `{resource}`\n"
                header += "\n"

            header += "---\n\n"
            header += "# Instructions\n\n"

            return header + instructions

        except Exception as e:
            logger.error(f"Error loading skill '{skill_name}': {e}", exc_info=True)
            raise SkillActivationError(
                f"Failed to load skill '{skill_name}': {e}"
            ) from e

    return skill


__all__ = ["create_skill_tool"]
