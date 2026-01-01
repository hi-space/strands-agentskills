"""Tool-Based usage example of Agent Skills

This example demonstrates the Tool-Based approach:
LLM uses the 'skill' tool to load instructions, then file_read for resources.

For Filesystem-Based approach, see: 1-basic_usage.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from strands import Agent
from strands_tools import file_read
from agentskills import discover_skills, create_skill_tool, generate_skills_prompt


def print_response(response):
    """Helper to print Strands Agent response"""
    if hasattr(response, "content"):
        content = response.content
        if isinstance(content, list):
            for block in content:
                if hasattr(block, "text"):
                    print(block.text)
        else:
            print(content)
    else:
        print(response)


async def main():
    """Tool-based usage example with progressive disclosure"""

    # 1. Discover skills (Phase 1: loads only metadata)
    skills_dir = Path(__file__).parent.parent / "skills"
    skills = discover_skills(skills_dir)

    print(f"✓ Discovered {len(skills)} skills")
    for skill in skills:
        print(f"  - {skill.name}: {skill.description}")

    if not skills:
        print("\n⚠️  No skills found. Create skills in 'skills/' directory.")
        print("Example structure:")
        print("  skills/")
        print("    web-research/")
        print("      SKILL.md")
        return

    # 2. Generate system prompt with skill metadata
    base_prompt = "You are a helpful AI assistant."
    skills_prompt = generate_skills_prompt(skills)
    full_prompt = f"{base_prompt}\n\n{skills_prompt}"

    # 3. Create skill tool
    skill_tool = create_skill_tool(skills, skills_dir)

    # 4. Create agent with skill tool + file_read
    # Progressive Disclosure:
    # - Phase 1: Metadata in system prompt
    # - Phase 2: skill(action="instructions") loads instructions
    # - Phase 3: file_read accesses resources
    agent = Agent(
        system_prompt=full_prompt,
        tools=[skill_tool, file_read],
        model="anthropic.claude-3-5-sonnet-20241022-v2:0",
    )

    # 5. Use the agent
    print("\n" + "=" * 60)
    print("Example 1: Asking about available skills")
    print("=" * 60)
    print("\nAsking: 'What skills do you have?'\n")
    response = await agent.invoke_async("What skills do you have?")
    print_response(response)

    # 6. Example: LLM will use skill tool to load instructions
    if skills:
        print("\n" + "=" * 60)
        print("Example 2: LLM uses skill tool for instructions")
        print("=" * 60)
        first_skill = skills[0]
        print(f"\nAsking: 'How do I use the {first_skill.name} skill?'\n")
        response = await agent.invoke_async(
            f"How do I use the {first_skill.name} skill?"
        )
        print_response(response)
        print("\n✓ LLM used skill tool to load instructions (progressive disclosure)")


if __name__ == "__main__":
    asyncio.run(main())
