#!/usr/bin/env python3
"""
Test: Simulate skill content validation.
Checks that the skill's internal cross-references are consistent,
that it uses proper patterns, and that all the orchestration scenarios
are complete and well-formed.
"""

import os
import re
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_file(path):
    with open(path) as f:
        return f.read()


def test_all_scenarios_present():
    """All 5 orchestration scenarios must be present."""
    skill_content = read_file(os.path.join(SKILL_DIR, "SKILL.md"))

    scenarios = [
        "Scenario A",   # Single-Agent
        "Scenario B",   # Parallel Fan-Out
        "Scenario C",   # Council
        "Scenario D",   # Pipeline / Review Chain
        "Scenario E",   # Manager / Workers
    ]

    for scenario in scenarios:
        if scenario not in skill_content:
            raise AssertionError(f"Missing scenario: {scenario}")
        print(f"✓ Found {scenario}")


def test_orchestrator_lifecycle():
    """The orchestrator lifecycle must have all 6 steps."""
    skill_content = read_file(os.path.join(SKILL_DIR, "SKILL.md"))

    steps = [
        "RECEIVE",
        "PLAN",
        "DEPLOY",
        "WAIT",
        "INTEGRATE",
        "REPORT",
    ]

    for step in steps:
        if step not in skill_content:
            raise AssertionError(f"Missing lifecycle step: {step}")
        print(f"✓ Found lifecycle step: {step}")


def test_tab_internal_focus():
    """The skill must emphasize tab-internal orchestration."""
    skill_content = read_file(os.path.join(SKILL_DIR, "SKILL.md"))

    patterns = [
        r"same tab",
        r"one tab",
        r"tab-internal",
        r"wider? pane",
        r"sub.?agent.?pane",
        r"wide.*left|left.*wide",
    ]

    found = 0
    for pattern in patterns:
        if re.search(pattern, skill_content, re.IGNORECASE):
            found += 1

    if found < 3:
        raise AssertionError(
            f"Skill doesn't sufficiently emphasize tab-internal orchestration. "
            f"Found {found}/5 tab-internal patterns."
        )

    print(f"✓ Tab-internal orchestration emphasized ({found}/5 patterns)")


def test_herdr_env_check():
    """Skill must check HERDR_ENV before operating."""
    skill_content = read_file(os.path.join(SKILL_DIR, "SKILL.md"))

    if "HERDR_ENV" not in skill_content:
        raise AssertionError("Skill must check HERDR_ENV to detect if running inside herdr")

    print("✓ HERDR_ENV check present")


def test_reference_file_consistency():
    """Reference files referenced in SKILL.md must exist and be meaningful."""
    skill_content = read_file(os.path.join(SKILL_DIR, "SKILL.md"))

    # Find all references to references/*.md
    refs = set(re.findall(r"references/([\w-]+\.md)", skill_content))

    reference_dir = os.path.join(SKILL_DIR, "references")
    existing_refs = set()
    for f in os.listdir(reference_dir):
        if f.endswith(".md"):
            existing_refs.add(f)

    # Check referenced files exist
    missing = refs - existing_refs
    if missing:
        raise AssertionError(f"Referenced files not found: {missing}")

    print(f"✓ All {len(refs)} referenced files exist")

    # Check for unreferenced reference files
    extra = existing_refs - refs
    if extra:
        print(f"  ℹ️  {len(extra)} reference file(s) not referenced in SKILL.md: {extra}")


def test_monitoring_commands():
    """Skill must include monitoring commands."""
    skill_content = read_file(os.path.join(SKILL_DIR, "SKILL.md"))

    monitoring_patterns = [
        r"herdr agent list",
        r"herdr agent read",
        r"herdr agent send",
        r"herdr agent wait",
        r"herdr agent explain",
        r"herdr notification",
    ]

    found = 0
    for pattern in monitoring_patterns:
        if re.search(pattern, skill_content):
            found += 1

    if found < 3:
        raise AssertionError(f"Skill missing monitoring commands. Found {found}/6.")

    print(f"✓ Monitoring commands present ({found}/6)")


def test_failure_handling():
    """Skill must cover failure modes."""
    skill_content = read_file(os.path.join(SKILL_DIR, "SKILL.md"))

    failure_patterns = [
        r"agent.*stuck|stuck.*agent",
        r"wrong.*state|state.*wrong",
        r"collision",
        r"timeout",
    ]

    found = 0
    for pattern in failure_patterns:
        if re.search(pattern, skill_content, re.IGNORECASE):
            found += 1

    if found < 2:
        raise AssertionError(
            f"Skill insufficiently covers failure modes. Found {found}/4."
        )

    print(f"✓ Failure handling present ({found}/4 patterns)")


def test_design_principles():
    """Skill must have design principles."""
    skill_content = read_file(os.path.join(SKILL_DIR, "SKILL.md"))

    if "design principle" in skill_content.lower() or "best practice" in skill_content.lower():
        print("✓ Design principles present")
    else:
        # Check for numbered principles (1-10)
        principles = re.findall(r"^\d+\.\s", skill_content, re.MULTILINE)
        if len(principles) >= 5:
            print(f"✓ Design principles present ({len(principles)} items)")
        else:
            print("  ℹ️  Design principles section not found (optional)")


def test_command_examples():
    """Skill must include herdr command examples."""
    skill_content = read_file(os.path.join(SKILL_DIR, "SKILL.md"))

    # Count herdr command usages
    herdr_commands = re.findall(r"herdr\s+\w+", skill_content)
    unique_commands = set(herdr_commands)

    if len(unique_commands) < 5:
        raise AssertionError(
            f"Skill has insufficient command examples. Found {len(unique_commands)} unique commands."
        )

    print(f"✓ Command examples present ({len(unique_commands)} unique commands)")


def main():
    print("=" * 60)
    print("Test: Skill Content Validation")
    print("=" * 60)

    tests = [
        test_all_scenarios_present,
        test_orchestrator_lifecycle,
        test_tab_internal_focus,
        test_herdr_env_check,
        test_reference_file_consistency,
        test_monitoring_commands,
        test_failure_handling,
        test_design_principles,
        test_command_examples,
    ]

    failed = []
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed.append(test.__name__)
        except Exception as e:
            print(f"✗ {test.__name__}: ERROR: {e}")
            failed.append(test.__name__)

    print()
    print("=" * 60)
    if not failed:
        print("✅ ALL CONTENT TESTS PASSED")
        return 0
    else:
        print(f"❌ {len(failed)} test(s) FAILED: {', '.join(failed)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
