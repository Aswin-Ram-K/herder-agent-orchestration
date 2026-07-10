#!/usr/bin/env python3
"""
Test: Verify the IDENTIFY → VERIFY → ACT golden rule is properly embedded.

This test validates that every orchestration scenario follows the
IDENTIFY → VERIFY → ACT pattern, that new rules are enforced, and that
dangerous operations (closing workspaces, closing without verifying)
are properly guarded.
"""

import os
import re
import sys

# Test against the installed skill
SKILL_DIR = os.path.expanduser("~/.pi/agent/skills/herder-agent-orchestration")


def read_skill():
    with open(os.path.join(SKILL_DIR, "SKILL.md")) as f:
        return f.read()


# ── Part 0: Operational Discipline ──────────────────────────────────


def test_part_0_exists():
    """Part 0 — Operational Discipline must exist as a new section."""
    content = read_skill()
    if "Part 0" not in content and "Operational Discipline" not in content:
        raise AssertionError(
            "Part 0 'Operational Discipline' section is missing. "
            "The rewrite must add this before Part 1."
        )
    print("✓ Part 0 — Operational Discipline section exists")


def test_golden_rule_section():
    """THE GOLDEN RULE section must exist and define IDENTIFY → VERIFY → ACT."""
    content = read_skill()

    if "THE GOLDEN RULE" not in content:
        raise AssertionError("THE GOLDEN RULE section is missing")

    if "IDENTIFY" not in content or "VERIFY" not in content or "ACT" not in content:
        raise AssertionError(
            "THE GOLDEN RULE section must contain IDENTIFY, VERIFY, and ACT"
        )

    # Check the pattern is explicitly stated
    golden_pattern = re.search(
        r"(?:IDENTIFY|VERIFY|ACT).*(?:→|->).*VERIFY.*(?:→|->).*ACT",
        content,
        re.IGNORECASE | re.DOTALL,
    )
    if not golden_pattern:
        raise AssertionError(
            "IDENTIFY → VERIFY → ACT pattern not found in THE GOLDEN RULE section"
        )

    print("✓ THE GOLDEN RULE (IDENTIFY → VERIFY → ACT) section is complete")


def test_rule_1_always_query_before_modify():
    """Rule 1: Always Query Before You Modify — must have a table of IDENTIFY commands."""
    content = read_skill()

    if "Rule 1" not in content:
        raise AssertionError("Rule 1 is missing from Part 0")

    # Check for IDENTIFY command table
    identify_table = re.search(
        r"Operation.*\|.*IDENTIFY|IDENTIFY.*Command|Query.*Modify",
        content,
        re.IGNORECASE,
    )
    if not identify_table:
        raise AssertionError(
            "Rule 1 must include a table mapping operations to IDENTIFY commands"
        )

    print("✓ Rule 1: Always Query Before You Modify (with table)")


def test_rule_2_use_current_workspace():
    """Rule 2: Use the Current Workspace/Tab by Default."""
    content = read_skill()

    if "Rule 2" not in content:
        raise AssertionError("Rule 2 is missing from Part 0")

    # Check that the rule discourages unnecessary workspace creation
    if "new workspace" not in content.lower() or "default" not in content.lower():
        raise AssertionError(
            "Rule 2 must emphasize using the current workspace/tab by default"
        )

    print("✓ Rule 2: Use current workspace/tab by default")


def test_rule_3_never_close_workspace_mid_orchestration():
    """Rule 3: Never Close a Workspace Mid-Orchestration."""
    content = read_skill()

    if "Rule 3" not in content:
        raise AssertionError("Rule 3 is missing from Part 0")

    has_close = "close" in content.lower()
    has_workspace = "workspace" in content.lower()
    has_never = "never" in content.lower()
    if not (has_close and has_workspace and has_never):
        raise AssertionError(
            "Rule 3 must explicitly forbid closing a workspace mid-orchestration"
        )

    print("✓ Rule 3: Never close a workspace mid-orchestration")


def test_rule_4_always_use_no_focus():
    """Rule 4: Always Use --no-focus."""
    content = read_skill()

    if "Rule 4" not in content:
        raise AssertionError("Rule 4 is missing from Part 0")

    if "--no-focus" not in content:
        raise AssertionError("Rule 4 must mention --no-focus")

    print("✓ Rule 4: Always use --no-focus")


