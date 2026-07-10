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

---

# THE GOLDEN RULE: IDENTIFY → VERIFY → ACT

**Before every single herdr command that modifies state, you MUST first identify
the current state, verify your target, then act.**

This is not optional. This is the difference between working orchestration and
destroying a live session.

```
IDENTIFY: Query the current state (workspace, tab, pane, agent)
VERIFY:   Confirm the result matches your target
ACT:      Only then perform the modification
```

**Never assume** a workspace, tab, or pane exists. **Never guess** an ID. **Never
create a new workspace when the current one is sufficient.**

Every operation follows this pattern. The snippets below are your complete playbook.

---

## Part 0 — Operational Discipline

### Rule 1: Always Query Before You Modify

| Operation | IDENTIFY Command |
|-----------|-----------------|
| Create a pane | `herdr pane list --workspace <wid>` (or `--current` if in herdr) |
| Create a tab | `herdr tab list --workspace <wid>` |
| Create a workspace | `herdr workspace list` |
| Start a sub-agent | `herdr agent list --json` (check if name is taken) |
| Resize a pane | `herdr pane layout --pane <pid>` (check current size) |
| Close a pane/tab/WS | **NEVER** close anything without first reading its contents |

### Rule 2: Use the Current Workspace/Tab by Default

When you are already inside herdr (`HERDR_ENV=1`), your current workspace and tab
are the correct target. **Do not create new ones unless explicitly needed.**

- `--workspace` + `--no-focus` → creates a **new** workspace (use sparingly)
- `--no-focus` on tabs/panes → creates in the **current** workspace/tab (default use case)
- `--current` → targets the pane/tab you are currently in

### Rule 3: Never Close a Workspace Mid-Orchestration

Closing a workspace destroys ALL panes, tabs, and running processes in it. This is
the single most destructive operation in herdr.

**Before closing any resource:**

1. Check if any agents are still working/blocked inside it
2. Confirm the human is ready for cleanup
3. Close individual panes first, then tabs, then workspace — in that order

### Rule 4: Always Use `--no-focus`

Stealing the user's terminal focus on every command is disruptive. Use `--no-focus`
on all create/split commands.

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
STEP 3: DEPLOY — Identify current state → create panes → spawn sub-agents
STEP 4: WAIT   — Monitor sub-agent states, route handoffs
STEP 5: INTEGRATE — Collect outputs, synthesize results
STEP 6: REPORT — Present results to the human
STEP 7: CLEAN  — Close sub-agent panes only, leave orchestrator pane
```

---

## Part 2 — Tab-Internal Pane Orchestration

### 2.1 Setting Up the Orchestrator Tab

**IDENTIFY first** — check the current workspace and tab situation:

```bash
# STEP 1: IDENTIFY — What workspaces and tabs already exist?
herdr workspace list --json
```

Parse the response:

- Find the workspace that matches your task context (or determine if you need a new one)
- Note the focused workspace and its active tab

**IF a workspace already exists for this task:**

```bash
# STEP 2: IDENTIFY — What tabs exist in this workspace?
herdr tab list --workspace <existing-workspace-id> --json

# STEP 3: VERIFY — Does an "orchestrator" tab already exist?
# If yes, reuse it. If no, create one in the existing workspace:
herdr tab create --workspace <existing-workspace-id> --label "orchestrator" --no-focus
```

**IF no workspace exists (first orchestration):**

```bash
# Only create a new workspace when there is truly no existing workspace
WORKSPACE_ID=$(herdr workspace create --cwd /path/to/project --label "<task-name>" --no-focus \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["workspace"]["workspace_id"])')

