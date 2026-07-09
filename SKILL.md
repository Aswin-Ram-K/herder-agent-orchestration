---
name: herder-agent-orchestration
description: >
  Master skill for agent-first multi-agent orchestration. You (the AI agent)
  act as an orchestrator that manages sub-agents inside panes within the same
  tab in herdr, so the human observer sees everything at a glance. Covers the
  orchestrator pattern, tab-internal pane orchestration, deployment of
  sub-agents as part of the skill itself, council/pipeline/fan-out/manager-worker
  workflows, real-time monitoring, state-based coordination, and failure handling.
  Auto-detects herdr (HERDR_ENV=1) and uses herdr commands when inside herdr;
  otherwise provides the same orchestration patterns as manual guidance.
  Triggers: "orchestrate with agents", "set up an orchestrator", "herder this task",
  "multi-agent orchestration", "sub-agent", "agent council", "agent pipeline",
  "fan-out agents", "manager workers", "agent orchestration", "herder".
---

# Herder Agent Orchestration — Master Skill

You (the AI agent) are the **orchestrator**. Your job is to:

1. **Plan** a task into sub-tasks
2. **Deploy** sub-agents into panes within the same tab
3. **Monitor** each sub-agent's state in real time
4. **Coordinate** handoffs between agents
5. **Integrate** results and report back to the human

The human watches **one tab** that shows:

- Your orchestration reasoning (your pane, wide on the left)
- Each sub-agent's work (sub-agent panes, right side)
- Everything visible at a glance. No tab-switching.

## Prerequisite

Check `HERDR_ENV`. If it is not set, you are **not** inside herdr. You cannot inspect or
control panes. Say so, stop, and offer manual guidance using the patterns below.

```
If HERDR_ENV is not set → "I'm outside herdr. I can't manage panes, but here's
exactly what to run to set up this orchestration pattern:"
```

When `HERDR_ENV` is set, proceed. All commands below use the herdr CLI.
Confirm exact spellings live when in doubt (`herdr --help`, `herdr workspace --help`, etc.).

---

## Part 1 — The Orchestrator Pattern

### Mental Model

```
TAB: "<task-name>"
┌──────────────────────┬────────────┬────────────┬────────────┐
│                      │            │            │            │
│  ORCHESTRATOR        │ SUB-A      │ SUB-B      │ SUB-C      │
│  (you, the AI)       │ (agent)    │ (agent)    │ (agent)    │
│                      │            │            │            │
│ • Plans              │ • Works    │ • Works    │ • Works    │
│ • Spawns panes       │ • Reports  │ • Reports  │ • Reports  │
│ • Routes input       │            │            │            │
│ • Monitors           │            │            │            │
│ • Integrates         │            │            │            │
│                      │            │            │            │
│ (wide)               │ (narrow)   │ (narrow)   │ (narrow)   │
│                      │            │            │            │
└──────────────────────┴────────────┴────────────┴────────────┘
```

**Key principle:** Your pane stays wide (roughly 30–40% of tab width). Sub-agent panes
share the remaining space. This ensures the human can always see your reasoning and
planning alongside every sub-agent's output.

### The Orchestrator Lifecycle

```
STEP 1: RECEIVE — Parse the human's task
STEP 2: PLAN   — Decompose into sub-tasks, assign sub-agents
STEP 3: DEPLOY — Create panes, spawn sub-agents, brief them
STEP 4: WAIT   — Monitor sub-agent states, route handoffs
STEP 5: INTEGRATE — Collect outputs, synthesize results
STEP 6: REPORT — Present results to the human
```

---

## Part 2 — Tab-Internal Pane Orchestration

### 2.1 Setting Up the Orchestrator Tab

When you receive a task, the first thing you do is create (or confirm the existence of)
a workspace and tab for orchestration.

**If workspace doesn't exist:**

```bash
herdr workspace create --cwd /path/to/project --label "<task-name>" --no-focus
```

**Create the orchestration tab:**