# ── Scenario-level IDENTIFY → VERIFY → ACT ──────────────────────────


def test_scenario_b_has_identify_verify():
    """Scenario B (Parallel Fan-Out) must have IDENTIFY + VERIFY before ACT."""
    content = read_skill()

    # Find Scenario B section
    scenario_b = re.search(r"### Scenario B.*?(?=### Scenario |\Z)", content, re.DOTALL)
    if not scenario_b:
        raise AssertionError("Scenario B not found")

    section = scenario_b.group(0)

    # Must have IDENTIFY, VERIFY, and ACT markers within the section
    has_identify = "IDENTIFY" in section or "identify" in section
    has_verify = "VERIFY" in section or "verify" in section
    has_act = "ACT" in section or "act" in section
    has_workspace_check = (
        "workspace list" in section
        or "workspace get" in section
        or "tab list" in section
        or "stray" in section.lower()
        or "orphan" in section.lower()
    )

    if not (has_identify and has_verify and has_act):
        raise AssertionError(
            f"Scenario B must include IDENTIFY → VERIFY → ACT pattern. "
            f"Identify={has_identify}, Verify={has_verify}, Act={has_act}"
        )

    if not has_workspace_check:
        raise AssertionError(
            "Scenario B must check workspace state before deploying panes"
        )

    print("✓ Scenario B: Parallel Fan-Out has IDENTIFY → VERIFY → ACT")


def test_scenario_d_has_pipeline_gates():
    """Scenario D (Pipeline) must gate each stage on prior completion."""
    content = read_skill()

    scenario_d = re.search(r"### Scenario D.*?(?=### Scenario |\Z)", content, re.DOTALL)
    if not scenario_d:
        raise AssertionError("Scenario D not found")

    section = scenario_d.group(0)

    # Must have agent wait (gate), read output before proceeding, and verify
    has_wait = "agent wait" in section or "wait.*--status" in section
    has_read_before_proceed = "read.*output" in section.lower() or (
        "IMPL_OUTPUT" in section or "output" in section
    )
    has_verify_output = "verify" in section.lower() or "valid" in section.lower()

    if not (has_wait and has_read_before_proceed and has_verify_output):
        raise AssertionError(
            f"Scenario D must gate each stage on prior completion. "
            f"wait={has_wait}, read_proceed={has_read_before_proceed}, verify={has_verify_output}"
        )

    print("✓ Scenario D: Pipeline has stage gating with IDENTIFY/VERIFY")


def test_scenario_c_has_cleanup_before_deploy():
    """Scenario C (Council) must clean up leftover members before starting."""
    content = read_skill()

    scenario_c = re.search(r"### Scenario C.*?(?=### Scenario |\Z)", content, re.DOTALL)
    if not scenario_c:
        raise AssertionError("Scenario C not found")

    section = scenario_c.group(0)

    # Must check for leftover council members
    has_leftover_check = (
        "leftover" in section.lower()
        or "cleanup" in section.lower()
        or "stale" in section.lower()
        or "stray" in section.lower()
    )

    if not has_leftover_check:
        raise AssertionError(
            "Scenario C must check for and clean up leftover council members before starting"
        )

    print("✓ Scenario C: Council checks for leftovers before deploying")


# ── Cleanup Safety ──────────────────────────────────────────────────


def test_cleanup_only_closes_sub_agent_panes():
    """Cleanup must only close sub-agent panes, NOT the orchestrator pane or workspace."""
    content = read_skill()

    cleanup_section = re.search(r"### 5\.3.*?(?=## |\Z)", content, re.DOTALL)
    if not cleanup_section:
        raise AssertionError("Cleanup section (5.3) not found")

    section = cleanup_section.group(0)

    # Must have explicit warning about NOT closing workspace
    has_workspace_warning = (
        "NEVER.*workspace" in section.upper()
        or "never close the workspace" in section.lower()
    )

    if not has_workspace_warning:
        raise AssertionError(
            "Cleanup section must explicitly warn against closing the workspace"
        )

    # Must mention closing only sub-agent panes
    has_sub_agent_only = (
        "sub-agent" in section.lower() or "sub agent" in section.lower()
    )

    if not has_sub_agent_only:
        raise AssertionError(
            "Cleanup must specify closing only sub-agent panes, not orchestrator"
        )

    print(
        "✓ Cleanup: Only closes sub-agent panes, never workspace or orchestrator pane"
    )


