"""Generate skills prompt for agent system prompts

This module provides Markdown-formatted prompt generation.
"""

from typing import List
from .models import SkillProperties


def generate_skills_prompt(skills: List[SkillProperties]) -> str:
    """Generate Markdown system prompt section from SkillProperties list

    This generates a human-readable Markdown format prompt from discovered skills.

    Args:
        skills: List of discovered skill properties

    Returns:
        Markdown formatted prompt text

    Example:
        >>> from agentskills import discover_skills, generate_skills_prompt
        >>> skills = discover_skills("./skills")
        >>> prompt = generate_skills_prompt(skills)
        >>> agent = Agent(system_prompt=base + "\\n\\n" + prompt)
    """
    if not skills:
        return ""

    lines = [
        "\n## Available Skills\n",
        "You have access to specialized skills that provide domain expertise "
        "and structured workflows. Skills use **progressive disclosure** - "
        "you see their names and descriptions here, but only load full "
        "instructions when needed.\n",
    ]

    # List skills
    for skill in sorted(skills, key=lambda s: s.name):
        lines.append(f"\n### {skill.name}")
        lines.append(f"{skill.description}\n")
        lines.append(f"**Location:** `{skill.path}`")

        # Add optional metadata
        if skill.allowed_tools:
            lines.append(f"**Allowed Tools:** {skill.allowed_tools}")
        if skill.compatibility:
            lines.append(f"**Requirements:** {skill.compatibility}")

    # Usage instructions
    lines.extend([
        "\n\n**How to Use Skills:**\n",
        "1. **Recognize relevance**: Check if user's task matches a skill's description",
        "2. **Activate the skill**: Use the `skill` tool with action='activate'",
        "3. **Follow instructions**: Read and follow the workflow in SKILL.md",
        "4. **Access resources**: Use absolute paths for scripts/references in skill directory\n",
    ])

    return "\n".join(lines)


__all__ = ["generate_skills_prompt"]