```bash
herdr tab create --workspace <workspace-id> --label "orchestrator" --no-focus
```

**Focus it:**

```bash
herdr tab focus <workspace-id>:<tab-id>
```

At this point, you are the orchestrator — running in a pane in this tab.

### 2.2 Spawning Sub-Agent Panes (Right of You)

For each sub-task, you create a pane **to the right** of your current pane, then deploy
a sub-agent into it.

**For a single sub-agent:**

```bash
# Split right from your pane
SUB_PANE=$(herdr pane split <your-pane-id> --direction right --no-focus \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')

# Brief the sub-agent
herdr pane run "$SUB_PANE" "<sub-agent-command>"
```

**For multiple sub-agents (parallel fan-out):**

```bash
# Split right
A_PANE=$(herdr pane split <your-pane-id> --direction right --no-focus \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')
herdr pane run "$A_PANE" "<agent-a-command> --task '<task-a>'"

# Split right again (this goes right of the first split, not yours)
B_PANE=$(herdr pane split $A_PANE --direction right --no-focus \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')
herdr pane run "$B_PANE" "<agent-b-command> --task '<task-b>'"

# Split right again
C_PANE=$(herdr pane split $B_PANE --direction right --no-focus \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')
herdr pane run "$C_PANE" "<agent-c-command> --task '<task-c>'"
```

> **Note:** Each successive `--direction right` splits off the rightmost pane created,
> not your original pane. To create all panes directly from yours, track your pane's
> ID and split from it each time, using the pane's right neighbor as the pivot:
>
> ```bash
> # Better: all panes directly right of yours
> PANE_A=$(herdr pane split <your-pane-id> --direction right --no-focus ...)
> PANE_B=$(herdr pane split <your-pane-id> --direction right --no-focus ...)  # pushes A left
> PANE_C=$(herdr pane split <your-pane-id> --direction right --no-focus ...)  # pushes A,B left
> ```
>
> This keeps all sub-agent panes at the same level, all right of you.

### 2.3 Naming Sub-Agents

Always give each sub-agent a name. Pane IDs compact; agent names are durable.

```bash
herdr agent start <pane-id> --name "<agent-label>" --session "<session-id>"
```

Named agents can be:

- Read by name: `herdr agent read <name> --lines 50`
- Sent input by name: `herdr agent send <name> "<message>"`
- Waited on by state: `herdr agent wait <name> --status done --timeout 120000`

### 2.4 Pane Sizing

Your orchestrator pane should be wide enough for the human to read your reasoning.
After creating sub-agent panes, resize if needed:

```bash
# Give yourself more space (adjust ratio as needed)
herdr pane resize <your-pane-id> --ratio 0.35
```

Rule of thumb: your pane gets ~35-40% of the tab width. Sub-agents share the rest.
If you have 3 sub-agents, each gets ~20%. If 5+ sub-agents, consider whether fan-out
is appropriate — legibility degrades past ~3-4 panes in a tab.

---

## Part 3 — Deployment Scenarios (Built Into the Skill)

Every orchestration scenario is a recipe in this skill. The agent reads the relevant
section and executes it. No external config files needed.

### Scenario A: Single-Agent Task

When the task is small enough for one agent, you ARE the sub-agent.

```
TAB: "task-name"
┌────────────────────────────────────┐
│                                    │
│  ORCHESTRATOR + WORKER (merged)    │
│                                    │
│  • Plan the task                   │
│  • Execute it directly             │
│  • Report back                     │
│                                    │
└────────────────────────────────────┘
```

**When to use:** Single sub-task, no collision risk, output is self-contained.

**What you do:**

1. Plan the task in your pane
2. Execute it yourself (or run commands in your pane)
3. Report results

**Deployment:** No extra panes needed. Your pane does double duty.

### Scenario B: Parallel Fan-Out

When the task decomposes into independent sub-tasks touching disjoint areas:

```
TAB: "task-name"
┌────────┬────────┬────────┬────────┐
│        │        │        │        │
│ YOU    │ SUB-A  │ SUB-B  │ SUB-C  │
│        │        │        │        │
└────────┴────────┴────────┴────────┘
```

**When to use:**

- Sub-tasks are **independent** (no shared files)
- Each sub-task touches **disjoint directories or files**
- You want results faster by parallelizing

**What you do:**

1. Decompose the task into independent slices
2. Deploy a sub-agent per slice (see §2.2)
3. Brief each sub-agent with its specific scope
4. Wait for all to reach `done`
5. Integrate results in your pane
6. Report

**Critical rule:** If sub-tasks could collide (edit the same files), use **one agent**
or **one worktree per agent** instead of fan-out.

### Scenario C: Council

When the task involves a high-stakes decision or ambiguous problem:

```
TAB: "task-name"
┌────────┬────────┬────────┬────────┐
│        │        │        │        │
│ JUDGE  │ AGENT  │ AGENT  │ AGENT  │
│ (you)  │ A      │ B      │ C      │
│        │        │        │        │
└────────┴────────┴────────┴────────┘
```

**When to use:**

- High-stakes design decisions
- Multiple valid approaches, need diverse perspectives
- "Which approach is right?" type questions

**What you do:**

1. Brief each council member with the **same problem** but **different perspective angles**
   - Member A: "Analyze from architecture perspective"
   - Member B: "Analyze from security perspective"
   - Member C: "Analyze from performance perspective"
2. Wait for all to reach `done`
3. Read each member's output
4. Synthesize a recommendation in your pane (the judge)
5. Report to the human

**Cost:** N× tokens for one answer. Only use when the decision quality matters enough.

### Scenario D: Pipeline / Review Chain

When one agent's output feeds the next agent's input:

```
TAB: "task-name"
┌────────┬───────────┬──────────┬────────┐
│        │           │          │        │
│ YOU    │ IMPLEMENT │ REVIEW   │ FIX    │
│ (ctrl) │ (agent)   │ (agent)  │ (agent)│
│        │           │          │        │
└────────┴───────────┴──────────┴────────┘
```

**When to use:**

- Implement → review → fix cycle
- Any sequence where stage N+1 consumes stage N's output
- Quality assurance via multiple passes

**What you do:**

1. Brief the implementer with the task
2. Wait on implementer → `done`
3. Read implementer's output
4. Brief the reviewer: "Review the implementation by implementer. Focus on X."
5. Wait on reviewer → `done`
6. Read reviewer's output
7. If review found issues, brief the fixer with the review findings
8. Wait on fixer → `done`
9. Read fixer's output
10. Report results

**Gating:** Each stage gates on the prior agent reaching `done`. Use:

```bash
herdr agent wait <agent-name> --status done --timeout 120000
```

**Detection reliability:** Pipeline stages you gate on should use agents with reliable
state reporting (Authority A agents — lifecycle hooks). Screen-detection agents
(Authority B) may report `idle` when actually stuck, causing silent hangs.

### Scenario E: Manager / Workers

When one agent orchestrates many workers for similar sub-tasks:

```
TAB: "task-name"
┌────────┬────────┬────────┬────────┬────────┐
│        │        │        │        │        │
│ YOU    │ W1     │ W2     │ W3     │ W4     │
│ (mgr)  │        │        │        │        │
│        │        │        │        │        │
└────────┴────────┴────────┴────────┴────────┘
```

**When to use:**

- Many similar sub-tasks
- A coordinator can distribute and collect efficiently
- Workers are independent (disjoint slices)

**What you do:**

1. Brief workers with their disjoint slices: "Worker 1: process module A only."
2. Wait for workers to reach `done` one at a time or in batches
3. Integrate results as they come in
4. Report

**Tip:** You can have workers report directly to each other via `herdr agent send`,
reducing your coordination load.

---

## Part 4 — Real-Time Monitoring From Within Your Pane

### 4.1 The Triage Loop

Every few seconds (or on demand), check the state of all sub-agents:

```bash
# List all agents with their states
herdr agent list --json

# Or read recent state:
herdr status --json
```

**Sort by urgency:**

1. `blocked` — human input needed → route input to the agent
2. `done` — finished → read the output, decide next step
3. `unknown` — detection failed → investigate with `herdr agent explain <name>`
4. `working` — let it run
5. `idle` — not processing (but check Authority-B agents for false `idle`)

### 4.2 Reading Sub-Agent Output

```bash
# Read recent output from an agent
herdr agent read <agent-name> --lines 50

# Read unwrapped (for parsing)
herdr agent read <agent-name> --source recent-unwrapped --lines 50

# Read visible viewport
herdr agent read <agent-name> --source visible --lines 30
```

### 4.3 Routing Input to Sub-Agents

When a sub-agent is `blocked` or needs input:

```bash
# Send a message
herdr agent send <agent-name> "<message>"

# Send keystrokes (e.g., answer a y/n prompt)
herdr pane send-keys <pane-id> "<key-sequence>"

# Or read the pane, answer the question, then send
herdr agent read <agent-name> --lines 30
# ... read the prompt ...
herdr agent send <agent-name> "<answer>"
```

### 4.4 Waiting on Agents

```bash
# Wait for a specific agent to reach a state
herdr agent wait <agent-name> --status done --timeout 120000

# Wait for any text in a pane
herdr wait output <pane-id> --match "<pattern>" --timeout 30000
```

### 4.5 Notifying the Human

Alert the human at genuine milestones (not per-step chatter):

```bash
# Milestone: all agents done
herdr notification show "Fleet done" --body "All sub-agents completed" --sound done

# Milestone: first agent blocked
herdr notification show "Agent blocked" --body "<name> needs your input" --sound request
```

Notifications are suppressed for the active tab — use them for attention-worthy alerts.

---

## Part 5 — Integration and Reporting

### 5.1 Collecting Results

After all sub-agents reach `done`, read each one's output in your pane:

```
# In your pane (the orchestrator):
"Collecting results from all agents..."
"Agent A output: [paste/summarize]"
"Agent B output: [paste/summarize]"
"Agent C output: [paste/summarize]"
```

You can read them in any order. If you want the human to see them, paste summaries
directly in your pane output.

### 5.2 Synthesizing the Result

Your pane output IS the final report. Structure it:

```
## Orchestration Complete

### What I Did
1. Decomposed the task into X sub-tasks
2. Deployed Y sub-agents (A, B, C)
3. Monitored and coordinated handoffs

### Results
- Agent A: [summary]
- Agent B: [summary]
- Agent C: [summary]

### Integration
[Synthesize the results into a coherent answer]

### Next Steps
[What the human should do next, if anything]
```

### 5.3 Cleaning Up

If you created extra panes that are no longer needed:

```bash
herdr pane close <pane-id>
```

Or leave them — they're still visible in the tab, and the human can close them.

---

## Part 6 — Failure Handling

### 6.1 Agent Stuck at `idle` (Authority-B)

Screen-detection agents (Claude Code, Codex, etc.) may report `idle` when actually
waiting at an unrecognized prompt.

**What to do:**

```bash
# Check the pane's recent output
herdr agent read <agent-name> --lines 30
```

If it's waiting at a prompt, answer it:

```bash
herdr agent send <agent-name> "<answer>"
```

### 6.2 Agent State Wrong

```bash
# Diagnose why an agent's state looks wrong
herdr agent explain <agent-name> --json
```

Then:

1. Check the manifest source — is herdr matching the right agent?
2. Check if it's Authority A or B
3. If Authority B, check the live bottom buffer
4. If herdr sees `tmux` instead of the agent, the agent is invisible to detection

### 6.3 Agent Blocked on a Non-UI Question

If an agent is blocked on something that isn't a standard approval/question prompt,
screen detection won't trigger `blocked` automatically. You must:

```bash
herdr agent read <name> --lines 30
# Read the question
herdr agent send <name> "<answer>"
```