def test_never_close_workspace_mid_orchestration_in_lifecycle():
    """Orchestrator lifecycle step 7 (CLEAN) must not include workspace close."""
    content = read_skill()

    lifecycle = re.search(
        r"The Orchestrator Lifecycle.*?(?=---|\n##)", content, re.DOTALL
    )
    if not lifecycle:
        raise AssertionError("Orchestrator lifecycle not found")

    section = lifecycle.group(0)

    # STEP 7 must be about closing panes only, not workspace
    if "STEP 7" not in section and "step 7" not in section:
        raise AssertionError("Lifecycle must have a STEP 7 for cleanup")

    # If it mentions close, it should be about panes, not workspace
    close_mentions = re.findall(r"close.*\w+", section, re.IGNORECASE)
    workspace_close = [m for m in close_mentions if "workspace" in m.lower()]

    if workspace_close:
        raise AssertionError(
            f"STEP 7 must NOT include workspace close. Found: {workspace_close}"
        )

    print("✓ Lifecycle STEP 7: Cleanup closes panes only, not workspace")


# ── Design Principles — Updated ─────────────────────────────────────


def test_design_principles_include_golden_rule():
    """Design principles must include the golden rule as Rule 1."""
    content = read_skill()

    # Find the design principles section
    principles_section = re.search(
        r"(?i)^## Part 8.*?(?=^## |\Z)", content, re.DOTALL | re.MULTILINE
    )
    if not principles_section:
        raise AssertionError("Design principles section not found")

    section = principles_section.group(0)

    # Must mention IDENTIFY before act
    if "IDENTIFY" not in section:
        raise AssertionError(
            "Design principles must include the IDENTIFY → VERIFY → ACT rule"
        )

    print("✓ Design principles include the golden rule")


def test_design_principles_include_never_close_workspace():
    """Design principles must include the never-close-workspace rule."""
    content = read_skill()

    principles_section = re.search(
        r"(?i)^## Part 8.*?(?=^## |\Z)", content, re.DOTALL | re.MULTILINE
    )
    section = principles_section.group(0) if principles_section else ""

    # Must mention never close workspace (use regex, not plain 'in')
    has_never_close_ws = (
        re.search(r"never.*close.*workspace", section, re.IGNORECASE) is not None
        or re.search(r"close.*workspace.*mid", section, re.IGNORECASE) is not None
    )

    if not has_never_close_ws:
        raise AssertionError(
            "Design principles must include the 'never close workspace mid-orchestration' rule"
        )

    print("✓ Design principles include never-close-workspace rule")


# ── Quick Reference — Updated ───────────────────────────────────────


def test_quick_ref_separates_identify_from_modify():
    """Quick reference must have separate IDENTIFY and MODIFY tables."""
    content = read_skill()

    # Check for both sections
    has_identify_ref = "IDENTIFY" in content and "identify" in content.lower()
    has_modify_ref = "MODIFY" in content or "Modify" in content

    if not (has_identify_ref and has_modify_ref):
        raise AssertionError(
            f"Quick reference must have IDENTIFY and MODIFY sections. "
            f"identify_ref={has_identify_ref}, modify_ref={has_modify_ref}"
        )

    # Find the Quick Reference section (use ^## with MULTILINE to avoid ### false matches)
    quick_ref = re.search(r"^## Part 7.*?(?=^## |\Z)", content, re.DOTALL | re.MULTILINE)
    if not quick_ref:
        raise AssertionError("Part 7 — Quick Reference not found")

    section = quick_ref.group(0)

    # Must have both IDENTIFY and MODIFY subsections
    has_identify_sub = re.search(r"IDENTIFY.*Command|Query.*Modify", section, re.IGNORECASE) is not None
    has_modify_sub = re.search(r"Modify.*Command|After.*IDENTIFY.*VERIFY", section, re.IGNORECASE) is not None

    if not (has_identify_sub and has_modify_sub):
        raise AssertionError(
            f"Quick reference must separate IDENTIFY commands from MODIFY commands. "
            f"identify_sub={has_identify_sub}, modify_sub={has_modify_sub}"
        )

    print("✓ Quick reference separates IDENTIFY vs MODIFY commands")


