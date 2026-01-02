"""Basic usage example of Agent Skills

This example demonstrates the Filesystem-Based approach (recommended):
LLM directly reads SKILL.md files using the file_read tool when needed.

For Tool-Based approach, see: 2-tool_based_usage.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from strands import Agent
from strands_tools import file_read
from agentskills import discover_skills, generate_skills_prompt


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
    """Basic usage example with true progressive disclosure"""

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

    print("\n" + "=" * 60)
    print(full_prompt)
    print("\n" + "=" * 60)

    # 3. Create agent with file_read tool
    # LLM will use file_read to load SKILL.md when needed (progressive disclosure)
    agent = Agent(
        system_prompt=full_prompt,
        tools=[file_read],  # LLM reads SKILL.md on demand
        model="anthropic.claude-3-5-sonnet-20241022-v2:0",
    )

    # 4. Use the agent
    print("\n" + "=" * 60)
    print("Example 1: Asking about available skills")
    print("=" * 60)
    print("\nAsking: 'What skills do you have?'\n")
    response = await agent.invoke_async("What skills do you have?")
    print_response(response)

    # 5. Example: LLM will read SKILL.md when needed
    if skills:
        print("\n" + "=" * 60)
        print("Example 2: LLM reads skill instructions on demand")
        print("=" * 60)
        first_skill = skills[0]
        print(f"\nAsking: 'How do I use the {first_skill.name} skill?'\n")
        response = await agent.invoke_async(
            f"How do I use the {first_skill.name} skill?"
        )
        print_response(response)
    

if __name__ == "__main__":
    asyncio.run(main())
