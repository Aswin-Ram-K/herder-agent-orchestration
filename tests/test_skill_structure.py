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

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_skill_exists():
    """SKILL.md must exist."""
    skill_path = os.path.join(SKILL_DIR, "SKILL.md")
    assert os.path.isfile(skill_path), f"SKILL.md not found at {skill_path}"
    print("  OK  SKILL.md exists")
    return skill_path


def test_frontmatter(skill_path):
    """SKILL.md must have valid YAML frontmatter with name and description."""
    with open(skill_path) as f:
        raw = f.read()

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

    if "name" not in fm:
        raise AssertionError("Frontmatter missing 'name' field")
    if "description" not in fm:
        raise AssertionError("Frontmatter missing 'description' field")

    print(f"  OK  Frontmatter: name='{fm['name']}'")
    return fm


def test_reference_files(fm):
    """All referenced reference files must exist. Returns the set of refs."""
    with open(os.path.join(SKILL_DIR, "SKILL.md")) as f:
        skill_content = f.read()

    ref_pattern = r"references/[\w-]+\.md"
    refs = set(re.findall(ref_pattern, skill_content))

    if not refs:
        raise AssertionError("No reference files found in skill. "
                           "The skill references reference files but none exist.")

    print(f"  OK  Found {len(refs)} referenced files")

    missing = []
    for ref in refs:
        ref_path = os.path.join(SKILL_DIR, ref)
        if not os.path.isfile(ref_path):
            missing.append(ref)

    if missing:
        raise AssertionError(f"Referenced files not found: {missing}")

    print("  OK  All referenced files exist")
    return refs


def test_reference_file_structure(refs):
    """Each reference file should have a heading and content."""
    for ref in sorted(refs):
        path = os.path.join(SKILL_DIR, ref)
        with open(path) as f:
            content = f.read()

        if not re.search(r"^#", content, re.MULTILINE):
            raise AssertionError(f"{ref} has no heading (must start with #)")

        if len(content.strip()) < 100:
            raise AssertionError(
                f"{ref} has suspiciously little content ({len(content)} bytes)")

        print(f"  OK  {ref}: {len(content)} bytes, has heading")


def test_no_broken_internal_links():
    """Check that Markdown links to files within the repo resolve."""
    with open(os.path.join(SKILL_DIR, "SKILL.md")) as f:
        skill_content = f.read()

    link_pattern = r"\]\(references/[\w-]+\.md\)"
    links = re.findall(link_pattern, skill_content)
    if links:
        print(f"  OK  {len(links)} internal reference links in SKILL.md")

    with open(os.path.join(SKILL_DIR, "README.md")) as f:
        readme_content = f.read()

    readme_links = re.findall(r"\]\(references/[\w-]+\.md\)", readme_content)
    if readme_links:
        print(f"  OK  {len(readme_links)} internal reference links in README.md")


def main():
    print("=" * 60)
    print("Test: Skill Structure Validation")
    print("=" * 60)

    try:
        skill_path = test_skill_exists()
        fm = test_frontmatter(skill_path)
        refs = test_reference_files(fm)
        test_reference_file_structure(refs)
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
