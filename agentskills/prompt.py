"""Generate skills prompt for agent system prompts

This module provides Markdown-formatted prompt generation.
"""

from typing import List
from .models import SkillProperties

SKILLS_SYSTEM_PROMPT = """
## Available Skills

{skills_list}

**How to Use:**
1. When a task matches a skill's description, use the `skill` tool to load instructions
2. Follow the skill's instructions precisely
3. Use `file_read` to access resources in the skill directory when needed
"""


def generate_skills_prompt(skills: List[SkillProperties]) -> str:
    """Generate Markdown system prompt section from SkillProperties list

    This generates a concise prompt with skill metadata only (Phase 1 of Progressive Disclosure).

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

    # Build skills list (metadata only)
    skills_list_lines = []
    for skill in sorted(skills, key=lambda s: s.name):
        skills_list_lines.append(f"- **{skill.name}**: {skill.description}")
        skills_list_lines.append(f"  Path: `{skill.path}`")
        skills_list_lines.append(f"  Directory: `{skill.skill_dir}/`")

        if skill.allowed_tools:
            skills_list_lines.append(f"  Allowed Tools: {skill.allowed_tools}")
        if skill.compatibility:
            skills_list_lines.append(f"  Requirements: {skill.compatibility}")

    skills_list = "\n".join(skills_list_lines)

    # Format the template
    return SKILLS_SYSTEM_PROMPT.format(skills_list=skills_list)


__all__ = ["generate_skills_prompt"]
