"""Generate skills prompt for agent system prompts

This module provides Markdown-formatted prompt generation.
"""

from typing import List
from .models import SkillProperties

SKILLS_SYSTEM_PROMPT = """
## Skills System

You have access to a skills library that provides specialized capabilities and domain knowledge.

{skills_locations}

**Available Skills:**

{skills_list}

**How to Use Skills (Progressive Disclosure):**

Skills follow a **progressive disclosure** pattern - you know they exist (name + description above), but you only read the full instructions when needed:

1. **Recognize when a skill applies**: Check if the user's task matches any skill's description
2. **Read the skill's full instructions**: Use the absolute path shown above to read SKILL.md
3. **Follow the skill's instructions**: SKILL.md contains step-by-step workflows, best practices, and examples
4. **Access supporting files**: Skills may include Python scripts, configs, or reference docs - always use absolute paths

**When to Use Skills:**
- When the user's request matches a skill's domain (e.g., "research X" → web-research skill)
- When you need specialized knowledge or structured workflows
- When a skill provides proven patterns for complex tasks

**Skills are Self-Documenting:**
- Each SKILL.md tells you exactly what the skill does and how to use it
- Read only the skills you need - this keeps your context focused and efficient

**Executing Skill Scripts:**
Skills may contain Python scripts or other executable files. Always use absolute paths from the skill list.

**Example Workflow:**

User: "Can you research the latest developments in quantum computing?"

1. Check available skills above → See "web-research" skill
2. Read the absolute path to SKILL.md shown in the list
3. Follow the skill's research workflow (search → organize → synthesize)
4. Use any helper scripts with absolute paths from the skill directory

Remember: Skills are tools to make you more capable and consistent. When in doubt, check if a skill exists for the task!
"""


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

    # Group skills by location (user vs system)
    user_skills = [s for s in skills if "/skills/" in s.path or s.path.startswith("skills/")]
    system_skills = [s for s in skills if s not in user_skills]

    # Build locations section
    locations_lines = []
    if user_skills:
        locations_lines.append("**User Skills**: Custom skills specific to your projects")
    if system_skills:
        locations_lines.append("**System Skills**: Built-in skills available globally")
    skills_locations = "\n".join(locations_lines) if locations_lines else ""

    # Build skills list
    skills_list_lines = []
    for skill in sorted(skills, key=lambda s: s.name):
        skills_list_lines.append(f"- **{skill.name}**: {skill.description}")
        skills_list_lines.append(f"  Path: `{skill.path}`")

        if skill.allowed_tools:
            skills_list_lines.append(f"  Allowed Tools: {skill.allowed_tools}")
        if skill.compatibility:
            skills_list_lines.append(f"  Requirements: {skill.compatibility}")

    skills_list = "\n".join(skills_list_lines)

    # Format the template
    return SKILLS_SYSTEM_PROMPT.format(
        skills_locations=skills_locations,
        skills_list=skills_list
    )


__all__ = ["generate_skills_prompt"]
