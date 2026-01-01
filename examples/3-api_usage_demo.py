"""API Usage Demo - Execute and show Progressive Disclosure in action

This example EXECUTES the actual API calls for each phase and shows the results.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agentskills import (
    discover_skills,
    read_metadata,
    read_instructions,
    read_resource,
    generate_skills_prompt,
    create_skill_tool,
)


def print_header(title: str, phase: str = ""):
    """Print section header"""
    print("\n" + "=" * 70)
    if phase:
        print(f"[{phase}] {title}")
    else:
        print(title)
    print("=" * 70)


def demo_phase1_discover_all():
    """Phase 1: discover_skills() - Load all skills metadata"""
    print_header("Phase 1: discover_skills()", "PHASE 1")

    print("\n💡 Function: discover_skills(skills_dir)")
    print("   Returns: List[SkillProperties]")
    print("   Purpose: Load metadata for ALL skills in directory\n")

    skills_dir = "../skills"

    print(f">>> skills = discover_skills('{skills_dir}')")
    skills = discover_skills(skills_dir)

    print(f"\n✅ Result: {len(skills)} skills discovered\n")

    for i, skill in enumerate(skills, 1):
        print(f"{i}. skill.name = '{skill.name}'")
        print(f"   skill.description = '{skill.description[:60]}...'")
        print(f"   skill.path = '{skill.path}'")
        print(f"   skill.skill_dir = '{skill.skill_dir}'")
        if skill.allowed_tools:
            print(f"   skill.allowed_tools = '{skill.allowed_tools}'")
        if skill.compatibility:
            print(f"   skill.compatibility = '{skill.compatibility}'")
        print()

    return skills


def demo_phase1_read_single():
    """Phase 1: read_metadata() - Load single skill metadata"""
    print_header("Phase 1: read_metadata()", "PHASE 1")

    print("\n💡 Function: read_metadata(skill_dir)")
    print("   Returns: SkillProperties")
    print("   Purpose: Load metadata for a SINGLE skill\n")

    skills_dir = Path(__file__).parent.parent.parent / "skills"

    # Find first directory with SKILL.md
    first_skill_dir = None
    for item in skills_dir.iterdir():
        if item.is_dir() and (item / "SKILL.md").exists():
            first_skill_dir = item
            break

    if not first_skill_dir:
        print("⚠️  No skills found")
        return None

    print(f">>> skill = read_metadata(Path('{first_skill_dir}'))")
    skill = read_metadata(first_skill_dir)

    print(f"\n✅ Result: Loaded '{skill.name}'\n")
    print(f"   name: {skill.name}")
    print(f"   description: {skill.description}")
    print(f"   path: {skill.path}")
    print(f"   skill_dir: {skill.skill_dir}")

    return skill


def demo_phase2_read_instructions(skills):
    """Phase 2: read_instructions() - Load instructions body"""
    print_header("Phase 2: read_instructions()", "PHASE 2")

    if not skills:
        print("⚠️  No skills available")
        return None

    skill = skills[0]

    print("\n💡 Function: read_instructions(skill_path)")
    print("   Returns: str (markdown body without frontmatter)")
    print("   Purpose: Load instructions when skill is ACTIVATED\n")

    print(f">>> instructions = read_instructions('{skill.path}')")
    instructions = read_instructions(skill.path)

    print(f"\n✅ Result: Loaded instructions\n")
    print(f"   Length: {len(instructions)} characters")
    print(f"   Lines: {len(instructions.split(chr(10)))}")
    print(f"   Tokens (estimate): ~{len(instructions) // 4}")

    print(f"\n📝 First 200 characters:")
    print("─" * 70)
    print(instructions[:200] + "...")
    print("─" * 70)

    return skill


def demo_phase3_read_resource(skill):
    """Phase 3: read_resource() - Load resource files"""
    print_header("Phase 3: read_resource()", "PHASE 3")

    if not skill:
        print("⚠️  No skill available")
        return

    print("\n💡 Function: read_resource(skill_dir, resource_path)")
    print("   Returns: str (file content)")
    print("   Purpose: Load resource files ON-DEMAND\n")

    skill_dir = Path(skill.skill_dir)

    # Try to find and load resources
    loaded = False

    for subdir in ["scripts", "references", "assets"]:
        resource_dir = skill_dir / subdir
        if not resource_dir.exists():
            continue

        files = [f for f in resource_dir.glob("**/*") if f.is_file()]
        if not files:
            continue

        # Load first file as example
        file = files[0]
        rel_path = f"{subdir}/{file.relative_to(resource_dir)}"

        print(f">>> content = read_resource('{skill.skill_dir}', '{rel_path}')")

        try:
            content = read_resource(skill.skill_dir, rel_path)
            loaded = True

            print(f"\n✅ Result: Loaded resource\n")
            print(f"   File: {rel_path}")
            print(f"   Length: {len(content)} characters")
            print(f"   Tokens (estimate): ~{len(content) // 4}")

            print(f"\n📝 First 150 characters:")
            print("─" * 70)
            print(content[:150] + "...")
            print("─" * 70)

            break  # Show only one example
        except Exception as e:
            print(f"⚠️  Error: {e}")

    if not loaded:
        print("⚠️  No resource files found in this skill")
        print("   (Resources are optional)")


def demo_helper_generate_prompt(skills):
    """Helper: generate_skills_prompt()"""
    print_header("Helper: generate_skills_prompt()", "HELPER")

    print("\n💡 Function: generate_skills_prompt(skills)")
    print("   Returns: str (markdown formatted prompt)")
    print("   Purpose: Generate system prompt section from skills\n")

    print(f">>> prompt = generate_skills_prompt(skills)")
    prompt = generate_skills_prompt(skills)

    print(f"\n✅ Result: Generated prompt\n")
    print(f"   Length: {len(prompt)} characters")
    print(f"   Lines: {len(prompt.split(chr(10)))}")

    print(f"\n📝 First 300 characters:")
    print("─" * 70)
    print(prompt[:300] + "...")
    print("─" * 70)


def demo_helper_create_tool(skills):
    """Helper: create_skill_tool()"""
    print_header("Helper: create_skill_tool()", "HELPER")

    print("\n💡 Function: create_skill_tool(skills, skills_dir)")
    print("   Returns: Callable (Strands @tool function)")
    print("   Purpose: Create tool for skill activation\n")

    skills_dir = Path(__file__).parent.parent.parent.parent / "skills"

    print(f">>> skill_tool = create_skill_tool(skills, '{skills_dir}')")
    skill_tool = create_skill_tool(skills, skills_dir)

    print(f"\n✅ Result: Tool created\n")
    print(f"   Function name: {skill_tool.__name__}")
    print(f"   Docstring: {skill_tool.__doc__[:100]}...")

    print("\n   Tool provides 3 actions:")
    print("   1. skill(skill_name='xxx', action='list') - List skills")
    print("   2. skill(skill_name='xxx', action='info') - Show metadata")
    print("   3. skill(skill_name='xxx', action='activate') - Load instructions")


def demo_token_comparison(skills):
    """Show token usage comparison"""
    print_header("Token Usage Comparison")

    if not skills:
        return

    print("\n📊 Progressive Disclosure Token Usage:\n")

    # Phase 1
    phase1_tokens = 0
    for skill in skills:
        metadata_text = f"{skill.name} {skill.description} {skill.allowed_tools or ''}"
        phase1_tokens += len(metadata_text) // 4

    print(f"   Phase 1 (All skills metadata): ~{phase1_tokens} tokens")

    # Phase 2
    skill = skills[0]
    instructions = read_instructions(skill.path)
    phase2_tokens = len(instructions) // 4

    print(f"   Phase 2 (1 skill instructions): ~{phase2_tokens} tokens")

    # Phase 3
    skill_dir = Path(skill.skill_dir)
    phase3_tokens = 0
    for subdir in ["scripts", "references", "assets"]:
        resource_dir = skill_dir / subdir
        if resource_dir.exists():
            files = [f for f in resource_dir.glob("**/*") if f.is_file()]
            for file in files[:2]:  # First 2 files
                try:
                    rel_path = f"{subdir}/{file.relative_to(resource_dir)}"
                    content = read_resource(skill.skill_dir, rel_path)
                    phase3_tokens += len(content) // 4
                except:
                    pass

    print(f"   Phase 3 (Resource files): ~{phase3_tokens} tokens")

    total = phase1_tokens + phase2_tokens + phase3_tokens
    print(f"\n   📊 Total (Progressive): ~{total} tokens")

    # Compare with loading everything
    all_tokens = 0
    for skill in skills:
        try:
            instructions = read_instructions(skill.path)
            all_tokens += len(instructions) // 4
        except:
            pass

    print(f"   📊 Without Progressive Disclosure: ~{all_tokens} tokens")
    print(f"   💡 Savings: ~{all_tokens - total} tokens ({100 - (total * 100 // all_tokens)}%)")


def main():
    """Run API usage demonstration"""
    print("\n" + "🔧 " * 20)
    print(" " * 20 + "Progressive Disclosure API Demo")
    print("🔧 " * 20)

    print("\nThis demo EXECUTES actual API calls and shows the results.\n")

    # Phase 1: Discovery
    print("\n" + "🔍 PHASE 1: DISCOVERY (Load Metadata Only)")
    skills = demo_phase1_discover_all()

    if not skills:
        print("\n⚠️  No skills found. Create skills in 'skills/' directory.")
        return

    input("\n⏸  Press Enter to see read_metadata() example...")
    demo_phase1_read_single()

    # Phase 2: Activation
    input("\n⏸  Press Enter to continue to Phase 2...")
    print("\n" + "⚡ PHASE 2: ACTIVATION (Load Instructions)")
    skill = demo_phase2_read_instructions(skills)

    # Phase 3: Resources
    input("\n⏸  Press Enter to continue to Phase 3...")
    print("\n" + "📦 PHASE 3: RESOURCES (Load Files On-Demand)")
    demo_phase3_read_resource(skill)

    # Helpers
    input("\n⏸  Press Enter to see helper functions...")
    print("\n" + "🛠️  HELPER FUNCTIONS")
    demo_helper_generate_prompt(skills)

    input("\n⏸  Press Enter for next helper...")
    demo_helper_create_tool(skills)

    # Token comparison
    input("\n⏸  Press Enter to see token usage comparison...")
    demo_token_comparison(skills)

    # Summary
    print_header("Summary")

    print("""
Progressive Disclosure API - 3 Phases:

Phase 1 - Discovery (Metadata):
  discover_skills(skills_dir) → List[SkillProperties]
  read_metadata(skill_dir) → SkillProperties

  ✓ Loads: name, description, path, allowed_tools
  ✓ When: Agent startup
  ✓ Cost: ~100 tokens per skill

Phase 2 - Activation (Instructions):
  read_instructions(skill_path) → str

  ✓ Loads: SKILL.md body (markdown)
  ✓ When: Skill is activated
  ✓ Cost: <5000 tokens per skill

Phase 3 - Resources (Files):
  read_resource(skill_dir, resource_path) → str

  ✓ Loads: Individual files (scripts, references, assets)
  ✓ When: File is referenced
  ✓ Cost: Varies by file size

Helper Functions:
  generate_skills_prompt(skills) → str
  create_skill_tool(skills, skills_dir) → Callable

Each phase loads progressively more content ONLY when needed!
""")

    print("✅ " * 20 + "\n")


if __name__ == "__main__":
    main()
