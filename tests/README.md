# Test Suite

Tests for the herder-agent-orchestration skill.

## Test: Skill Structure

Validates that all required files exist and have valid structure.

```bash
python3 tests/test_skill_structure.py
```

## Test: Skill Load Simulation

Simulates loading the skill in a clean Pi environment (no herdr installed).

```bash
python3 tests/test_skill_load.py
```

## Test: Skill Content Validation

Validates that the skill references itself correctly and all cross-references are valid.

```bash
python3 tests/test_content.py
```

## Test: Clean Environment Integration

Sets up a minimal `.pi` config with only this skill and validates it loads without errors.

```bash
# Requires a clean Pi installation
python3 tests/test_clean_env.py
```
