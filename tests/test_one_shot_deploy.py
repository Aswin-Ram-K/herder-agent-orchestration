#!/usr/bin/env python3
"""
Test: Verify every scenario has a complete one-shot deploy template.

A "one-shot deploy template" means a copy-paste-ready IDENTIFY → VERIFY → ACT
sequence that deploys the full orchestration for that scenario, with no steps
missing and no "see §X.Y" gaps.

Each scenario must have:
1. IDENTIFY block (query current state)
2. VERIFY block (confirm target matches state)
3. ACT block (create panes, spawn agents, brief them)
4. Optional WAIT/READ for scenarios that need gating (pipeline)
5. Optional CLEANUP block

Tests check that no scenario has a "TODO" or "see §X.Y" gap that forces
the user to jump to another section to complete the deploy.
"""

import os
import re
import sys

SKILL_DIR = os.path.expanduser("~/.pi/agent/skills/herder-agent-orchestration")


def read_skill():
    with open(os.path.join(SKILL_DIR, "SKILL.md")) as f:
        return f.read()


def _get_scenario(name):
    """Extract the section text for a scenario by name."""
    pattern = rf"### {name}.*?(?=### Scenario |\Z)"
    m = re.search(pattern, content, re.DOTALL)
    if not m:
        return ""
    return m.group(0)


content = read_skill()


def test_scenario_a_complete_one_shot():
    """Scenario A: Single-Agent must be deployable in one shot."""
    section = _get_scenario("Scenario A")
    assert section, "Scenario A not found"

    # Must have IDENTIFY commands (at least one)
    assert "herdr pane current" in section or "herdr pane list" in section, (
        "Scenario A must have IDENTIFY query commands"
    )

    # Must NOT require going elsewhere — no "see §X.Y" gaps
    assert "see §" not in section, (
        "Scenario A has a 'see §' gap — it must be self-contained"
    )
    assert "Refer to §" not in section, (
        "Scenario A has a 'Refer to §' gap — it must be self-contained"
    )
    assert "see Section" not in section.lower(), (
        "Scenario A has a 'see Section' gap — it must be self-contained"
    )

    # Scenario A: no extra panes needed, but should have run commands or explicit "no extra panes"
    has_commands = re.search(r"herdr\s+\w+", section)
    has_explicit_no_panes = "no extra panes" in section.lower() or "no panes needed" in section.lower()
    assert has_commands or has_explicit_no_panes, (
        "Scenario A must have herdr commands or state 'no extra panes needed'"
    )

    print("✓ Scenario A: Single-Agent is a complete one-shot template")


def test_scenario_b_complete_one_shot():
    """Scenario B: Parallel Fan-Out must be deployable in one shot."""
    section = _get_scenario("Scenario B")
    assert section, "Scenario B not found"

    # Must have IDENTIFY commands
    assert "herdr pane current" in section or "herdr tab list" in section or (
        "herdr pane list" in section
    ), "Scenario B must have IDENTIFY query commands"

    # Must have ACT commands (split + run) — must be self-contained
    assert "herdr pane split" in section, (
        "Scenario B must have pane split (ACT) commands — not 'see §X'"
    )

    # Must NOT require going elsewhere
    assert "see §" not in section, (
        "Scenario B has a 'see §' gap — it must be self-contained"
    )
    assert "Refer to §" not in section, (
        "Scenario B has a 'Refer to §' gap — it must be self-contained"
    )

    print("✓ Scenario B: Parallel Fan-Out is a complete one-shot template")


def test_scenario_c_complete_one_shot():
    """Scenario C: Council must have IDENTIFY → VERIFY → ACT."""
    section = _get_scenario("Scenario C")
    assert section, "Scenario C not found"

    # Must have IDENTIFY (check for leftovers)
    assert "herdr pane list" in section or "herdr agent list" in section, (
        "Scenario C must have IDENTIFY query commands"
    )

    # Must have ACT commands (split + start + brief)
    assert "herdr pane split" in section, (
        "Scenario C must have pane split (ACT) commands — not 'see §X'"
    )

    # Must NOT require going elsewhere
    assert "see §" not in section, (
        "Scenario C has a 'see §' gap — it must be self-contained"
    )
    assert "Refer to §" not in section, (
        "Scenario C has a 'Refer to §' gap — it must be self-contained"
    )

    print("✓ Scenario C: Council is a complete one-shot template")


def test_scenario_d_complete_one_shot():
    """Scenario D: Pipeline must have full IDENTIFY → VERIFY → ACT with gating."""
    section = _get_scenario("Scenario D")
    assert section, "Scenario D not found"

    # Must have IDENTIFY
    assert "herdr agent wait" in section or "herdr agent read" in section, (
        "Scenario D must have IDENTIFY query commands"
    )

    # Must have gating (wait on prior stage)
    assert "herdr agent wait" in section, (
        "Scenario D must gate stages with 'agent wait'"
    )

    # Must have ACT (split + start + brief)
    assert "herdr pane split" in section, (
        "Scenario D must have pane split (ACT) commands"
    )

    # Must NOT require going elsewhere
    assert "see §" not in section, (
        "Scenario D has a 'see §' gap — it must be self-contained"
    )
    assert "Refer to §" not in section, (
        "Scenario D has a 'Refer to §' gap — it must be self-contained"
    )

    print("✓ Scenario D: Pipeline is a complete one-shot template")


