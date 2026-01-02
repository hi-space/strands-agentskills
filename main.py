import asyncio
from pathlib import Path
from strands import Agent
from strands_tools import file_read, file_write, shell
from examples.strands_logger import StreamingLogger
from agentskills import (
    discover_skills,
    generate_skills_prompt,
    create_skill_tool,
)

def discovery(skills_dir):
    print("=" * 60)
    print("Phase 1: Discovery (Metadata Only)")
    print("=" * 60)

    skills = discover_skills(skills_dir)

    print(f"\nDiscovered {len(skills)} skills:\n")
    for skill in skills:
        print(f"📦 {skill.name}")
        print(f"   Description: {skill.description}")
        print(f"   Location: {skill.path}")
        if skill.allowed_tools:
            print(f"   Allowed tools: {skill.allowed_tools}")
        print()

    return skills


def prompt_injection(system_prompt, skills):
    print("=" * 60)
    print("Phase 2: Prompt Injection")
    print("=" * 60)

    skills_prompt = generate_skills_prompt(skills)
    full_prompt = f"{system_prompt}\n\n{skills_prompt}"
    print(full_prompt)
    return full_prompt


async def interactive_chat(agent):
    """Example: Interactive chat with agent using skills"""
    print("\n" + "=" * 60)
    print("Interactive Chat (Progressive Disclosure in Action)")
    print("=" * 60)
    print("\nCommands: 'quit', 'exit', 'q' to stop")
    
    logger = StreamingLogger()

    while True:
        user_input = input("\n👤 You: ").strip()

        if user_input.lower() in ["quit", "exit", "q"]:
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        print("\n🤖 Agent: ", end="")

        # Reset logger for new query
        logger.reset()
        async for event in agent.stream_async(user_input):
            logger.process_event(event)
        print()  # New line after response

def main():
    try:
        # 1. Discover skills (Phase 1: loads only metadata)
        skills_dir = Path(__file__).parent / "skills"
        skills = discovery(skills_dir)

        # 2. Generate system prompt with skill metadata
        system_prompt = "You are a helpful AI assistant."
        full_prompt = prompt_injection(system_prompt, skills)

        # 3. Create skill tool
        skill_tool = create_skill_tool(skills, skills_dir)

        # 4. Create agent with skill tool + file, write, shell tools
        agent = Agent(
            system_prompt=full_prompt,
            tools=[skill_tool, file_read, file_write, shell],
            model="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
        )

        asyncio.run(interactive_chat(agent))
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        return
    except Exception as e:
        print(f"\nError: {e}")
        return


if __name__ == "__main__":
    main()