# Sub-Agent Design — Briefing, Management, and Handoffs

This reference covers how to design sub-agents, what to brief them with, and how
to manage them throughout an orchestration cycle.

## Designing Sub-Tasks

### Decomposition Checklist

Before deploying sub-agents, answer these:

1. **Are the sub-tasks independent?** Can they run in parallel without colliding?
2. **Do they touch disjoint files?** If two sub-tasks edit the same file, serialize them.
3. **Can each sub-task produce a self-contained output?** Can you integrate the results?
4. **Is the scope small enough for one agent?** No sub-task should exceed what a single
   agent can complete without getting lost in context.

### Sub-Task Scoping

Each sub-agent should have:

- **A clear scope** — "You own `src/auth/` only"
- **A specific task** — "Implement login validation in src/auth/validate.ts"
- **A success criterion** — "Your work is done when the tests in src/auth/validate.test.ts pass"
- **An output contract** — "Summarize what you changed and any issues found"

### Sub-Task Examples

| Task | Sub-Task Scope | Rationale |
|------|---------------|-----------|
| "Build user auth" | Sub-A: "Implement login in src/auth/login.ts" | Disjoint files |
| "Build user auth" | Sub-B: "Implement logout in src/auth/logout.ts" | Disjoint files |
| "Build user auth" | Sub-C: "Write tests for login AND logout" | Independent of implementation |
| "Build user auth" | Sub-C: "Write tests for login AND logout" | ❌ Collision risk with Sub-A/B — serialize instead |

## Briefing Sub-Agents

### The Brief Template

Every sub-agent should receive a briefing that covers:

```
CONTEXT: [What the overall task is]
SCOPE: [What files/directories you own]
TASK: [What you need to do]
INPUT: [What to read first, what context to load]
OUTPUT: [What to produce, how to signal done]
CONSTRAINTS: [What NOT to do, what to avoid]
```

### Example Brief

```
You are an agent working on the feature "user auth".

CONTEXT: The overall task is to implement user authentication.
I'm orchestrating multiple agents on this task. You own a specific slice.

SCOPE: You only edit files under src/auth/. Do not touch anything else.
Do not modify tests or any other module.

TASK: Implement login validation in src/auth/validate.ts.
Read the existing test file src/auth/validate.test.ts first to understand
what behavior is expected, then implement it.

OUTPUT: When done, print: "LOGIN_VALIDATION_DONE" followed by a summary
of what you changed and any issues.

CONSTRAINTS: Do not create new files. Work only within src/auth/validate.ts.
Do not install dependencies. Do not modify other files.
```

### What NOT to Include in a Brief

- **Unnecessary context** — Don't paste the entire codebase. Point to files the agent
  should read itself.
- **Overlapping scope** — If sub-agent A might also touch `src/api/`, don't give it
  to sub-agent B.
- **Vague instructions** — "Fix the code" is not a brief. "Implement the validation
  function in src/auth/validate.ts to match the test expectations in src/auth/validate.test.ts" is.

## Managing Sub-Agents During Execution

### Checking Progress

Every ~30 seconds (or when the orchestrator has a free moment):

```bash
herdr agent list --json
```

This returns all agents and their states. Sort by urgency (see the master skill).

### Responding to Sub-Agent Requests

Sub-agents may ask questions or request permissions:

1. Read the agent's recent output: `herdr agent read <name> --lines 30`
2. Identify the question/request
3. Decide the answer yourself, or escalate to the human
4. Send the answer: `herdr agent send <name> "<answer>"`

### Escalation to the Human

When a sub-agent presents a problem you can't resolve:

```
I'm reviewing agent "implementer". It hit an issue I can't resolve:
[description of the issue, including the agent's output]

What should I do?
[A] [option A]
[B] [option B]
[C] [cancel the sub-task]
```

## Handoff Patterns

### Direct Handoff (Agent-to-Agent)

One sub-agent passes work to another directly:

```bash
# Agent A is done, send its output to Agent B
A_OUTPUT=$(herdr agent read implementer --lines 100)
herdr agent send reviewer "Implementer is done. Here's the output: $A_OUTPUT"
```

### Orchestrator-Mediated Handoff

The orchestrator reads both agents' output and routes between them:

```bash
# Read implementer, read reviewer, then send fixer the findings
IMPL=$(herdr agent read implementer --lines 100)
REV=$(herdr agent read reviewer --lines 50)
herdr agent send fixer "Implementer produced: [summary]. Reviewer found issues: [summary]. Fix the issues."
```

**Prefer orchestrator-mediated handoffs** when the handoff involves judgment calls
or when you want to maintain visibility of the full flow.

### Batch Handoff

When multiple sub-agents produce outputs that one sub-agent needs:

```bash
# Collect all outputs first
ALL_OUTPUTS=""
for agent in agent-a agent-b agent-c; do
  OUTPUT=$(herdr agent read "$agent" --lines 50)
  ALL_OUTPUTS="$ALL_OUTPUTS\n\n=== $agent ===\n$OUTPUT"
done

# Send to the integrator
herdr agent send integrator "All agents are done. Here are their outputs:$ALL_OUTPUTS"
```

## Sub-Agent Lifecycle

```
DEPLOY → BRIEF → WORK → done/working/blocked/unknown → INTEGRATE
   │        │        │        │
   │        │        │        └──→ If blocked: route input, re-wait
   │        │        └──→ If working: check periodically
   │        └──→ After deploy: confirm it started working
   └──→ If unknown: investigate with explain
```

## Agent Selection

### Matching Agent Types to Sub-Tasks

| Sub-Task Type | Recommended Agent | Why |
|--------------|-------------------|-----|
| Code implementation | claude / codex | Strong code generation |
| Code review | codex / hermes | Strong at finding issues |
| Testing | hermes / codex | Good at writing tests |
| Research/analysis | claude / opencode | Good at reasoning |
| Documentation | claude / opencode | Good at writing |

### Authority vs Detection

For pipeline stages you **gate on**, prefer **Authority-A agents** (agents with
lifecycle-state hooks: Pi, OpenCode). They report `working`/`blocked`/`done`
directly rather than through screen detection.

For sub-agents where you **don't gate** (you check manually), Authority-B is fine.