# ── Collision Prevention ────────────────────────────────────────────


def test_collision_prevention_in_fanout():
    """Fan-out must check for collision risk before deploying."""
    content = read_skill()

    scenario_b = re.search(r"### Scenario B.*?(?=### Scenario |\Z)", content, re.DOTALL)
    if not scenario_b:
        raise AssertionError("Scenario B not found")

    section = scenario_b.group(0)

    # Must mention disjoint scopes or collision risk
    has_collision_check = (
        "collision" in section.lower()
        or "disjoint" in section.lower()
        or "overlap" in section.lower()
    )

    if not has_collision_check:
        raise AssertionError(
            "Scenario B must check for collision risk before deploying panes"
        )

    print("✓ Scenario B checks for collision risk before deploying")


# ── Orchestrator Lifecycle — Updated ────────────────────────────────


def test_lifecycle_has_7_steps():
    """Lifecycle must have 7 steps including CLEAN (after the rewrite)."""
    content = read_skill()

    lifecycle = re.search(
        r"The Orchestrator Lifecycle.*?(?=---|\n##)", content, re.DOTALL
    )
    if not lifecycle:
        raise AssertionError("Orchestrator lifecycle not found")

    section = lifecycle.group(0)

    # Must have all 7 steps
    steps = ["RECEIVE", "PLAN", "DEPLOY", "WAIT", "INTEGRATE", "REPORT", "CLEAN"]

    for step in steps:
        if step not in section:
            raise AssertionError(f"Missing lifecycle step: {step}")

    print(f"✓ Lifecycle has all {len(steps)} steps including CLEAN")


def main():
    print("=" * 60)
    print("Test: Golden Rule Verification")
    print("=" * 60)
    print()

    tests = [
        ("Part 0 — Operational Discipline", test_part_0_exists),
        ("THE GOLDEN RULE section", test_golden_rule_section),
        ("Rule 1: Always Query Before Modify", test_rule_1_always_query_before_modify),
        ("Rule 2: Use Current Workspace/Tab", test_rule_2_use_current_workspace),
        (
            "Rule 3: Never Close Workspace Mid",
            test_rule_3_never_close_workspace_mid_orchestration,
        ),
        ("Rule 4: Always Use --no-focus", test_rule_4_always_use_no_focus),
        ("Lifecycle: 7 Steps (incl CLEAN)", test_lifecycle_has_7_steps),
        ("Scenario B: IDENTIFY → VERIFY → ACT", test_scenario_b_has_identify_verify),
        ("Scenario D: Pipeline Gating", test_scenario_d_has_pipeline_gates),
        ("Scenario C: Cleanup Leftovers", test_scenario_c_has_cleanup_before_deploy),
        ("Cleanup: Sub-agent panes only", test_cleanup_only_closes_sub_agent_panes),
        (
            "Lifecycle STEP 7: No workspace close",
            test_never_close_workspace_mid_orchestration_in_lifecycle,
        ),
        ("Design Principles: Golden Rule", test_design_principles_include_golden_rule),
        (
            "Design Principles: Never Close WS",
            test_design_principles_include_never_close_workspace,
        ),
        (
            "Quick Ref: Identify vs Modify",
            test_quick_ref_separates_identify_from_modify,
        ),
        ("Scenario B: Collision Prevention", test_collision_prevention_in_fanout),
    ]

    failed = []
    for name, test_fn in tests:
        try:
            test_fn()
        except AssertionError as e:
            print(f"✗ {name}: {e}")
            failed.append(name)
        except Exception as e:
            print(f"✗ {name}: ERROR: {e}")
            import traceback

            traceback.print_exc()
            failed.append(name)

    print()
    print("=" * 60)
    if not failed:
        print("✅ ALL GOLDEN RULE TESTS PASSED")
        return 0
    else:
        print(f"❌ {len(failed)}/{len(tests)} tests FAILED:")
        for f in failed:
            print(f"   - {f}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