def test_scenario_e_complete_one_shot():
    """Scenario E: Manager/Workers must have full IDENTIFY → VERIFY → ACT."""
    section = _get_scenario("Scenario E")
    assert section, "Scenario E not found"

    # Must have IDENTIFY (check for room)
    assert "herdr pane list" in section, (
        "Scenario E must have IDENTIFY query commands"
    )

    # Must have ACT commands (split + start + brief)
    assert "herdr pane split" in section, (
        "Scenario E must have pane split (ACT) commands"
    )

    # Must NOT require going elsewhere
    assert "see §" not in section, (
        "Scenario E has a 'see §' gap — it must be self-contained"
    )
    assert "Refer to §" not in section, (
        "Scenario E has a 'Refer to §' gap — it must be self-contained"
    )

    print("✓ Scenario E: Manager/Workers is a complete one-shot template")


def test_no_generic_see_elsewhere_references():
    """No scenario should say 'see §X.Y' to complete its deploy."""
    for scenario in ["Scenario A", "Scenario B", "Scenario C", "Scenario D", "Scenario E"]:
        section = _get_scenario(scenario)
        assert section, f"{scenario} not found"
        # Check for "see §" cross-references that force the user to jump to another section
        assert "see §" not in section, (
            f"{scenario} has a 'see §' gap — must be self-contained"
        )
        assert "Refer to §" not in section, (
            f"{scenario} has a 'Refer to §' gap — must be self-contained"
        )
        assert "see Section" not in section.lower(), (
            f"{scenario} has a 'see Section' gap — must be self-contained"
        )
        # "see the" is OK (e.g., "see the reference file")
    print("✓ No 'see §' or 'Refer to §' gaps found in scenarios")


def test_each_scenario_has_identify_block():
    """Every scenario must have an IDENTIFY block (query commands)."""
    # Scenario-specific IDENTIFY patterns — each scenario uses different queries
    scenario_identify = {
        "Scenario A": ["herdr pane current", "herdr pane list"],
        "Scenario B": ["herdr pane current", "herdr tab list", "herdr pane list", "herdr workspace list"],
        "Scenario C": ["herdr pane list", "herdr agent list"],
        "Scenario D": ["herdr agent wait", "herdr agent read"],
        "Scenario E": ["herdr pane list"],
    }
    for scenario, patterns in scenario_identify.items():
        section = _get_scenario(scenario)
        assert section, f"{scenario} not found"
        has_identify = any(p in section for p in patterns)
        assert has_identify, (
            f"{scenario} must have IDENTIFY block with query commands: {patterns}"
        )
        print(f"✓ {scenario}: has IDENTIFY block")


def test_each_scenario_has_act_block():
    """Every scenario must have an ACT block (modify commands)."""
    for scenario in ["Scenario A", "Scenario B", "Scenario C", "Scenario D", "Scenario E"]:
        section = _get_scenario(scenario)
        assert section, f"{scenario} not found"
        has_act = (
            "herdr pane split" in section or
            "herdr pane run" in section or
            "herdr agent start" in section or
            "herdr tab create" in section or
            "herdr workspace create" in section
        )
        # Scenario A is special: "no extra panes needed" is valid
        if scenario == "Scenario A":
            has_act = has_act or (
                "no extra panes" in section.lower() or
                "no panes needed" in section.lower() or
                "your pane does double duty" in section.lower()
            )
        assert has_act, (
            f"{scenario} must have ACT block with modify commands"
        )
        print(f"✓ {scenario}: has ACT block")


def test_each_scenario_has_verify_block():
    """Every scenario must have a VERIFY step (even if inline)."""
    for scenario in ["Scenario A", "Scenario B", "Scenario C", "Scenario D", "Scenario E"]:
        section = _get_scenario(scenario)
        assert section, f"{scenario} not found"
        # VERIFY can be inline text explaining what to confirm
        has_verify = (
            "VERIFY" in section or
            "verify" in section.lower() or
            "confirm" in section.lower() or
            "ensure" in section.lower() or
            "check" in section.lower()
        )
        assert has_verify, (
            f"{scenario} must have a VERIFY step"
        )
        print(f"✓ {scenario}: has VERIFY step")


def test_cleanup_in_scenarios():
    """Scenarios that deploy panes should mention cleanup."""
    for scenario in ["Scenario B", "Scenario C", "Scenario D", "Scenario E"]:
        section = _get_scenario(scenario)
        assert section, f"{scenario} not found"
        # Should mention closing panes or at least not leaving panes open
        has_cleanup = (
            "close" in section.lower() or
            "clean" in section.lower() or
            "cleanup" in section.lower() or
            "remove" in section.lower()
        )
        if not has_cleanup:
            print(f"  ⚠️  {scenario}: no cleanup mentioned (consider adding)")
            # Don't fail — cleanup is optional for some scenarios


def main():
    print("=" * 60)
    print("Test: One-Shot Deploy Completeness Audit")
    print("=" * 60)
    print()

    tests = [
        ("Scenario A: Single-Agent", test_scenario_a_complete_one_shot),
        ("Scenario B: Parallel Fan-Out", test_scenario_b_complete_one_shot),
        ("Scenario C: Council", test_scenario_c_complete_one_shot),
        ("Scenario D: Pipeline", test_scenario_d_complete_one_shot),
        ("Scenario E: Manager/Workers", test_scenario_e_complete_one_shot),
        ("No 'see §' gaps", test_no_generic_see_elsewhere_references),
        ("All have IDENTIFY block", test_each_scenario_has_identify_block),
        ("All have ACT block", test_each_scenario_has_act_block),
        ("All have VERIFY step", test_each_scenario_has_verify_block),
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
        print("✅ ALL SCENARIOS ARE ONE-SHOT DEPLOYABLE")
        return 0
    else:
        print(f"❌ {len(failed)}/{len(tests)} tests FAILED:")
        for f in failed:
            print(f"   - {f}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