herdr tab create --workspace "$WORKSPACE_ID" --label "orchestrator" --no-focus
```

**CRITICAL DECISION POINT:**

```
IF workspace_count > 0 AND task_context_matches → USE EXISTING WORKSPACE
IF workspace_count == 0 OR no workspace matches → CREATE NEW WORKSPACE
```

**NEVER create a workspace if one already exists that can serve the purpose.**
This was the mistake that destroyed the live session. Creating a new workspace
abandons the current one and all its panes/agents.

**Focus the orchestration tab:**

```bash
herdr tab focus <workspace-id>:<orchestrator-tab-id>
```

At this point, you are the orchestrator — running in a pane in this tab.

### 2.2 Spawning Sub-Agent Panes (Right of You)

**IDENTIFY your pane and the workspace before splitting:**

```bash
# STEP 1: IDENTIFY — what pane am I in? what workspace?
herdr pane current --json
```

Parse the response to get:

- `current_pane_id` — your pane
- `workspace_id` — the workspace you're in
- `tab_id` — the tab you're in

**Deploy sub-agent panes within the SAME workspace and tab:**

For a single sub-agent:

```bash
# STEP 2: IDENTIFY — confirm your pane exists and is the right one
herdr pane list --workspace <workspace-id> --json

# STEP 3: VERIFY — is your pane_id the same as current_pane_id from IDENTIFY step?
# If yes, proceed. If no, re-identify (tab might have changed).

