"""Complete example of using Agent Skills with Strands Agents SDK

This example demonstrates the complete Progressive Disclosure pattern:
- Phase 1: Discovery (load metadata only)
- Phase 2: Activation (load instructions on demand)
- Phase 3: Resources (load files when needed)
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from strands import Agent
from agentskills import (
    discover_skills,
    create_skill_tool,
    generate_skills_prompt,
    read_instructions,
    read_resource,
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
    """Example: Phase 2 - Activate skill and load instructions"""
    print("=" * 60)
    print("Phase 2: Activation (Load Instructions)")
    print("=" * 60)

    # Create skill tool (handles Phase 2 automatically)
    skill_tool = create_skill_tool(skills, skills_dir)

    # Create agent with skill tool
    base_prompt = "You are a helpful AI assistant with access to specialized skills."
    skills_prompt = generate_skills_prompt(skills)
    full_prompt = f"{base_prompt}\n\n{skills_prompt}"

    agent = Agent(
        system_prompt=full_prompt,
        tools=[skill_tool],
        model="anthropic.claude-3-5-sonnet-20241022-v2:0",
    )

    print("\nAsking agent: 'What skills do you have?'\n")
    response = await agent.invoke_async("What skills do you have?")
    print_response(response)

    # Manual Phase 2: Load instructions directly
    if skills:
        print("\n" + "=" * 60)
        print("Manual Phase 2: Reading instructions directly")
        print("=" * 60)
        first_skill = skills[0]
        instructions = read_instructions(first_skill.path)
        print(f"\nInstructions for '{first_skill.name}':")
        print(f"Length: {len(instructions)} chars")
        print(f"Preview: {instructions[:200]}...")

    return agent


async def example_phase3_resources(skills):
    """Example: Phase 3 - Load resource files on demand"""
    print("\n" + "=" * 60)
    print("Phase 3: Resources (Load on Demand)")
    print("=" * 60)

    if not skills:
        print("No skills available to demonstrate Phase 3")
        return

    # Find a skill with resources
    for skill in skills:
        skill_dir = Path(skill.skill_dir)

        # Check for scripts/
        scripts_dir = skill_dir / "scripts"
        if scripts_dir.exists() and scripts_dir.is_dir():
            script_files = list(scripts_dir.glob("*.py"))
            if script_files:
                print(f"\nSkill '{skill.name}' has scripts:")
                for script in script_files[:3]:  # Show first 3
                    try:
                        content = read_resource(skill.skill_dir, f"scripts/{script.name}")
                        print(f"  📄 scripts/{script.name} ({len(content)} chars)")
                    except Exception as e:
                        print(f"  ⚠️  scripts/{script.name}: {e}")

        # Check for references/
        references_dir = skill_dir / "references"
        if references_dir.exists() and references_dir.is_dir():
            ref_files = list(references_dir.glob("*"))
            if ref_files:
                print(f"\nSkill '{skill.name}' has references:")
                for ref in ref_files[:3]:  # Show first 3
                    if ref.is_file():
                        try:
                            content = read_resource(
                                skill.skill_dir, f"references/{ref.name}"
                            )
                            print(f"  📄 references/{ref.name} ({len(content)} chars)")
                        except Exception as e:
                            print(f"  ⚠️  references/{ref.name}: {e}")


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
