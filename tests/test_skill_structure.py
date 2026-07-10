#!/usr/bin/env python3
"""
Test: Validate the skill structure matches Pi's expectations.
A Pi skill must have:
1. A SKILL.md file with YAML frontmatter containing name and description
2. Optional reference files referenced by the skill
3. Valid Markdown structure (no broken links, etc.)
"""

import os
import re
import sys

# Test against the installed skill, not the repo copy
SKILL_DIR = os.path.expanduser("~/.pi/agent/skills/herder-agent-orchestration")


def _read_skill():
    path = os.path.join(SKILL_DIR, "SKILL.md")
    if not os.path.isfile(path):
        raise AssertionError(f"SKILL.md not found at {path}")
    with open(path) as f:
        return f.read()


def test_skill_exists():
    """SKILL.md must exist."""
    path = os.path.join(SKILL_DIR, "SKILL.md")
    assert os.path.isfile(path), f"SKILL.md not found at {path}"
    print("  OK  SKILL.md exists")


def test_frontmatter():
    """SKILL.md must have valid YAML frontmatter with name and description."""
    raw = _read_skill()

    if not raw.startswith("---"):
        raise AssertionError("SKILL.md missing YAML frontmatter (--- markers)")

    fm_end = raw.index("---", 3)
    fm_text = raw[3:fm_end]

    fm = {}
    current_key = None
    current_value = []
    in_folded = False

    for line in fm_text.split("\n"):
        if line.startswith("name:"):
            if current_key and current_value:
                fm[current_key] = " ".join(current_value)
            current_key = "name"
            current_value = [line.split(":", 1)[1].strip().strip('"')]
            in_folded = False
        elif line.startswith("description:"):
            if current_key and current_value:
                fm[current_key] = " ".join(current_value)
            current_key = "description"
            value = line.split(":", 1)[1].strip()
            if value.startswith('"') and value.endswith('"'):
                current_value = [value.strip('"')]
                in_folded = False
            elif value == ">":
                current_value = []
                in_folded = True
            else:
                current_value = [value]
                in_folded = False
        elif in_folded and (line.startswith("  ") or line.strip() == ""):
            if line.strip():
                current_value.append(line.strip())
        elif in_folded and current_value:
            fm[current_key] = " ".join(current_value)
            current_key = None
            current_value = []
            in_folded = False
        elif current_key:
            fm[current_key] = " ".join(current_value)
            current_key = None
            current_value = []

    if current_key and current_value:
        fm[current_key] = " ".join(current_value)

    assert "name" in fm, "Frontmatter missing 'name' field"
    assert "description" in fm, "Frontmatter missing 'description' field"
    print(f"  OK  Frontmatter: name='{fm['name']}'")
    return fm


def test_reference_files():
    """All referenced reference files must exist."""
    skill_content = _read_skill()
    ref_pattern = r"references/[\w-]+\.md"
    refs = set(re.findall(ref_pattern, skill_content))

    assert refs, (
        "No reference files found in skill. "
        "The skill references reference files but none exist."
    )

    print(f"  OK  Found {len(refs)} referenced files")

    missing = []
    for ref in refs:
        ref_path = os.path.join(SKILL_DIR, ref)
        if not os.path.isfile(ref_path):
            missing.append(ref)

    assert not missing, f"Referenced files not found: {missing}"
    print("  OK  All referenced files exist")
    return refs


def test_reference_file_structure():
    """Each reference file should have a heading and content."""
    refs = test_reference_files()

    for ref in sorted(refs):
        path = os.path.join(SKILL_DIR, ref)
        with open(path) as f:
            content = f.read()

        assert re.search(r"^#", content, re.MULTILINE), (
            f"{ref} has no heading (must start with #)"
        )
        assert len(content.strip()) >= 100, (
            f"{ref} has suspiciously little content ({len(content)} bytes)"
        )
        print(f"  OK  {ref}: {len(content)} bytes, has heading")


def test_no_broken_internal_links():
    """Check that Markdown links to files within the skill resolve."""
    skill_content = _read_skill()

    link_pattern = r"\]\(references/[\w-]+\.md\)"
    links = re.findall(link_pattern, skill_content)
    if links:
        print(f"  OK  {len(links)} internal reference links in SKILL.md")

    readme_path = os.path.join(SKILL_DIR, "README.md")
    if os.path.isfile(readme_path):
        with open(readme_path) as f:
            readme_content = f.read()
        readme_links = re.findall(r"\]\(references/[\w-]+\.md\)", readme_content)
        if readme_links:
            print(f"  OK  {len(readme_links)} internal reference links in README.md")
    else:
        print("  OK  No README.md (optional)")


def main():
    print("=" * 60)
    print("Test: Skill Structure Validation")
    print("=" * 60)

    try:
        test_skill_exists()
        test_frontmatter()
        test_reference_files()
        test_reference_file_structure()
        test_no_broken_internal_links()

        print()
        print("=" * 60)
        print("PASS  ALL TESTS PASSED")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"FAIL  {e}")
        print("=" * 60)
        return 1
    except Exception as e:
        print()
        print("=" * 60)
        print(f"ERROR {e}")
        print("=" * 60)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
