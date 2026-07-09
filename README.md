# Herder Agent Orchestration

**Agent-first multi-agent orchestration skill for herdr** — one master skill where an orchestrator agent acts as the user, manages sub-agents inside panes within the same tab, and the human observer sees everything at a glance.

## The Problem

herdr already gives you a terminal multiplexer with agent-aware panes. But the existing skills are **tool-centric**: they teach the human how to run herdr commands. They don't teach an AI agent how to **act as the user** — to spawn panes, deploy sub-agents, coordinate them, and keep the orchestrator itself in the user's line of sight.

This skill flips that: the AI agent IS the orchestrator. It opens panes, creates sub-agents, routes handoffs, monitors state, and reports back — all from within one tab the user watches.

## Key Concepts

### Tab-Internal Orchestration

```
TAB: "orchestrator"
├─ Wide pane (left) — "orchestrator" — the AI agent (Pi/claude) running this skill
├─ Pane (right) — "sub-agent-A" — e.g. codex, implementing feature
├─ Pane (right) — "sub-agent-B" — e.g. claude, reviewing code
└─ Pane (right) — "sub-agent-C" — e.g. hermes, running tests
```

The orchestrator pane stays wide and visible. Sub-agent panes sit to the right. The human sees:

- **What the orchestrator is thinking and planning** (its pane output)
- **What each sub-agent is doing** (their panes)
- **No tab-switching needed** — everything is in one tab

### The Orchestrator Pattern

```
1. HUMAN says: "Implement feature X"
2. ORCHESTRATOR breaks it into sub-tasks
3. ORCHESTRATOR opens panes for each sub-task
4. ORCHESTRATOR deploys sub-agents into those panes
5. ORCHESTRATOR monitors each sub-agent's state
6. ORCHESTRATOR routes handoffs between agents
7. ORCHESTRATOR reports the result back to the human
```

### Deployment-as-Code

The skill **is** the deployment manifest. Every orchestration scenario (single-agent, council, pipeline, fan-out, manager/workers) is a recipe in the skill. The agent reads its own instructions and executes them — no external config files needed.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        TAB: "task-name"                      │
│  ┌──────────────────┬──────────┬──────────┬───────────┐     │
│  │                  │          │          │           │     │
│  │  ORCHESTRATOR    │ SUB-A    │ SUB-B    │ SUB-C     │     │
│  │  (you, the AI)   │ (agent)  │ (agent)  │ (agent)   │     │
│  │                  │          │          │           │     │
│  │ • Plans tasks    │ • Works  │ • Works  │ • Works   │     │
│  │ • Spawns panes   │ • Reports│ • Reports│ • Reports │     │
│  │ • Routes input   │          │          │           │     │
│  │ • Monitors state │          │          │           │     │
│  │ • Integrates     │          │          │           │     │
│  └──────────────────┴──────────┴──────────┴───────────┘     │
│                                                              │
│  Human watches the whole tab. Nothing hidden in other tabs.  │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Inside herdr (HERDR_ENV=1)

The skill auto-detects herdr is active and uses herdr commands directly:

```
herder <task>
```

Says: "Set up a workspace with an orchestrator and sub-agent panes for this task."

### Outside herdr

The skill provides the same orchestration **pattern** — what to do, in what order, why. You manually run herdr commands and the skill's guidance tells you the exact sequence.

## Reference Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Master skill — all orchestration patterns in one file |
| `references/pane-orchestration.md` | Deep dive on tab-internal pane layout design |
| `references/sub-agent-design.md` | How to design, brief, and manage sub-agents |
| `references/tab-management.md` | Tab-specific orchestration patterns |
| `references/monitoring.md` | Real-time monitoring, triage, and alerting |
| `references/failure-handling.md` | What to do when things go wrong |

## Comparison with Existing Skills

| | herdr (official) | herdr-plugin | herder-agent-orchestration |
|---|---|---|---|
| **Who acts?** | Human runs herdr commands | Claude runs herdr commands via plugin | **AI agent runs herdr commands as orchestrator** |
| **View** | Human switches between tabs/panes | Same | **Human watches ONE tab, AI manages inside it** |
| **Deployment** | Human provisions panes manually | Plugin provisions panes | **Skill provisions panes as part of its orchestration** |
| **Scope** | Pane/workspace mechanics | Mechanics + some strategy | **Full orchestration: plan → deploy → monitor → integrate** |
| **Tab-internal** | N/A (human switches tabs) | N/A (human switches tabs) | **Core design: everything in one tab** |

## License

MIT
