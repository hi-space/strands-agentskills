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

    This factory function creates a tool that implements:
    - Single "skill" dispatcher tool (meta-tool pattern)
    - Progressive disclosure (metadata → full content on activation)
    - Three actions: list, info, activate

    Args:
        skills: List of discovered skill properties
        skills_dir: Base directory containing skills

    Returns:
        A Strands tool function decorated with @tool

    Example:
        >>> from agentskills import discover_skills, create_skill_tool
        >>> from strands import Agent
        >>>
        >>> skills = discover_skills("./skills")
        >>> skill_tool = create_skill_tool(skills, "./skills")
        >>>
        >>> agent = Agent(
        ...     tools=[skill_tool, read_tool, bash_tool]
        ... )
    """
    skills_dir = Path(skills_dir).expanduser().resolve()

    # Create a lookup map for fast skill access
    skill_map = {skill.name: skill for skill in skills}

    @tool
    def skill(
        skill_name: str,
        action: str = "instructions",
    ) -> str:
        """Access specialized agent skills with progressive disclosure

        Skills are specialized instruction sets that provide domain expertise
        and structured workflows. Use this tool to load skill content progressively.

        Args:
            skill_name: The name of the skill (from available_skills list)
            action: What to load:
                   - "info": Show metadata only (name, description, paths)
                   - "instructions" (default): Load skill instructions
                   - "list": Show all available skills

        Returns:
            For 'info': Metadata including skill directory path
            For 'instructions': Full skill instructions from SKILL.md
            For 'list': Formatted list of all available skills

        Progressive Disclosure Pattern:
            Phase 1: Metadata already in system prompt
            Phase 2: skill(skill_name="web-research", action="instructions")
            Phase 3: Use file_read to access resources in skill directory

        Example:
            1. skill(skill_name="web-research", action="instructions")
            2. Follow the instructions provided
            3. Read resources: file_read(path="/path/to/skill/scripts/helper.py")
        """
        # Handle list action
        if action == "list":
            if not skills:
                return "No skills available. Check the skills directory."

            lines = ["Available Skills:\n"]
            for s in sorted(skills, key=lambda x: x.name):
                lines.append(f"- {s.name}")
                lines.append(f"  {s.description}")
                lines.append(f"  Location: {s.path}\n")
            return "\n".join(lines)

        # Handle info action
        if action == "info":
            if skill_name not in skill_map:
                available = ", ".join(skill_map.keys())
                return (
                    f"Skill '{skill_name}' not found.\n"
                    f"Available skills: {available}"
                )

            skill_props = skill_map[skill_name]
            info_lines = [
                f"Skill: {skill_props.name}",
                f"Description: {skill_props.description}",
                f"SKILL.md: {skill_props.path}",
                f"Directory: {skill_props.skill_dir}",
            ]

            if skill_props.allowed_tools:
                info_lines.append(f"Allowed Tools: {skill_props.allowed_tools}")
            if skill_props.compatibility:
                info_lines.append(f"Compatibility: {skill_props.compatibility}")
            if skill_props.license:
                info_lines.append(f"License: {skill_props.license}")

            return "\n".join(info_lines)

        # Handle instructions action (default) - Phase 2: Load instructions
        if skill_name not in skill_map:
            available = ", ".join(skill_map.keys())
            raise SkillNotFoundError(
                f"Skill '{skill_name}' not found. "
                f"Available skills: {available}"
            )

        skill_props = skill_map[skill_name]

        try:
            # Phase 2: Load instructions only (not frontmatter)
            from .parser import read_instructions

            instructions = read_instructions(skill_props.path)
            logger.info(f"Loading instructions for skill: {skill_name}")

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

            # Add resource access hint
            header += (
                f"**Resources:** Use file_read to access scripts and references in `{skill_props.skill_dir}/`\n\n"
            )

            header += "---\n\n"
            header += "# Instructions\n\n"

            return header + instructions

        except Exception as e:
            logger.error(f"Error loading skill instructions {skill_name}: {e}", exc_info=True)
            raise SkillActivationError(
                f"Failed to load skill '{skill_name}': {e}"
            ) from e

    return skill


__all__ = ["create_skill_tool"]
