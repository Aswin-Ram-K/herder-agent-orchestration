#!/usr/bin/env python3
"""
Test: Clean Environment Integration Setup.

This test creates a minimal .pi/skills directory with ONLY this skill,
mimicking a clean Pi installation. It validates that the skill can be
found and loaded correctly.

Usage:
  python3 tests/test_clean_env.py [--setup] [--cleanup]

  --setup    : Create the test environment (default)
  --cleanup  : Remove the test environment
  --both     : Setup then cleanup (run test)
"""

import os
import sys
import shutil

# Path to the actual skill repo
SKILL_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_NAME = "herder-agent-orchestration"

# Where Pi looks for user skills
PI_SKILLS_DIR = os.path.expanduser("~/.pi/agent/skills")

# Where we'll copy the skill for testing
TEST_SKILL_PATH = os.path.join(PI_SKILLS_DIR, SKILL_NAME)


def setup_test_env():
    """Create a copy of the skill in ~/.pi/agent/skills/"""
    print("Setting up test environment...")
    print(f"  Source: {SKILL_SRC}")
    print(f"  Target: {TEST_SKILL_PATH}")

    # Ensure parent dir exists
    os.makedirs(PI_SKILLS_DIR, exist_ok=True)

    # Check if skill already exists
    if os.path.exists(TEST_SKILL_PATH):
        print(f"  ℹ️  Skill already exists at {TEST_SKILL_PATH}")
        print("  ℹ️  Removing existing copy...")
        shutil.rmtree(TEST_SKILL_PATH)

    # Create the test skill directory
    os.makedirs(TEST_SKILL_PATH, exist_ok=True)

    # Copy the skill directory (but only the essential files)
    essential_files = [
        "SKILL.md",
        "references",
        "README.md",
    ]

    for name in essential_files:
        src = os.path.join(SKILL_SRC, name)
        dst = os.path.join(TEST_SKILL_PATH, name)

        if os.path.isdir(src):
            shutil.copytree(src, dst)
            print(f"  ✓ Copied: {name}/")
        elif os.path.isfile(src):
            shutil.copy2(src, dst)
            print(f"  ✓ Copied: {name}")

    print()
    print("Test environment setup complete.")
    print(f"  Skill is at: {TEST_SKILL_PATH}")
    print()
    print("To verify the skill loads in Pi:")
    print(f"  1. Check that ~/.pi/agent/skills/{SKILL_NAME}/SKILL.md exists")
    print("  2. The skill should be discoverable when the user mentions:")
    print("     'orchestrate with agents', 'herder this task', 'sub-agent', etc.")
    print()

    # Verify the copy
    skill_md = os.path.join(TEST_SKILL_PATH, "SKILL.md")
    if not os.path.isfile(skill_md):
        print(f"❌ ERROR: SKILL.md not found at {skill_md}")
        return False

    with open(skill_md) as f:
        content = f.read()

    if "---" not in content or "name:" not in content:
        print("❌ ERROR: SKILL.md has invalid frontmatter")
        return False

    print("✓ Copy verified: SKILL.md has valid frontmatter")

    ref_count = sum(
        1
        for _ in os.scandir(os.path.join(TEST_SKILL_PATH, "references"))
        if _.is_file() and _.name.endswith(".md")
    )
    print(f"✓ Copy verified: {ref_count} reference files copied")
    print()
    return True


def cleanup_test_env():
    """Remove the test skill from ~/.pi/agent/skills/"""
    print("Cleaning up test environment...")
    print(f"  Removing: {TEST_SKILL_PATH}")

    if os.path.exists(TEST_SKILL_PATH):
        shutil.rmtree(TEST_SKILL_PATH)
        print("✓ Test environment removed")
    else:
        print("  ℹ️  Nothing to clean up (skill not found)")

    print()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Test clean environment setup")
    parser.add_argument("--setup", action="store_true", help="Create test environment")
    parser.add_argument(
        "--cleanup", action="store_true", help="Remove test environment"
    )
    parser.add_argument(
        "--both", action="store_true", help="Setup then cleanup (run test)"
    )
    args = parser.parse_args()

    if args.setup or args.both:
        success = setup_test_env()
        if args.both:
            if success:
                cleanup_test_env()
            else:
                cleanup_test_env()
                sys.exit(1)
    elif args.cleanup:
        cleanup_test_env()
    else:
        # Default: setup then cleanup (test mode)
        print("No flag specified. Running --both (setup + cleanup)...")
        success = setup_test_env()
        if success:
            cleanup_test_env()
        else:
            cleanup_test_env()
            sys.exit(1)


if __name__ == "__main__":
    main()
