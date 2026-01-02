"""Generate skills prompt for agent system prompts

This module provides XML-formatted prompt generation following the AgentSkills.io specification.
"""

from typing import List
from .models import SkillProperties


SKILLS_SYSTEM_PROMPT = """
## Skills System

You have access to a skills library that provides specialized capabilities and domain knowledge.

<skills_instructions>
**How to Use Skills:**

Skills follow a **progressive disclosure** pattern - you know they exist (name + description above), but you only read the full instructions when needed:
1. **Recognize when a skill applies**: Check if the user's task matches any skill's description
2. **Read the skill's full instructions**: 
   - **Preferred**: If a `skill` tool is available, call it with the skill name (e.g., `skill(skill_name="web-research")`)
   - **Alternative**: Use the absolute path shown above to read SKILL.md directly
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

Remember: Skills are tools to make you more capable and consistent. When in doubt, check if a skill exists for the task!
</skills_instructions>

<available_skills>
{skills_list}
</available_skills>
"""

# SKILLS_SYSTEM_PROMPT = """
# You have access to a skills library that provides specialized capabilities and domain knowledge.

# <skills_instructions>
# When users ask you to perform tasks, check if any of the available skills below can help complete the task more effectively. Skills provide specialized capabilities and domain knowledge.

# How to use skills:
# - Invoke skills using this tool with the skill name only (no arguments)
# - The skill's prompt will expand and provide detailed instructions on how to complete the task
# - Examples:
#   - \`command: "pdf"\` - invoke the pdf skill
#   - \`command: "xlsx"\` - invoke the xlsx skill
#   - \`command: "ms-office-suite:pdf"\` - invoke using fully qualified name

# Important:
# - Only use skills listed in <available_skills> below
# - Do not invoke a skill that is already running
# - Do not use this tool for built-in CLI commands (like /help, /clear, etc.)
# </skills_instructions>

# <available_skills>
# {skills_list}
# </available_skills>
# """


def generate_skills_prompt(skills: List[SkillProperties]) -> str:
    """Generate XML system prompt section from SkillProperties list

    This generates a concise prompt with skill metadata only (Phase 1 of Progressive Disclosure),
    following the AgentSkills.io specification format using XML.

    Args:
        skills: List of discovered skill properties

    Returns:
        XML formatted prompt text with <available_skills> section

    Example:
        >>> from agentskills import discover_skills, generate_skills_prompt
        >>> skills = discover_skills("./skills")
        >>> prompt = generate_skills_prompt(skills)
        >>> agent = Agent(system_prompt=base + "\\n\\n" + prompt)
    """
    if not skills:
        return ""

    # Build XML skills list (metadata only)
    skill_elements = []
    for skill in sorted(skills, key=lambda s: s.name):
        skill_xml = (
            "  <skill>\n"
            f"    <name>{skill.name}</name>\n"
            f"    <description>{skill.description}</description>\n"
            f"    <location>{skill.path}</location>\n"
            "  </skill>"
        )
        skill_elements.append(skill_xml)

    skills_list = "\n".join(skill_elements)

    # Format the template
    return SKILLS_SYSTEM_PROMPT.format(skills_list=skills_list)


__all__ = ["generate_skills_prompt"]
