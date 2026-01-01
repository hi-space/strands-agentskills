"""Complete example of using Agent Skills with Strands Agents SDK

This example demonstrates the complete Progressive Disclosure pattern:
- Phase 1: Discovery (load metadata only in system prompt)
- Phase 2: LLM reads SKILL.md when needed (true progressive disclosure)
- Phase 3: LLM reads resources when needed (scripts, references)
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from strands import Agent
from strands_tools import file_read
from agentskills import (
    discover_skills,
    generate_skills_prompt,
)


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


async def example_phase1_discovery():
    """Example: Phase 1 - Discover skills and load metadata only"""
    print("=" * 60)
    print("Phase 1: Discovery (Metadata Only)")
    print("=" * 60)

    # Phase 1: Load only metadata (~100 tokens per skill)
    skills_dir = Path(__file__).parent.parent / "skills"
    skills = discover_skills(skills_dir)

    print(f"\nDiscovered {len(skills)} skills:\n")
    for skill in skills:
        print(f"📦 {skill.name}")
        print(f"   Description: {skill.description}")
        print(f"   Location: {skill.path}")
        if skill.allowed_tools:
            print(f"   Allowed tools: {skill.allowed_tools}")
        print()

    return skills, skills_dir


async def example_phase2_activation(skills, skills_dir):
    """Example: Phase 2 - LLM reads skills when needed (True Progressive Disclosure)"""
    print("=" * 60)
    print("Phase 2: LLM-Driven Progressive Disclosure")
    print("=" * 60)

    # Create agent with file_read tool (LLM will read SKILL.md when needed)
    base_prompt = "You are a helpful AI assistant with access to specialized skills."
    skills_prompt = generate_skills_prompt(skills)
    full_prompt = f"{base_prompt}\n\n{skills_prompt}"

    agent = Agent(
        system_prompt=full_prompt,
        tools=[file_read],  # LLM uses this to read SKILL.md
        model="anthropic.claude-3-5-sonnet-20241022-v2:0",
    )

    print("\nAsking agent: 'What skills do you have?'\n")
    response = await agent.invoke_async("What skills do you have?")
    print_response(response)

    print("\n" + "=" * 60)
    print("Now asking agent to use a skill...")
    print("=" * 60)

    if skills:
        first_skill = skills[0]
        print(f"\nAsking: 'Can you show me how to use the {first_skill.name} skill?'\n")
        response = await agent.invoke_async(
            f"Can you show me how to use the {first_skill.name} skill?"
        )
        print_response(response)
        print("\n✓ Agent read the SKILL.md only when needed (true progressive disclosure)")

    return agent


async def example_phase3_resources(skills):
    """Example: Phase 3 - LLM reads resource files when needed"""
    print("\n" + "=" * 60)
    print("Phase 3: Resources (LLM reads on demand)")
    print("=" * 60)

    if not skills:
        print("No skills available to demonstrate Phase 3")
        return

    # Show available resources
    print("\nAvailable resources that LLM can read when needed:")
    for skill in skills:
        skill_dir = Path(skill.skill_dir)

        # Check for scripts/
        scripts_dir = skill_dir / "scripts"
        if scripts_dir.exists() and scripts_dir.is_dir():
            script_files = list(scripts_dir.glob("*.py"))
            if script_files:
                print(f"\n📦 Skill '{skill.name}' - scripts/")
                for script in script_files[:3]:  # Show first 3
                    print(f"  📄 {script}")

        # Check for references/
        references_dir = skill_dir / "references"
        if references_dir.exists() and references_dir.is_dir():
            ref_files = list(references_dir.glob("*"))
            if ref_files:
                print(f"\n📦 Skill '{skill.name}' - references/")
                for ref in ref_files[:3]:  # Show first 3
                    if ref.is_file():
                        print(f"  📄 {ref}")

    print("\n✓ LLM will read these files using file_read tool only when needed")


async def example_interactive_chat(agent):
    """Example: Interactive chat with agent using skills"""
    print("\n" + "=" * 60)
    print("Interactive Chat (Progressive Disclosure in Action)")
    print("=" * 60)
    print("\nCommands: 'quit', 'exit', 'q' to stop")
    print("Try: 'Activate the web-research skill'\n")

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                print("\nGoodbye!")
                break

            if not user_input:
                continue

            response = await agent.invoke_async(user_input)
            print("\nAgent: ", end="")
            print_response(response)

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


async def main():
    """Run all Progressive Disclosure examples"""
    print("\n🚀 Agent Skills with Strands SDK - Progressive Disclosure Demo\n")

    # Phase 1: Discovery
    skills, skills_dir = await example_phase1_discovery()

    if not skills:
        print("\n⚠️  No skills found. Please create skills in the 'skills/' directory.")
        return

    # Phase 2: Activation
    agent = await example_phase2_activation(skills, skills_dir)

    # Phase 3: Resources
    await example_phase3_resources(skills)

    # Interactive chat (optional)
    print("\n" + "=" * 60)
    response = input("\nStart interactive chat? (y/N): ").strip().lower()
    if response == "y":
        await example_interactive_chat(agent)


if __name__ == "__main__":
    asyncio.run(main())
