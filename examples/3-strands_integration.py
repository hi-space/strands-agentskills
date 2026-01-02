"""Complete example of using Agent Skills with Strands Agents SDK

This example demonstrates the complete Progressive Disclosure pattern:
- Phase 1: Discovery (load metadata only in system prompt)
- Phase 2: LLM reads SKILL.md when needed (true progressive disclosure)
- Phase 3: LLM reads resources when needed (scripts, references)
"""

import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from strands import Agent
from strands_tools import file_read, file_write, shell
from agentskills import (
    discover_skills,
    generate_skills_prompt,
)
from strands_logger import StreamingLogger


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


async def example_phase2_activation(skills, agent):
    """Example: Phase 2 - LLM reads skills when needed (True Progressive Disclosure)"""
    print("=" * 60)
    print("Phase 2: LLM-Driven Progressive Disclosure")
    print("=" * 60)

    # Create streaming logger
    logger = StreamingLogger()

    prompt = "어떤 skill을 사용할 수 있나요?"
    print(f"\nAsking agent: '{prompt}'\n")
    
    # Use streaming to track tool calls and output chunk text
    async for event in agent.stream_async(prompt):
        logger.process_event(event)
    
    print("\n" + "=" * 60)
    
    if skills:
        first_skill = skills[0]
        prompt2 = f"{first_skill.name} skill을 어떻게 사용할 수 있나요?"
        print(f"\nAsking: {prompt2}\n")
        
        # Reset logger for new query
        logger.reset()
        
        # Use streaming to track tool calls and output chunk text
        async for event in agent.stream_async(prompt2):
            logger.process_event(event)
        
        print("\n✓ Agent read the SKILL.md only when needed (true progressive disclosure)")


async def example_phase3_resources(skills, agent):
    """Example: Phase 3 - LLM reads resource files when needed based on SKILL.md instructions"""
    print("\n" + "=" * 60)
    print("Phase 3: Resources (LLM reads on demand based on instructions)")
    print("=" * 60)

    if not skills:
        print("No skills available to demonstrate Phase 3")
        return

    # Find a skill that mentions resources in its SKILL.md instructions
    # We'll look for skills that reference scripts/ or references/ in their instructions
    skill_with_resource_mentions = None
    for skill in skills:
        skill_path = Path(skill.path)
        if not skill_path.exists():
            continue
            
        # Read SKILL.md to check if it mentions resources
        try:
            content = skill_path.read_text(encoding='utf-8')
            # Check if instructions mention scripts or references
            if 'scripts/' in content.lower() or 'references/' in content.lower():
                skill_with_resource_mentions = skill
                break
        except Exception:
            continue

    if not skill_with_resource_mentions:
        print("\nNo skills found that mention resources in their instructions")
        return

    skill_name = skill_with_resource_mentions.name
    skill_dir = Path(skill_with_resource_mentions.skill_dir)
    
    print(f"\n📦 Testing with skill: '{skill_name}'")
    print("Testing: Agent reads resources based on SKILL.md instructions")
    print("=" * 60)
    
    # Read SKILL.md to understand what resources are mentioned and how they should be used
    skill_path = Path(skill_with_resource_mentions.path)
    
    prompt = f"{skill_name} skill을 사용해서 작업을 수행해주세요. SKILL.md의 instructions에 따라 필요한 리소스 파일들을 참고해주세요."
    
    print(f"\nAsking agent: '{prompt}'\n")
    
    # Create streaming logger for this query
    logger = StreamingLogger()
    
    # Use streaming to track tool calls and output chunk text
    async for event in agent.stream_async(prompt):
        logger.process_event(event)
        
    print("\n✓ Agent should have read resource files based on SKILL.md instructions (true progressive disclosure)")


async def main():
    """Run all Progressive Disclosure examples"""
    print("\n🚀 Agent Skills with Strands SDK - Progressive Disclosure Demo\n")

    # Phase 1: Discovery
    skills, skills_dir = await example_phase1_discovery()

    if not skills:
        print("\n⚠️  No skills found. Please create skills in the 'skills/' directory.")
        return

    # Create agent with file_read tool (LLM will read SKILL.md when needed)
    base_prompt = "You are a helpful AI assistant."
    skills_prompt = generate_skills_prompt(skills)
    full_prompt = f"{base_prompt}\n\n{skills_prompt}"

    agent = Agent(
        system_prompt=full_prompt,
        tools=[file_read, file_write, shell],  # LLM uses this to read SKILL.md
        model="global.anthropic.claude-haiku-4-5-20251001-v1:0",
    )

    # Phase 2: Activation
    await example_phase2_activation(skills, agent)

    # Phase 3: Resources
    await example_phase3_resources(skills, agent)


if __name__ == "__main__":
    asyncio.run(main())