# STEP 4: ACT — split from YOUR pane, not from any other pane
SUB_PANE=$(herdr pane split <your-pane-id> --direction right --no-focus \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')

herdr pane run "$SUB_PANE" "<sub-agent-command>"
```

For multiple sub-agents (parallel fan-out):

```bash
# All panes split from YOUR pane (flat structure, all at same level)
PANE_A=$(herdr pane split <your-pane-id> --direction right --no-focus ...)
PANE_B=$(herdr pane split <your-pane-id> --direction right --no-focus ...)
PANE_C=$(herdr pane split <your-pane-id> --direction right --no-focus ...)

herdr pane run "$PANE_A" "<agent-a-command>"
herdr pane run "$PANE_B" "<agent-b-command>"
herdr pane run "$PANE_C" "<agent-c-command>"
```

**DO NOT chain splits** (`split A → split from A → split from that`) unless you need a
nested layout. Flat splits (all from your pane) keep all sub-agent panes at the same
level, all directly right of you.

**IDENTIFY after creating all panes — verify the layout:**

```bash
# STEP 5: VERIFY — did all panes land in the right workspace/tab?
herdr pane list --workspace <workspace-id> --json

# Check:
# - All new panes have the correct workspace_id
# - All new panes are in the orchestration tab
# - No panes ended up in a different workspace
```

### 2.3 Naming Sub-Agents

Always give each sub-agent a name. Pane IDs compact; agent names are durable.

```bash
# STEP 1: VERIFY — is the name available?
herdr agent list --json | grep -c "<agent-name>"

# STEP 2: ACT — start with the name
herdr agent start <pane-id> --name "<agent-label>" --session "<session-id>"
```

Named agents can be:

- Read by name: `herdr agent read <name> --lines 50`
- Sent input by name: `herdr agent send <name> "<message>"`
- Waited on by state: `herdr agent wait <name> --status done --timeout 120000`

### 2.4 Pane Sizing

Your orchestrator pane should be wide enough for the human to read your reasoning.

**IDENTIFY current layout before resizing:**

```bash
# STEP 1: IDENTIFY — current pane layout
herdr pane layout --pane <your-pane-id> --json
```

**VERIFY the current ratio is too narrow, then ACT:**

```bash
# STEP 2: ACT — give yourself more space (only if needed)
herdr pane resize <your-pane-id> --ratio 0.35
```

Rule of thumb: your pane gets ~35-40% of the tab width. Sub-agents share the rest.
If you have 3 sub-agents, each gets ~20%. If 5+ sub-agents, consider whether fan-out
is appropriate — legibility degrades past ~3-4 panes in a tab.

---

## Part 3 — Deployment Scenarios (Built Into the Skill)

Every orchestration scenario is a recipe in this skill. The agent reads the relevant
section and executes it using the IDENTIFY → VERIFY → ACT pattern.

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

**IDENTIFY first — confirm the workspace/tab state:**

```bash
herdr pane current --json
herdr pane list --workspace <wid> --json
# Verify: only your pane exists (no stray sub-agent panes from previous runs)
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

**IDENTIFY and VERIFY before deploying:**

```bash
# 1. IDENTIFY — current workspace, tab, pane
herdr pane current --json
herdr tab list --workspace <wid> --json

# 2. VERIFY — ensure we're in the right workspace
# If we created an orphan workspace in a previous run, close it first
herdr workspace list --json
# If workspace has stray panes from old runs:
#   herdr pane close <stray-pane>   (for each stray pane, one at a time)
#   THEN close the workspace only after all panes are gone

# 3. ACT — deploy panes using the flat-split pattern
#    (all panes split from YOUR pane, flat structure)
YOUR_PANE=$(herdr pane current --json | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')

PANE_A=$(herdr pane split "$YOUR_PANE" --direction right --no-focus \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')
PANE_B=$(herdr pane split "$YOUR_PANE" --direction right --no-focus \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')
PANE_C=$(herdr pane split "$YOUR_PANE" --direction right --no-focus \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')

# Brief each agent with its disjoint task
herdr agent start "$PANE_A" --name "agent-a" --session "fanout-a" \
  herdr agent send "agent-a" "<brief for agent A: disjoint task>"
herdr agent start "$PANE_B" --name "agent-b" --session "fanout-b" \
  herdr agent send "agent-b" "<brief for agent B: disjoint task>"
herdr agent start "$PANE_C" --name "agent-c" --session "fanout-c" \
  herdr agent send "agent-c" "<brief for agent C: disjoint task>"
```

**When to use:**

- Sub-tasks are **independent** (no shared files)
- Each sub-task touches **disjoint directories or files**
- You want results faster by parallelizing

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

**IDENTIFY — confirm no leftover council members from previous runs:**

```bash
herdr pane list --workspace <wid> --json
herdr agent list --json
# Clean up any stale agents/panes before starting
```

**ACT — deploy council members with disjoint perspective angles:**

```bash
YOUR_PANE=$(herdr pane current --json   | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')

PANE_A=$(herdr pane split "$YOUR_PANE" --direction right --no-focus   | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')
PANE_B=$(herdr pane split "$YOUR_PANE" --direction right --no-focus   | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')
PANE_C=$(herdr pane split "$YOUR_PANE" --direction right --no-focus   | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')

# Brief each council member with a unique angle — same problem, different lens
herdr agent start "$PANE_A" --name "architect" --session "council-arch"
herdr agent send "architect" "Analyze this problem from an architecture perspective: <problem>"

herdr agent start "$PANE_B" --name "security" --session "council-sec"
herdr agent send "security" "Analyze this problem from a security perspective: <problem>"

herdr agent start "$PANE_C" --name "performance" --session "council-perf"
herdr agent send "performance" "Analyze this problem from a performance perspective: <problem>"
```

**WAIT for all council members to reach `done`:**

```bash
herdr agent wait "architect" --status done --timeout 120000
herdr agent wait "security" --status done --timeout 120000
herdr agent wait "performance" --status done --timeout 120000
```

**VERIFY — read each output before synthesizing:**

```bash
herdr agent read "architect" --lines 50
herdr agent read "security" --lines 50
herdr agent read "performance" --lines 50
```

**Then** synthesize a recommendation in your pane (the judge) and report to the human.

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

**IDENTIFY — each stage must wait for the prior:**

```bash
# Pipeline stage: implementer → reviewer → fixer

# Stage 1: Deploy implementer
IMPL_PANE=$(herdr pane split <your-pane-id> --direction right --no-focus ...)
herdr agent start "$IMPL_PANE" --name "implementer" --session "impl-sess"

# Stage 2: WAIT for implementer before deploying reviewer
herdr agent wait "implementer" --status done --timeout 120000

# Stage 3: VERIFY implementer output before proceeding
IMPL_OUTPUT=$(herdr agent read "implementer" --lines 100)
# Check: does output look valid? Does it match the brief?
# If no → fix or retry implementer before moving on
# If yes → deploy reviewer

# Stage 4: Deploy reviewer
REV_PANE=$(herdr pane split <your-pane-id> --direction right --no-focus ...)
herdr agent start "$REV_PANE" --name "reviewer" --session "rev-sess"
herdr agent send "reviewer" "Review this output: $IMPL_OUTPUT"
```

**Gating:** Each stage gates on the prior agent reaching `done`.

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

**IDENTIFY — ensure you have room for workers in the current tab:**

```bash
herdr pane list --workspace <wid> --json
pane_count=$(...)
# If pane_count + worker_count > 5, consider batching workers in rounds
```

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
# IDENTIFY — list all agents with their states
herdr agent list --json
```

**Sort by urgency:**

1. `blocked` — human input needed → route input to the agent
2. `done` — finished → read the output, decide next step
3. `unknown` — detection failed → investigate with `herdr agent explain <name>`
4. `working` — let it run
5. `idle` — not processing (but check Authority-B agents for false `idle`)

### 4.2 Reading Sub-Agent Output

```bash
# Verify agent exists, then read
herdr agent read <agent-name> --lines 50

# Unwrapped (for parsing)
herdr agent read <agent-name> --source recent-unwrapped --lines 50

# Visible viewport
herdr agent read <agent-name> --source visible --lines 30
```

### 4.3 Routing Input to Sub-Agents

When a sub-agent is `blocked` or needs input:

```bash
# Read the prompt first (identify what's needed)
herdr agent read <agent-name> --lines 30

# Then act — send the answer
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
herdr agent read <name> --lines 100
# ... repeat for each agent ...
```

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

**IDENTIFY before closing anything:**

```bash
# 1. Check which panes are yours (orchestrator) vs sub-agent panes
herdr pane list --workspace <wid> --json

# 2. Close sub-agent panes only (NOT your orchestrator pane)
herdr pane close <sub-agent-pane-id>   # one at a time
```

**NEVER close the workspace** while the orchestrator pane is still in it.
**NEVER close a workspace with working agents inside it.**

Leave your orchestrator pane — it's the only one the human needs to see.

---

## Part 6 — Failure Handling

### 6.1 Agent Stuck at `idle` (Authority-B)

Screen-detection agents (Claude Code, Codex, etc.) may report `idle` when actually
waiting at an unrecognized prompt.

**IDENTIFY the truth:**

```bash
herdr agent read <agent-name> --lines 30
# If it's waiting at a prompt → ACT: answer it
# If it's truly idle → let it sit or send a ping
```

### 6.2 Agent State Wrong

**IDENTIFY why:**

```bash
herdr agent explain <name> --json
# Check manifest source, authority level, bottom buffer
```

### 6.3 Agent Blocked on a Non-UI Question

```bash
herdr agent read <name> --lines 30
# Read the question, then answer
herdr agent send <name> "<answer>"
```

### 6.4 Collision Detection

**IDENTIFY collision risk before deploying:**

```bash
# Before fan-out, confirm disjoint scopes
Sub-agent A owns: src/auth/login.ts, src/auth/logout.ts
Sub-agent B owns: src/auth/profile.ts, src/auth/settings.ts
→ No overlap ✓

Sub-agent A owns: src/api/
Sub-agent B owns: src/api/
→ Collision! ❌ — don't fan-out
```

If collision is detected:

```bash
# Act: stop the colliding agent and re-scope
herdr agent send <later-agent> "Hold — you may collide with <other-agent>. Awaiting re-scope."
```

### 6.5 Cascading Failure in a Pipeline

If a pipeline agent reports `done` but the output is wrong:

```bash
# IDENTIFY: read the output
IMPL=$(herdr agent read implementer --lines 100)

# ACT: Option A — re-send to implementer
herdr agent send implementer "The review found issues: <findings>. Fix them."

# ACT: Option B — create a fixer instead
FIXER=$(herdr pane split <your-pane-id> --direction right --no-focus ...)
herdr agent start "$FIXER" --name "fixer" --session "fix-sess"
herdr agent send "fixer" "<review-findings>"
```

---

## Part 7 — Quick Reference

### IDENTIFY Commands (Query Before Modify)

```bash
# Workspace
herdr workspace list --json                    # All workspaces
herdr workspace get <wid> --json               # Specific workspace

# Tab
herdr tab list --workspace <wid> --json         # Tabs in workspace
herdr tab get <wid>:<tid> --json               # Specific tab

# Pane
herdr pane current --json                      # My current pane
herdr pane list --workspace <wid> --json       # All panes in workspace
herdr pane list --workspace <wid> --tab <tid> --json  # All panes in tab
herdr pane get <pid> --json                    # Specific pane
herdr pane layout --pane <pid> --json          # Layout of specific pane

# Agent
herdr agent list --json                        # All agents with states
herdr agent get <name> --json                  # Specific agent
herdr agent explain <name> --json              # Why state is X
```

### Agent States

| State | Meaning | Action |
|-------|---------|--------|
| `blocked` | Needs human input | Route input to it |
| `done` | Finished, not yet viewed | Read the output |
| `unknown` | Detection failed | Investigate with `explain` |
| `working` | Actively running | Let it run, check periodically |
| `idle` | Not processing | Check Authority-B for false idle |

### Pane ID Format

- Workspace: `w1`, `wX`, `w14`... (randomized hex-like)
- Tab: `w1:t1`, `w1:t2`...
- Pane: `w1:p1`, `w1:p2`...

### Modify Commands (After IDENTIFY + VERIFY)

```bash
# Workspace
herdr workspace create --cwd <path> --label <name> --no-focus     # Only if no existing WS works
herdr workspace rename <id> <name>
herdr workspace close <id>                                          # DANGEROUS — only when human confirms

# Tab
herdr tab create --workspace <wid> --label <name> --no-focus
herdr tab rename <wid>:<tid> <name>
herdr tab close <wid>:<tid>

# Pane
herdr pane split <pid> --direction right --no-focus               # Always from YOUR pane
herdr pane run <pid> "<command>"
herdr pane send-keys <pid> "<keys>"
herdr pane resize <pid> --ratio 0.35
herdr pane close <pid>

# Agent
herdr agent start <pid> --name <label> --session <id>
herdr agent send <name> "<message>"
herdr agent wait <name> --status done --timeout 120000
herdr agent explain <name> --json

# Wait
herdr wait output <pid> --match "<text>" --timeout 30000

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

1. **IDENTIFY before you act.** Every single operation starts with a query.
2. **Use the current workspace/tab by default.** Only create new ones when needed.
3. **NEVER close a workspace mid-orchestration** without human confirmation.
4. **Your pane is the command center.** Keep it wide. The human watches your reasoning.
5. **One sub-agent per pane.** Don't cram multiple agents into one pane.
6. **3-4 panes max per tab.** If you need more, split across tabs.
7. **Name your agents.** Pane IDs are not durable. Agent names are.
8. **`done` ≠ correct.** Always read the pane output before feeding it downstream.
9. **`blocked` = urgent.** Something is waiting on input. Route it quickly.
10. **Use `--no-focus`.** Don't yank the user's terminal focus around when scripting.
11. **Disjoint slices or one agent.** If sub-tasks touch the same files, don't fan out.
12. **Prefer Authority-A agents for pipeline gates.** Screen-detection agents may report
    `idle` when stuck, causing silent hangs in your pipeline.
13. **Alert at milestones, not per-step.** One notification when the fleet is done or
    the first agent is blocked.
14. **Close only sub-agent panes during cleanup.** Never close your orchestrator pane or the workspace.

---

## Reference Files

For deep dives, see the reference files in this skill's `references/` directory:

- **`references/pane-orchestration.md`** — Tab-internal pane layout design, sizing, and
  arrangement patterns.
- **`references/sub-agent-design.md`** — How to design sub-tasks, brief sub-agents,
  manage them during execution, and handle handoffs.
- **`references/tab-management.md`** — Single-tab vs multi-tab orchestration.
- **`references/monitoring.md`** — Real-time monitoring, the triage loop, state-based
  alerting, and stalled detection.
- **`references/failure-handling.md`** — 8 failure modes, recovery strategies, and
  escalation framework.

**When you need more detail than this master skill provides, read the appropriate
reference file. This skill is your quick-reference; the references are your deep-dive.**