### 6.4 Collision Detection

If you detect that two agents are editing the same files:

```bash
# Stop the agent that shouldn't be there
herdr pane close <colliding-pane-id>
```

Then restructure your fan-out to have disjoint slices.

### 6.5 Cascading Failure in a Pipeline

If a pipeline agent reports `done` but the output is wrong:

```
Pipeline: implementer (done, wrong) → reviewer → fixer
```

**Option A:** Send the review findings back to the implementer:

```bash
herdr agent send implementer "The reviewer found issues: <findings>. Fix them."
```

**Option B:** Create a fixer agent instead:

```bash
# Split a new pane for the fixer
FIXER=$(herdr pane split <your-pane-id> --direction right --no-focus ...)
herdr pane run "$FIXER" "hermes --task '<review-findings>'"
```

---

## Part 7 — Quick Reference

### Agent States

| State | Meaning | Action |
|-------|---------|--------|
| `blocked` | Needs human input | Route input to it |
| `done` | Finished, not yet viewed | Read the output |
| `unknown` | Detection failed | Investigate with `explain` |
| `working` | Actively running | Let it run, check periodically |
| `idle` | Not processing | Check Authority-B for false idle |

### Pane ID Format

- Workspace: `1`, `2`, `3`...
- Tab: `1:1`, `1:2`, `2:1`...
- Pane: `1-1`, `1-2`, `2-1`...

### Common Commands (Confirm Live)

```bash
# Workspace
herdr workspace create --cwd <path> --label <name> --no-focus
herdr workspace focus <id>
herdr workspace rename <id> <name>

# Tab
herdr tab create --workspace <wid> --label <name> --no-focus
herdr tab focus <wid>:<tid>

# Pane
herdr pane split <pid> --direction right --no-focus
herdr pane run <pid> "<command>"
herdr pane read <pid> --lines 50
herdr pane send-keys <pid> "<keys>"
herdr pane close <pid>

# Agent
herdr agent list --json
herdr agent read <name> --lines 50
herdr agent send <name> "<message>"
herdr agent wait <name> --status done --timeout 120000
herdr agent explain <name> --json
herdr agent start <pid> --name <label> --session <id>

# Wait
herdr wait output <pid> --match "<text>" --timeout 30000
herdr wait agent-status <pid> --status done --timeout 120000

# Notification
herdr notification show "<title>" --body "<text>" --sound <done|request|none>
```

### When to Use Which Scenario

| Situation | Use |
|-----------|-----|
| One small task | Scenario A: Single-Agent (no extra panes) |
| Independent sub-tasks | Scenario B: Parallel Fan-Out |
| High-stakes decision | Scenario C: Council |
| Implement → review → fix | Scenario D: Pipeline |
| Many similar sub-tasks | Scenario E: Manager/Workers |
| Sub-tasks share files | Use ONE agent or worktrees — no fan-out |

---

## Part 8 — Design Principles

1. **Your pane is the command center.** Keep it wide. The human watches your reasoning.
2. **One sub-agent per pane.** Don't cram multiple agents into one pane.
3. **3-4 panes max per tab.** If you need more, split across tabs (only if the human
   wants to switch tabs, which defeats the purpose). Otherwise, break the task into
   multiple orchestration rounds.
4. **Name your agents.** Pane IDs are not durable. Agent names are.
5. **`done` ≠ correct.** Always read the pane output before feeding it downstream.
6. **`blocked` = urgent.** Something is waiting on input. Route it quickly.
7. **Use `--no-focus`.** Don't yank the user's terminal focus around when scripting.
8. **Disjoint slices or one agent.** If sub-tasks touch the same files, don't fan out.
9. **Prefer Authority-A agents for pipeline gates.** Screen-detection agents may report
   `idle` when stuck, causing silent hangs in your pipeline.
10. **Alert at milestones, not per-step.** One notification when the fleet is done or
    the first agent is blocked. Not after every sub-task completes.
