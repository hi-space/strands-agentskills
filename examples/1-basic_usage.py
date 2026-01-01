"""Basic usage example of Agent Skills

This example shows the simplest way to use Agent Skills with Strands SDK.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from strands import Agent
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
    """Basic usage example"""

    # 1. Discover skills (Phase 1: loads only metadata)
    skills_dir = Path(__file__).parent.parent.parent / "skills"
    skills = discover_skills(skills_dir)

    print(f"Discovered {len(skills)} skills")

    if not skills:
        print("\n⚠️  No skills found. Create skills in 'skills/' directory.")
        print("Example structure:")
        print("  skills/")
        print("    web-research/")
        print("      SKILL.md")
        return

    # 2. Create skill tool
    skill_tool = create_skill_tool(skills, skills_dir)

    # 3. Generate system prompt
    base_prompt = "You are a helpful AI assistant."
    skills_prompt = generate_skills_prompt(skills)
    full_prompt = f"{base_prompt}\n\n{skills_prompt}"

    # 4. Create agent
    agent = Agent(
        system_prompt=full_prompt,
        tools=[skill_tool],
        model="anthropic.claude-3-5-sonnet-20241022-v2:0",
    )

    # 5. Use the agent
    print("\nAsking: 'What skills do you have?'\n")
    response = await agent.invoke_async("What skills do you have?")
    

if __name__ == "__main__":
    asyncio.run(main())
