.PHONY: test test-structure test-content test-clean test-all install push

test: test-all

test-all: test-structure test-content test-clean

test-structure:
	@echo "=== Skill Structure Tests ==="
	@python3 tests/test_skill_structure.py
	@echo ""

test-content:
	@echo "=== Skill Content Tests ==="
	@python3 tests/test_content.py
	@echo ""

test-clean:
	@echo "=== Clean Environment Tests ==="
	@python3 tests/test_clean_env.py --both
	@echo ""

install:
	@echo "Installing skill to ~/.pi/agent/skills/..."
	@mkdir -p ~/.pi/agent/skills
	@python3 tests/test_clean_env.py --setup
	@echo ""
	@echo "Skill installed. Verify in Pi by mentioning:"
	@echo "  'orchestrate with agents', 'herder this task', 'sub-agent'"

push:
	git add -A
	git commit -m "feat: update skill and tests" || echo "No changes to commit"
	git push

check:
	@echo "Running all tests..."
	@python3 tests/test_skill_structure.py && \
	python3 tests/test_content.py && \
	python3 tests/test_clean_env.py --both && \
	echo "" && \
	echo "All checks passed."
