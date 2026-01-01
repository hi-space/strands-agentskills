"""Skill activation tool for Strands Agents

This module creates a simple Strands tool for activating skills following
the progressive disclosure pattern.
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
        action: str = "activate",
    ) -> str:
        """Activate and use specialized agent skills

        Skills are specialized instruction sets that provide domain expertise
        and structured workflows. Use this tool to activate a skill when the
        user's task matches the skill's description.

        Args:
            skill_name: The name of the skill to activate (from available_skills list)
            action: Action to perform:
                   - "activate" (default): Activate skill and load full instructions
                   - "list": Show all available skills
                   - "info": Show detailed skill metadata

        Returns:
            For 'activate': Full skill instructions from SKILL.md
            For 'list': Formatted list of all available skills
            For 'info': Detailed metadata about the requested skill

        Example:
            To use the web-research skill:
            1. skill(skill_name="web-research", action="activate")
            2. Follow the instructions provided
            3. Use only the tools specified in allowed-tools (if any)
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

        # Handle activate action (default) - Phase 2: Load instructions
        if skill_name not in skill_map:
            available = ", ".join(skill_map.keys())
            raise SkillNotFoundError(
                f"Skill '{skill_name}' not found. "
                f"Available skills: {available}"
            )

        skill_props = skill_map[skill_name]

        try:
            # Phase 2: Load instructions only (not full SKILL.md)
            from .parser import read_instructions

            instructions = read_instructions(skill_props.path)
            logger.info(f"Activating skill: {skill_name}")

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

            header += "---\n\n"
            header += "# Instructions\n\n"

            return header + instructions

        except Exception as e:
            logger.error(f"Error activating skill {skill_name}: {e}", exc_info=True)
            raise SkillActivationError(
                f"Failed to activate skill '{skill_name}': {e}"
            ) from e

    return skill


__all__ = ["create_skill_tool"]
