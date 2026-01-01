"""Progressive Disclosure Demo - Visualize 3-Phase Loading

This example demonstrates how Progressive Disclosure works in practice,
showing token usage and loading patterns for each phase.
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
)


def estimate_tokens(text: str) -> int:
    """Rough token estimation (1 token ≈ 4 characters)"""
    return len(text) // 4


def print_section(title: str, phase: str = ""):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    if phase:
        print(f"[{phase}] {title}")
    else:
        print(title)
    print("=" * 70)


def demo_phase1_discovery():
    """Phase 1: Discovery - Load only metadata (~100 tokens/skill)"""
    print_section("Phase 1: Discovery (Metadata Only)", "PHASE 1")

    skills_dir = Path(__file__).parent.parent.parent / "skills"

    print(f"\n📂 Scanning: {skills_dir}")
    print("⏳ Loading metadata only (not instructions or resources)...\n")

    # Phase 1: discover_skills() loads ONLY frontmatter
    skills = discover_skills(skills_dir)

    total_tokens = 0
    print(f"✅ Discovered {len(skills)} skills\n")

    for i, skill in enumerate(skills, 1):
        # Calculate approximate tokens for metadata
        metadata_text = (
            f"{skill.name} {skill.description} "
            f"{skill.license or ''} {skill.compatibility or ''} "
            f"{skill.allowed_tools or ''}"
        )
        tokens = estimate_tokens(metadata_text)
        total_tokens += tokens

        print(f"{i}. 📦 {skill.name}")
        print(f"   Description: {skill.description[:80]}...")
        print(f"   📊 Estimated tokens: ~{tokens} tokens")

        if skill.allowed_tools:
            print(f"   🔧 Allowed tools: {skill.allowed_tools}")
        if skill.compatibility:
            print(f"   ⚙️  Compatibility: {skill.compatibility}")

        print(f"   📁 Path: {skill.path}")
        print()

    print(f"💡 Phase 1 Total: ~{total_tokens} tokens for {len(skills)} skills")
    print(f"   Average: ~{total_tokens // len(skills) if skills else 0} tokens/skill")

    return skills


def demo_phase2_activation(skills):
    """Phase 2: Activation - Load instructions only when needed"""
    print_section("Phase 2: Activation (Load Instructions)", "PHASE 2")

    if not skills:
        print("⚠️  No skills available")
        return

    # Demonstrate loading instructions for first skill
    skill = skills[0]

    print(f"\n🎯 Activating skill: {skill.name}")
    print(f"📂 Skill directory: {skill.skill_dir}")
    print(f"📄 Loading instructions from: {skill.path}")
    print("⏳ Reading SKILL.md body (without re-parsing frontmatter)...\n")

    # Phase 2: read_instructions() loads ONLY the body
    instructions = read_instructions(skill.path)

    tokens = estimate_tokens(instructions)
    lines = len(instructions.split('\n'))

    print("✅ Instructions loaded!")
    print(f"   📊 Size: {len(instructions)} characters")
    print(f"   📊 Estimated tokens: ~{tokens} tokens")
    print(f"   📊 Lines: {lines}")
    print(f"\n📝 Preview (first 300 chars):")
    print("-" * 70)
    print(instructions[:300] + "...")
    print("-" * 70)

    # Show token efficiency
    print(f"\n💡 Phase 2: Loaded {tokens} tokens only when activated")
    print(f"   ✓ Metadata already loaded in Phase 1 (not reloaded)")
    print(f"   ✓ Resources NOT loaded yet (Phase 3)")

    return skill


def demo_phase3_resources(skill):
    """Phase 3: Resources - Load files only when referenced"""
    print_section("Phase 3: Resources (Load on Demand)", "PHASE 3")

    if not skill:
        print("⚠️  No skill available")
        return

    skill_dir = Path(skill.skill_dir)
    print(f"\n📂 Skill directory: {skill_dir}")
    print("🔍 Scanning for resource files...\n")

    resources_loaded = []
    total_resource_tokens = 0

    # Check scripts/
    scripts_dir = skill_dir / "scripts"
    if scripts_dir.exists() and scripts_dir.is_dir():
        print("📁 scripts/ directory found:")
        script_files = list(scripts_dir.glob("**/*.py"))

        for script in script_files[:3]:  # Load first 3 as example
            rel_path = f"scripts/{script.relative_to(scripts_dir)}"
            print(f"\n   📄 {rel_path}")
            print(f"      ⏳ Loading on-demand...")

            try:
                content = read_resource(skill.skill_dir, rel_path)
                tokens = estimate_tokens(content)
                total_resource_tokens += tokens

                print(f"      ✅ Loaded: {len(content)} chars, ~{tokens} tokens")
                print(f"      Preview: {content[:100].strip()}...")
                resources_loaded.append((rel_path, tokens))
            except Exception as e:
                print(f"      ❌ Error: {e}")

    # Check references/
    references_dir = skill_dir / "references"
    if references_dir.exists() and references_dir.is_dir():
        print("\n📁 references/ directory found:")
        ref_files = list(references_dir.glob("**/*.md"))

        for ref in ref_files[:3]:  # Load first 3 as example
            rel_path = f"references/{ref.relative_to(references_dir)}"
            print(f"\n   📄 {rel_path}")
            print(f"      ⏳ Loading on-demand...")

            try:
                content = read_resource(skill.skill_dir, rel_path)
                tokens = estimate_tokens(content)
                total_resource_tokens += tokens

                print(f"      ✅ Loaded: {len(content)} chars, ~{tokens} tokens")
                print(f"      Preview: {content[:100].strip()}...")
                resources_loaded.append((rel_path, tokens))
            except Exception as e:
                print(f"      ❌ Error: {e}")

    # Check assets/
    assets_dir = skill_dir / "assets"
    if assets_dir.exists() and assets_dir.is_dir():
        print("\n📁 assets/ directory found:")
        asset_files = list(assets_dir.glob("**/*"))

        for asset in [f for f in asset_files if f.is_file()][:3]:
            rel_path = f"assets/{asset.relative_to(assets_dir)}"
            print(f"\n   📄 {rel_path}")
            print(f"      ⏳ Loading on-demand...")

            try:
                content = read_resource(skill.skill_dir, rel_path)
                tokens = estimate_tokens(content)
                total_resource_tokens += tokens

                print(f"      ✅ Loaded: {len(content)} chars, ~{tokens} tokens")
                resources_loaded.append((rel_path, tokens))
            except Exception as e:
                print(f"      ❌ Error: {e}")

    if not resources_loaded:
        print("\n⚠️  No resource files found in this skill")
        print("   (This is fine - resources are optional)")
    else:
        print(f"\n💡 Phase 3: Loaded {len(resources_loaded)} resources")
        print(f"   Total: ~{total_resource_tokens} tokens")
        print("\n   Resources loaded:")
        for path, tokens in resources_loaded:
            print(f"   - {path}: ~{tokens} tokens")


def demo_complete_flow():
    """Show complete flow with token tracking"""
    print_section("Complete Progressive Disclosure Flow")

    print("\n🎯 Progressive Disclosure ensures:")
    print("   1. Minimal initial load (Phase 1: metadata only)")
    print("   2. Instructions loaded only when skill is activated (Phase 2)")
    print("   3. Resources loaded only when actually needed (Phase 3)")
    print("\nThis approach minimizes context usage and maximizes efficiency!\n")

    # Phase 1
    skills = demo_phase1_discovery()

    if not skills:
        print("\n⚠️  No skills found. Create skills in 'skills/' directory.")
        return

    input("\n⏸  Press Enter to continue to Phase 2...")

    # Phase 2
    skill = demo_phase2_activation(skills)

    input("\n⏸  Press Enter to continue to Phase 3...")

    # Phase 3
    demo_phase3_resources(skill)

    # Summary
    print_section("Summary: Token Usage Pattern")

    print("\n📊 Token Usage by Phase:\n")
    print("   Phase 1 (Discovery):")
    print("   └─ All skills metadata: ~100 tokens/skill")
    print("   └─ Loaded at: Agent startup")
    print("   └─ Purpose: Skill discovery and selection\n")

    print("   Phase 2 (Activation):")
    print("   └─ Single skill instructions: <5000 tokens")
    print("   └─ Loaded at: Skill activation")
    print("   └─ Purpose: Workflow guidance\n")

    print("   Phase 3 (Resources):")
    print("   └─ Individual files: varies")
    print("   └─ Loaded at: When referenced")
    print("   └─ Purpose: Detailed documentation, scripts\n")

    print("✨ This pattern ensures efficient context usage!")
    print("   - Start with minimal context (Phase 1)")
    print("   - Expand only when needed (Phase 2, 3)")
    print("   - Keep token usage under control")


def main():
    """Run Progressive Disclosure demonstration"""
    print("\n" + "🚀 " * 20)
    print(" " * 20 + "Progressive Disclosure Demo")
    print("🚀 " * 20)

    demo_complete_flow()

    print("\n" + "✅ " * 20)
    print(" " * 20 + "Demo Complete!")
    print("✅ " * 20 + "\n")


if __name__ == "__main__":
    main()
